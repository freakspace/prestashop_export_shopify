import json
import ast
from slugify import slugify
from shopify_types import ShopifyMetaField

# TODO Good example https://induclean.dk/slangeopruller/2126-aut-slangeopruller-til-luft-20-bar-5706224097264.html
# TODO https://induclean.dk/kabeloprullere/1902-aut-kabelopruller-ip42--5706224095031.html
# Key mapping (e.g., map "volume" to "size")
key_mapping = {
    "Liter / min.": "Liter min.",
    "Længde (slange)": "Slange længde",
    "Liter min": "Liter min.",
    "Max Tryk": "Maks tryk",
}

# Value mapping (e.g., map "L" to "Large" and "Small/Medium" to "Small" and "Medium")
value_mapping = {
    "Benzin - Diesel": ["Benzin", "Diesel"],
    "Gas - ilt": ["Gas", "ilt"],
    "Gas/ilt": ["Gas", "ilt"],
    "Luft,Vand": ["Luft", "Vand"],
    "Luft,Vand,Olie": ["Luft", "Vand", "Olie"],
    "Luft/Vand": ["Luft", "Vand"],
    "Vand/Hydraulik": ["Vand", "Hydraulik"],
    "Olie/Kølevæske/Emulsion": ["Olie", "Kølevæske", "Emulsion"],
    "Propan gas": ["Propan"],
    "Diesel/Petroleum": ["Diesel", "Petroleum"],
    "DieselPetroleum": ["Diesel", "Petroleum"],
    "Luft,Hygiejnisk": ["Luft", "Hygiejnisk"],
    "Benzin/Diesel": ["Benzin", "Diesel"],
    "Luft,Vand,Benzin/Diesel": ["Luft", "Vand", "Benzin", "Diesel"],
    "AD Blue": ["Adblue"],
    "CEE": ["CEE Stik"],
}


consolidation_mapping = {
    "Luft": "Medie",
    "Vand": "Medie",
    "Olie": "Medie",
    "Fedt": "Medie",
    "Benzin - Diesel": "Medie",
    "Adblue": "Medie",
    "Gas - Ilt": "Medie",
    "Propan": "Medie",
}


def metafields_include_key(metafields, key):
    """
    Check if any metafield in the list has the specified value.

    Args:
        metafields (list): List of ShopifyMetaField objects.
        value (str): The value to check for.

    Returns:
        bool: True if any metafield has the specified value, False otherwise.
    """
    for metafield in metafields:
        if metafield.key == key:
            return True
    return False


def feature_mapping(metafields):
    """
    Maps metafields with namespace "product_feature" to new keys and values.

    Args:
        metafields (list): List of ShopifyMetaField objects.

    Returns:
        list: A list of transformed ShopifyMetaField objects.
    """
    transformed_metafields = {}
    passthrough_metafields = []

    for metafield in metafields:
        if metafield.namespace != "product_feature":
            # Pass through non-product_feature metafields unchanged
            passthrough_metafields.append(metafield)
            continue

        new_key = consolidation_mapping.get(
            metafield.key, key_mapping.get(metafield.key, metafield.key)
        )
        new_value = metafield.value

        # Skip "false" values for consolidated keys
        if metafield.key in consolidation_mapping and new_value == "false":
            continue

        # Handle consolidated keys with "true" values
        if metafield.key in consolidation_mapping and new_value == "true":
            new_value = metafield.key  # Use the original key as the value
            if new_key in transformed_metafields:
                transformed_metafields[new_key].add(new_value)
            else:
                transformed_metafields[new_key] = {new_value}
            continue

        # Map values using value_mapping
        mapped_values = value_mapping.get(new_value, [new_value])
        if not isinstance(mapped_values, list):
            mapped_values = [mapped_values]

        # Add or update the transformed metafield
        if new_key in transformed_metafields:
            transformed_metafields[new_key].update(mapped_values)
        else:
            transformed_metafields[new_key] = set(mapped_values)

    # Convert the transformed_metafields dictionary to a list of ShopifyMetaField objects
    product_feature_metafields = [
        ShopifyMetaField(
            namespace="product_feature",
            key=slugify(key),
            value=(
                json.dumps(list(values))
                if (len(values) > 1 or key == "Medie")
                else list(values)[0]
            ),
            type=(
                "list.single_line_text_field"
                if key == "Medie"
                else "single_line_text_field"
            ),
        )
        for key, values in transformed_metafields.items()
        # Remove metafields with multiple values for specific keys - it doesnt make sense to have 2 different lengths for example
        if not (
            slugify(key)
            in ["hojde", "bredde", "laengde", "maks-tryk", "dimension", "liter-min"]
            and len(values) > 1
        )
    ]
    # TODO Remove duplicates længde etc.

    # Combine product_feature metafields with passthrough metafields
    return passthrough_metafields + product_feature_metafields


def run_feature_mapping(path):
    with open(path, "r") as file:
        data = json.load(file)

    for product in data:
        if (
            "metafields" in product
            and isinstance(product["metafields"], list)
            and len(product["metafields"]) > 0
        ):
            # Convert metafields from dictionaries to ShopifyMetaField objects
            metafields = [
                (
                    ShopifyMetaField(**metafield)
                    if isinstance(metafield, dict)
                    else metafield
                )
                for metafield in product["metafields"]
            ]

            transformed_metafields = feature_mapping(metafields)
            product["metafields"] = [
                metafield.to_dict() for metafield in transformed_metafields
            ]

    with open("dump/transformed_shopify_products.json", "w") as file:
        json.dump(data, file, indent=2)

    return "dump/transformed_shopify_products.json"
