import os
import random

from prestapyt import PrestaShopWebServiceDict, PrestaShopWebServiceError

from dotenv import load_dotenv

load_dotenv()

PS_API_KEY = os.environ.get("PS_API_KEY")
PS_API_URL = os.environ.get("PS_API_URL")

if PS_API_KEY is None:
    raise Exception("You need to set the Prestashp API key")

if PS_API_URL is None:
    raise Exception("You need to set the Prestashp API url")

prestashop = PrestaShopWebServiceDict(
    PS_API_URL,
    PS_API_KEY,
)


def get_products(id: int = None, limit: int = 100, random_sample: bool = False):
    if id:
        return prestashop.get("products", id)

    if random_sample:
        all_products = prestashop.get("products", options={"filter[active]": "[1]"})[
            "products"
        ]["product"]
        all_product_ids = [product["attrs"]["id"] for product in all_products]
        rnd_product_ids = random.sample(all_product_ids, k=limit)
        id_filter = "|".join(map(str, rnd_product_ids))
        return prestashop.get(
            "products",
            options={
                "display": "full",
                "filter[active]": "[1]",
                "filter[id]": f"[{id_filter}]",
            },
        )

    if id is None and limit > 1:
        return prestashop.get(
            "products",
            id,
            options={"display": "full", "filter[active]": "[1]", "limit": limit},
        )

    raise Exception(
        "get_products method requires either an id or a limit greater than 1"
    )


def get_product(id: int):
    return prestashop.get("products", id)


def get_combination(id: int):
    return prestashop.get("combinations", id)


def get_combination(id: int):
    return prestashop.get("combinations", id)


def get_feature(id: int):
    return prestashop.get("product_features", id)


def get_feature_value(id: int):
    return prestashop.get("product_feature_values", id)


def get_product_option_values(id: int):
    return prestashop.get("product_option_values", id)


def get_product_option(id: int):
    try:
        return prestashop.get("product_options", id)
    except PrestaShopWebServiceError as e:
        return None


def get_manufacturer(id: int):
    try:
        return prestashop.get("manufacturers", id)
    except PrestaShopWebServiceError as e:
        print(f"Error getting manufacturer {id}: {e}")
        return None


def get_manufacturer_name(id: int):
    if isinstance(id, str):
        id = int(id)
    if id == 0:
        return ""

    manufacturer = get_manufacturer(id)

    name = manufacturer["manufacturer"]["name"]

    if name == "Karcher":
        name = "Kärcher"

    return name


def get_supplier(id: int):
    return prestashop.get("suppliers", id)


def get_supplier_name(id: int):
    if isinstance(id, str):
        id = int(id)
    if id == 0:
        return ""

    supplier = get_supplier(id)

    return supplier["supplier"]["name"]


def get_product_image(id: int):
    try:
        images = prestashop.get("images/products", id)
    except PrestaShopWebServiceError as e:
        return None
    # Check if declination is a list or a dictionary
    declinations = images["image"]["declination"]

    if isinstance(declinations, dict):
        declinations = [declinations]

    image_data = [
        {
            "url": f"https://induclean.dk//img/p/{'/'.join(list(image['attrs']['id']))}/{image['attrs']['id']}.jpg",
            "alt": (
                image["legend"]["language"]["value"]
                if "legend" in image and "language" in image["legend"]
                else ""
            ),
        }
        for image in declinations
    ]

    return image_data


def get_categories(id: int = None, limit: int = 100):
    if id is None and limit > 1:
        return prestashop.get(
            "categories",
            id,
            options={"display": "full", "filter[active]": "[1]", "limit": limit},
        )
    if id:
        return prestashop.get("categories", id)

    raise Exception(
        "get_categories method requires either an id or a limit greater than 1"
    )


def get_category(id: int):
    return prestashop.get("categories", id)


def get_features(id: int = None, limit: int = 999):
    if id is None and limit > 1:
        return prestashop.get(
            "product_features",
            id,
            options={"display": "full", "limit": limit},
        )
    if id:
        return prestashop.get("product_features", id)

    raise Exception(
        "get_categories method requires either an id or a limit greater than 1"
    )
