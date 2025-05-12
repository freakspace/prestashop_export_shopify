import os
import json
import requests
from bs4 import BeautifulSoup
from ps_services import (
    get_products,
    get_product_option,
    get_product_image,
    get_product_option_values,
    get_combination,
    get_feature,
    get_feature_value,
    get_manufacturer,
    get_supplier_name,
    get_category,
)

from shopify_types import (
    CreateShopifyProductInput,
    Product,
    SEO,
    Image,
    File,
    ShopifyMetaField,
    InventoryItem,
    CreateShopifyProductVariantInput,
    VariantOptionValue,
    ProductOptionValue,
    OptionValue,
    ProductSet,
    CreateCollectionInput,
    CreateBrandInput,
    MetaobjectHandle
)

DEFAULT_OPTION_NAME = "Title"
DEFAULT_OPTION_VALUE_NAME = "Default Title"
CATEGORIES_TO_SKIP = ["1", "2", "24", "591", "584", "604", "609", "597"]
PRODUCTS_TO_SKIP = ["738"]


# TODO Default title - maybe use product name?
# TODO nogen billeder fra karcher komemr med selvom de ikke er synlige i PS (måske bare fiks det manuelt)
# TODO For the ongoing sync i need to handle cases where they send new product features to prevent dublicates
# TODO Naming convention can be imroved
# TODO If metafield value is a list, all of the values has to be a list
# TODO Brands is not getting created properly - missing data in shopify
# TODO There might be an issue where categories share same names, its not set correct -  see product 762
def clean_html(html_content):
    if not html_content:
        return ""

    soup = BeautifulSoup(html_content, "html.parser")

    # Remove all class attributes from p, span, and div tags
    for tag in soup.find_all(["p", "span", "div"]):
        del tag["class"]

    # Remove all style attributes from p, span, and div tags
    for tag in soup.find_all(["p", "span", "div"]):
        del tag["style"]

    # Remove all inline CSS
    for style in soup.find_all("style"):
        style.decompose()

    return str(soup)

used_handles = set()

def ensure_unique_handle(handle):
    """
    Ensure the handle is unique by appending a small suffix if necessary.
    """
    original_handle = handle
    counter = 1
    while handle in used_handles:
        handle = f"{original_handle}-{counter}"
        counter += 1
    used_handles.add(handle)
    return handle

def create_shopify_collection_input(category):
    metafields = [
        ShopifyMetaField(
            namespace="prestashop_category_id",
            key="id",
            value=str(category["id"]),
            type="single_line_text_field",
        ),
        ShopifyMetaField(
            namespace="prestashop_posittion",
            key="position",
            value=str(category["position"]),
            type="single_line_text_field",
        ),
        # TODO Need the old URL
    ]

    if category["id_parent"] not in CATEGORIES_TO_SKIP:
        metafields.append(
            ShopifyMetaField(
                namespace="parent_category_id",
                key="id",
                value=str(category["id_parent"]),
                type="single_line_text_field",
            )
        )

    # Filter out metafields with None values
    metafields = [
        metafield for metafield in metafields if metafield.value not in [None, ""]
    ]

    return CreateCollectionInput(
        title=category["name"]["language"]["value"],
        descriptionHtml=clean_html(category["description"]["language"]["value"]),
        handle=category["link_rewrite"]["language"]["value"],
        seo=SEO(
            description=category["meta_description"]["language"]["value"],
            title=category["meta_title"]["language"]["value"],
        ),
        metafields=metafields,
        image=(
            Image(
                alt=category["name"]["language"]["value"], src=category["image"]["url"]
            )
            if "image" in category
            else None
        ),
    )


def create_shopify_brand_input(manufacturer):
    return CreateBrandInput(
        name=manufacturer["manufacturer"]["name"],
        description=manufacturer["manufacturer"]["description"]["language"]["value"],
        short_description=manufacturer["manufacturer"]["short_description"]["language"][
            "value"
        ],
        meta_title=manufacturer["manufacturer"]["meta_title"]["language"]["value"],
        meta_description=manufacturer["manufacturer"]["meta_description"]["language"][
            "value"
        ],
        handle=MetaobjectHandle(handle=manufacturer["manufacturer"]["link_rewrite"]["value"], type="brand"),
    )


def get_option_value(product_option_values_id: int):
    option_value = get_product_option_values(product_option_values_id)
    option_value_name = option_value["product_option_value"]["name"]["language"][
        "value"
    ]
    option = get_product_option(
        option_value["product_option_value"]["id_attribute_group"]
    )
    if option is None:
        return None, None
    option_name = option["product_option"]["name"]["language"]["value"]
    return option_value_name, option_name


