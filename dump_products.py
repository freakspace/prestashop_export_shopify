import os
import json
import requests
from slugify import slugify
from bs4 import BeautifulSoup
from ps_services import (
    get_products,
    get_product_option,
    get_product_image,
    get_product_option_values,
    get_combination,
    get_feature,
    get_feature_value,
    get_manufacturer_name,
    get_supplier_name,
    get_category,
)
from shopify_types import (
    CreateShopifyProductInput,
    Product,
    SEO,
    Image,
    CreateShopifyMediaPayload,
    ShopifyMetaField,
    InventoryItem,
    CreateShopifyProductVariantInput,
    VariantOptionValue,
    ProductOptionValue,
    OptionValue,
    ProductSet,
    CreateCollectionInput,
)

DEFAULT_OPTION_NAME = "Title"
DEFAULT_OPTION_VALUE_NAME = "Default Title"
CATEGORIES_TO_SKIP=["1","2","24","591","584","604","609","597"]

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


def create_shopify_collection_input(category):
    metafields = [
        ShopifyMetaField(
            namespace="prestashop_category_id",
            key="id",
            value=str(category["id"]),
            type="single_line_text_field",
        )
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


def create_shopify_product_input(product, as_set=False):
    print(f"Processing product: {product['name']['language']['value']}")
    seo = SEO(
        description=product["meta_description"]["language"]["value"],
        title=product["meta_title"]["language"]["value"],
    )
    shopify_product = Product(
        title=product["name"]["language"]["value"],
        descriptionHtml=clean_html(product["description"]["language"]["value"]),
        handle=product["link_rewrite"]["language"]["value"],
        seo=seo,
        status="ACTIVE",
        vendor=get_manufacturer_name(product["id_manufacturer"]),
        productOptions=[],
    )
    # Image URLs
    images = get_product_image(product["id"])

    # Extract media payloads
    media = [
        CreateShopifyMediaPayload(
            alt=image["alt"], mediaContentType="IMAGE", originalSource=image["url"]
        )
        for image in images
    ]

    metafields = []

    # Handle product features as metafields in Shopify
    if "product_feature" in product["associations"]["product_features"]:
        # Extract metafields
        metafields = [
            ShopifyMetaField(
                namespace="product_feature",
                key=slugify(
                    get_feature(feature["id"])["product_feature"]["name"]["language"][
                        "value"
                    ]
                ),
                value=get_feature_value(feature["id_feature_value"])[
                    "product_feature_value"
                ]["value"]["language"]["value"],
                type="single_line_text_field",
            )
            for feature in product["associations"]["product_features"][
                "product_feature"
            ]
        ]

    # Add prestashop product to metadata
    prestashop_product_id = ShopifyMetaField(
        namespace="prestashop_product_id",
        key="id",
        value=product["id"],
        type="single_line_text_field",
    )
    metafields.append(prestashop_product_id)

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
    short_description = ShopifyMetaField(
        namespace="short_description",
        key="description",
        value=product["description_short"]["language"]["value"],
        type="multi_line_text_field",
    )
    metafields.append(short_description)

    # Add name_extra to metadata
    name_extra = ShopifyMetaField(
        namespace="name_extra",
        key="name_extra",
        value=product["name_extra"]["language"]["value"],
        type="single_line_text_field",
    )
    metafields.append(name_extra)

    def get_option_value(product_option_values_id: int):
        option_value = get_product_option_values(product_option_values_id)
        option_value_name = option_value["product_option_value"]["name"]["language"][
            "value"
        ]
        option = get_product_option(
            option_value["product_option_value"]["id_attribute_group"]
        )
        option_name = option["product_option"]["name"]["language"]["value"]
        return option_value_name, option_name

    # TODO Make this as a separate function
    # Extract variants
    variants = []
    option_values = {}
    if (
        "combinations" in product["associations"]
        and "combination" in product["associations"]["combinations"]
    ):
        for combination in product["associations"]["combinations"]["combination"]:
            variant = get_combination(combination["id"])
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
                    variant_option_values.append(
                        VariantOptionValue(
                            name=option_value_name, optionName=option_name
                        )
                    )
                    if option_name not in option_values:
                        option_values[option_name] = set()
                    option_values[option_name].add(option_value_name)

                # Multiple options
                else:
                    for option_value in variants_payload:
                        option_value_name, option_name = get_option_value(
                            option_value["id"]
                        )
                        variant_option_values.append(
                            VariantOptionValue(
                                name=option_value_name, optionName=option_name
                            )
                        )
                        if option_name not in option_values:
                            option_values[option_name] = set()
                        option_values[option_name].add(option_value_name)
            variants.append(
                CreateShopifyProductVariantInput(
                    barcode=variant["combination"]["ean13"],
                    inventoryItem=InventoryItem(
                        cost=str(
                            float(variant["combination"]["wholesale_price"])
                        ),  # Using wholesale price as cost price
                        sku=variant["combination"]["reference"],
                        tracked=True,
                    ),
                    inventoryPolicy="CONTINUE",  # CONTINUE = Customers can buy this product variant after it's out of stock.
                    optionValues=variant_option_values,
                    price=str(float(variant["combination"]["price"])),
                )
            )
    else:
        # Construct a single Variant since Shopify requires at least 1 variant
        new_variant = CreateShopifyProductVariantInput(
            barcode=product["ean13"],
            inventoryItem=InventoryItem(
                cost=str(float(product["wholesale_price"])),
                sku=product["reference"],
                tracked=True,
            ),
            inventoryPolicy="CONTINUE",
            price=str(float(product["price"])),
            optionValues=[
                VariantOptionValue(
                    name=DEFAULT_OPTION_VALUE_NAME, optionName=DEFAULT_OPTION_NAME
                )
            ],
        )
        variants.append(new_variant)

    # Handle collections
    collections = []
    for category in product["associations"]["categories"]["category"]:
        category_id = category["id"]
        if category_id not in CATEGORIES_TO_SKIP:
            category_instance = get_category(category_id)
            collection = create_shopify_collection_input(category_instance["category"])
            collections.append(collection)

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
                values=[OptionValue(name=DEFAULT_OPTION_VALUE_NAME)],
            )
        ]
    if as_set:

        return ProductSet(
            title=shopify_product.title,
            descriptionHtml=shopify_product.descriptionHtml,
            handle=shopify_product.handle,
            seo=shopify_product.seo,
            status=shopify_product.status,
            vendor=shopify_product.vendor,
            productOptions=(
                shopify_product.productOptions
                if shopify_product.productOptions
                else None
            ),
            metafields=metafields,
            variants=variants,
            collections=collections,
        )

    return CreateShopifyProductInput(
        product=shopify_product, media=media, metafields=metafields, variants=variants
    )


def dump_products():
    products = get_products(id=73, limit=10)
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

    # Save the Shopify product inputs as JSON
    with open(os.path.join("dump", "shopify_products.json"), "w") as f:
        json.dump([product.to_dict() for product in shopify_products], f, indent=2)
