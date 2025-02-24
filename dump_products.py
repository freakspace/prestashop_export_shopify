import os
import json
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
)
from shopify_types import (
    CreateShopifyProductInput,
    Product,
    SEO,
    CreateShopifyMediaPayload,
    ShopifyMetaField,
    MoneyV2,
    InventoryItem,
    CreateShopifyProductVariantInput,
    OptionValue,
)


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


def create_shopify_product_input(product):
    print(f"Processing product: ID {product['id']}")
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

    if "product_feature" in product["associations"]["product_features"]:
        # Extract metafields
        metafields = [
            ShopifyMetaField(
                namespace="product_feature",
                key=get_feature(feature["id"])["product_feature"]["name"]["language"][
                    "value"
                ],
                value=get_feature_value(feature["id_feature_value"])[
                    "product_feature_value"
                ]["value"]["language"]["value"],
                type="single_line_text_field",
            )
            for feature in product["associations"]["product_features"][
                "product_feature"
            ]
        ]

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

    # Extract variants
    variants = []
    if (
        "combinations" in product["associations"]
        and "combination" in product["associations"]["combinations"]
    ):
        for combination in product["associations"]["combinations"]["combination"]:
            variant = get_combination(combination["id"])
            option_values = []
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
                    option_values.append(
                        OptionValue(name=option_value_name, optionName=option_name)
                    )

                # Multiple options
                else:
                    for option_value in variants_payload:
                        option_value_name, option_name = get_option_value(
                            option_value["id"]
                        )
                        option_values.append(
                            OptionValue(name=option_value_name, optionName=option_name)
                        )
            variants.append(
                CreateShopifyProductVariantInput(
                    inventoryItem=InventoryItem(
                        cost=MoneyV2(
                            amount=float(variant["combination"]["wholesale_price"]),
                            currencyCode="DKK",
                        ),  # Using wholesale price as cost price
                        sku=variant["combination"]["reference"],
                        tracked=True,
                    ),
                    inventoryPolicy="CONTINUE",  # CONTINUE = Customers can buy this product variant after it's out of stock.
                    optionValues=option_values,
                    price=MoneyV2(
                        amount=float(variant["combination"]["price"]),
                        currencyCode="DKK",
                    ),
                )
            )

    return CreateShopifyProductInput(
        product=shopify_product, media=media, metafields=metafields, variants=variants
    )


def process_product(product):
    return create_shopify_product_input(product)


def dump_products():
    products = get_products(id=None, limit=3)

    if "products" in products:
        if isinstance(products["products"]["product"], list):
            shopify_products = [
                create_shopify_product_input(product)
                for product in products["products"]["product"]
            ]
        else:
            shopify_products = [
                create_shopify_product_input(products["products"]["product"])
            ]
    else:
        shopify_products = [create_shopify_product_input(products["product"])]

    if not os.path.exists("dump"):
        os.makedirs("dump")

    # Save the Shopify product inputs as JSON
    with open(os.path.join("dump", "shopify_products.py"), "w") as f:
        json.dump([product.to_dict() for product in shopify_products], f, indent=2)