def create_shopify_product_variant_input(
    base_price, base_cost_price, combination_id, option_values
):
    variant = get_combination(combination_id)
    cost_price = float(variant["combination"]["wholesale_price"])

    # Defaults to base cost price if cost price is not set
    if cost_price == 0.0:
        cost_price = base_cost_price
    variant_option_values = []
    if (
        "associations" in variant["combination"]
        and "product_option_values" in variant["combination"]["associations"]
    ):

        variants_payload = variant["combination"]["associations"][
            "product_option_values"
        ]["product_option_value"]
        # Single option
        if isinstance(variants_payload, dict):
            option_value_id = variants_payload["id"]
            option_value_name, option_name = get_option_value(option_value_id)
            if not all([option_value_name, option_name]):
                return None, option_values
            variant_option_values.append(
                VariantOptionValue(name=option_value_name, optionName=option_name)
            )
            if option_name not in option_values:
                option_values[option_name] = set()
            option_values[option_name].add(option_value_name)

        # Multiple options
        else:
            for option_value in variants_payload:
                option_value_name, option_name = get_option_value(option_value["id"])
                variant_option_values.append(
                    VariantOptionValue(name=option_value_name, optionName=option_name)
                )
                if option_name not in option_values:
                    option_values[option_name] = set()
                option_values[option_name].add(option_value_name)

        variant_input = CreateShopifyProductVariantInput(
            barcode=variant["combination"]["ean13"],
            inventoryItem=InventoryItem(
                cost=str(cost_price),  # Using wholesale price as cost price
                sku=variant["combination"]["reference"],
                tracked=True,
            ),
            inventoryPolicy="CONTINUE",  # CONTINUE = Customers can buy this product variant after it's out of stock.
            optionValues=variant_option_values,
            price=str(base_price + float(variant["combination"]["price"])),
        )

        return variant_input, option_values
    return None, option_values


def create_shopify_product_input(product, as_set=False):
    if product["id"] in PRODUCTS_TO_SKIP:
        print(f"Skipping product: {product['name']['language']['value']}")
        return None
    print(
        f"Processing product: {product['name']['language']['value']}, ID: {product['id']}"
    )
    base_price = float(product["price"])
    wholesale_price = float(product["wholesale_price"])
    seo = SEO(
        description=product["meta_description"]["language"]["value"],
        title=product["meta_title"]["language"]["value"],
    )
    shopify_product = Product(
        title=product["name"]["language"]["value"],
        descriptionHtml=clean_html(product["description"]["language"]["value"]),
        handle=ensure_unique_handle(product["link_rewrite"]["language"]["value"]),
        seo=seo,
        status="ACTIVE",
        # vendor=get_manufacturer_name(product["id_manufacturer"]),
        productOptions=[],
    )
    # Image URLs
    images = get_product_image(product["id"])

    # Extract media payloads
    media = (
        [
            File(alt=image["alt"], contentType="IMAGE", originalSource=image["url"])
            for image in images
        ]
        if images
        else []
    )

    metafields = []

    # Handle product features as metafields in Shopify
    if "product_feature" in product["associations"]["product_features"]:
        features_payload = product["associations"]["product_features"][
            "product_feature"
        ]
        # Multiple features
        if isinstance(features_payload, list):
            # Extract metafields
            metafields = [
                ShopifyMetaField(
                    namespace="product_feature",
                    key=get_feature(feature["id"])["product_feature"]["name"][
                        "language"
                    ]["value"],
                    value=get_feature_value(feature["id_feature_value"])[
                        "product_feature_value"
                    ]["value"]["language"]["value"],
                    type="single_line_text_field",
                )
                for feature in features_payload
            ]
        # Single feature
        else:
            # Extract metafields
            metafields = [
                ShopifyMetaField(
                    namespace="product_feature",
                    key=get_feature(features_payload["id"])["product_feature"]["name"][
                        "language"
                    ]["value"],
                    value=get_feature_value(features_payload["id_feature_value"])[
                        "product_feature_value"
                    ]["value"]["language"]["value"],
                    type="single_line_text_field",
                )
            ]

    # Add prestashop product to metadata
    prestashop_product_id = ShopifyMetaField(
        namespace="prestashop_product_id",
        key="id",
        value=product["id"],
        type="single_line_text_field",
    )
    metafields.append(prestashop_product_id)

    # Add product reference to metadata
    product_reference = product["reference"]
    if product_reference:
        # Add prestashop reference to metadata
        prestashop_reference = ShopifyMetaField(
            namespace="prestashop_reference",
            key="reference",
            value=product["reference"],
            type="single_line_text_field",
        )
        metafields.append(prestashop_reference)

    # Add prestashop url to metadata
    product_id = product["id"]
    prestashop_url = ShopifyMetaField(
        namespace="prestashop_url",
        key="url",
        value=requests.get(
            f"https://induclean.dk/random/{product_id}-random.html"
        ).url,  # Ps will automatically redirect
        type="single_line_text_field",
    )
    metafields.append(prestashop_url)

    # Add supplier to metadata
    supplier_name = get_supplier_name(product["id_supplier"])
    if supplier_name:
        supplier = ShopifyMetaField(
            namespace="supplier",
            key="supplier",
            value=supplier_name,
            type="single_line_text_field",
        )
        metafields.append(supplier)

    # Add short_description to metadata
    product_short_description = product["description_short"]["language"]["value"]
    if product_short_description:
        short_description = ShopifyMetaField(
            namespace="short_description",
            key="description",
            value=product["description_short"]["language"]["value"],
            type="multi_line_text_field",
        )
        metafields.append(short_description)

    # Add name_extra to metadata
    product_name_extra = product["name_extra"]["language"]["value"]
    if product_name_extra:
        name_extra = ShopifyMetaField(
            namespace="name_extra",
            key="name_extra",
            value=product["name_extra"]["language"]["value"],
            type="single_line_text_field",
        )
        metafields.append(name_extra)

    # TODO Make this as a separate function
    # Extract variants
    variants = []
    option_values = {}
    if (
        "combinations" in product["associations"]
        and "combination" in product["associations"]["combinations"]
    ):
        combination_payload = product["associations"]["combinations"]["combination"]
        if isinstance(combination_payload, dict):
            combination_id = combination_payload["id"]
            # TODO Maybe construct a default variant instead, if there is only 1 option
            variant_input, _ = create_shopify_product_variant_input(
                base_price, wholesale_price, combination_id, option_values
            )
            if variant_input:
                variants.append(variant_input)
        else:
            for combination in product["associations"]["combinations"]["combination"]:
                variant_input, option_values = create_shopify_product_variant_input(
                    base_price, wholesale_price, combination["id"], option_values
                )
                if variant_input:
                    variants.append(variant_input)
    else:
        # Construct a single Variant since Shopify requires at least 1 variant
        new_variant = CreateShopifyProductVariantInput(
            barcode=product["ean13"],
            inventoryItem=InventoryItem(
                cost=str(wholesale_price),
                sku=product["reference"],
                tracked=True,
            ),
            inventoryPolicy="CONTINUE",
            price=str(base_price),
            optionValues=[
                VariantOptionValue(
                    name=product["name"]["language"]["value"], optionName=DEFAULT_OPTION_NAME
                )
            ],
        )
        variants.append(new_variant)

    # Handle collections
    collections = []
    category_payload = product["associations"]["categories"]["category"]
    if isinstance(category_payload, list):
        for category in category_payload:
            try:
                category_id = category["id"]
            except TypeError:
                raise Exception("Failed to get category ID")

            if category_id not in CATEGORIES_TO_SKIP:
                category_instance = get_category(category_id)
                collection = create_shopify_collection_input(
                    category_instance["category"]
                )
                collections.append(collection)
    else:
        category_id = category_payload["id"]
        if category_id not in CATEGORIES_TO_SKIP:
            category_instance = get_category(category_id)
            collection = create_shopify_collection_input(category_instance["category"])
            collections.append(collection)

    # Handle brands
    shopify_brand_input = None
    manufacturer_id = product["id_manufacturer"]
    if manufacturer_id != "0":
        manufacturer_instance = get_manufacturer(manufacturer_id)
        if manufacturer_instance:
            shopify_brand_input = create_shopify_brand_input(manufacturer_instance)

    # Create product options
    product_options = [
        ProductOptionValue(
            name=option_name,
            values=[OptionValue(name=value) for value in option_values[option_name]],
        )
        for option_name in option_values
    ]

    if len(product_options) > 0:
        shopify_product.productOptions = product_options
    else:
        shopify_product.productOptions = [
            ProductOptionValue(
                name=DEFAULT_OPTION_NAME,
                values=[OptionValue(name=product["name"]["language"]["value"])],
            )
        ]

    # Filter out metafields with None values
    metafields = [
        metafield for metafield in metafields if metafield.value not in [None, ""]
    ]

    if as_set:

        return ProductSet(
            # id="gid://shopify/Product/10079785100", pass id to update
            title=shopify_product.title,
            descriptionHtml=shopify_product.descriptionHtml,
            handle=shopify_product.handle,
            seo=shopify_product.seo,
            status=shopify_product.status,
            # vendor=shopify_product.vendor,
            files=media,
            productOptions=(
                shopify_product.productOptions
                if shopify_product.productOptions
                else None
            ),
            metafields=metafields,
            variants=variants,
            collections=collections,
            brand=shopify_brand_input,
        )

    return CreateShopifyProductInput(
        product=shopify_product, media=media, metafields=metafields, variants=variants
    )

def dump_products():
    products = get_products(id=None, limit=50, random_sample=True)
    CREATE_AS_SET = True
    if "products" in products:
        if isinstance(products["products"]["product"], list):
            shopify_products = [
                create_shopify_product_input(product, CREATE_AS_SET)
                for product in products["products"]["product"]
            ]
        else:
            shopify_products = [
                create_shopify_product_input(
                    products["products"]["product"], CREATE_AS_SET
                )
            ]
    else:
        shopify_products = [
            create_shopify_product_input(products["product"], CREATE_AS_SET)
        ]

    if not os.path.exists("dump"):
        os.makedirs("dump")

    else:
        # Save the Shopify product inputs as JSON
        with open(os.path.join("dump", "shopify_products.json"), "w") as f:
            json.dump([product.to_dict() for product in shopify_products if product is not None], f, indent=2)

    return "dump/shopify_products.json"