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

        new_key = consolidation_mapping.get(metafield.key, key_mapping.get(metafield.key, metafield.key))
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
            value=json.dumps(list(values)) if len(values) > 1 else list(values)[0],
            type="single_line_text_field",
        )
        for key, values in transformed_metafields.items()
        # Remove metafields with multiple values for specific keys - it doesnt make sense to have 2 different lengths for example
        if not (slugify(key) in ["hojde", "bredde", "laengde", "maks-tryk", "dimension", "liter-min"] and len(values) > 1)
    ]
    # TODO Remove duplicates længde etc.


    # Combine product_feature metafields with passthrough metafields
    return passthrough_metafields + product_feature_metafields

if __name__ == "__main__":
    with open("dump/shopify_products.json", "r") as file:
        data = json.load(file)
    
    for product in data:
        if "metafields" in product and isinstance(product["metafields"], list) and len(product["metafields"]) > 0:
            # Convert metafields from dictionaries to ShopifyMetaField objects
            metafields = [
                ShopifyMetaField(**metafield) if isinstance(metafield, dict) else metafield
                for metafield in product["metafields"]
            ]
            
            transformed_metafields = feature_mapping(metafields)
            product["metafields"] = [metafield.to_dict() for metafield in transformed_metafields ]
        
    with open("dump/transformed_shopify_products.json", "w") as file:
        json.dump(data, file, indent=2)

""" # TODO Der er slange-længde og længde-slange

from shopify_types import ShopifyMetaField

TEST_DATA = [
    ShopifyMetaField(namespace='product_feature', key='Højde', value='160,00', type='single_line_text_field'),
    ShopifyMetaField(namespace='product_feature', key='Bredde', value='30,00', type='single_line_text_field'),
    ShopifyMetaField(namespace='product_feature', key='Længde', value='387,00', type='single_line_text_field'),
    ShopifyMetaField(namespace='product_feature', key='Længde', value='120,00', type='single_line_text_field'),
    ShopifyMetaField(namespace='product_feature', key='Bredde', value='178,00', type='single_line_text_field'),
    ShopifyMetaField(namespace='product_feature', key='Højde', value='331,00', type='single_line_text_field'),
    ShopifyMetaField(namespace='product_feature', key='Længde (slange)', value='10m', type='single_line_text_field'),
    ShopifyMetaField(namespace='product_feature', key='Dimension', value='5/16"', type='single_line_text_field'),
    ShopifyMetaField(namespace='product_feature', key='Dimension', value='Andet', type='single_line_text_field'),
    ShopifyMetaField(namespace='product_feature', key='Tilslutning', value='1/4" u.g.', type='single_line_text_field'),
    ShopifyMetaField(namespace='product_feature', key='Max Tryk', value='20,00', type='single_line_text_field'),
    ShopifyMetaField(namespace='product_feature', key='Max Tryk', value='10,50', type='single_line_text_field'),
    ShopifyMetaField(namespace='product_feature', key='Medie', value='Luft', type='single_line_text_field'),
    ShopifyMetaField(namespace='product_feature', key='Materiale', value='Plast', type='single_line_text_field'),
    ShopifyMetaField(namespace='product_feature', key='Liter min', value='200,00', type='single_line_text_field'),
    ShopifyMetaField(namespace='product_feature', key='Maks tryk', value='20', type='single_line_text_field'),
    ShopifyMetaField(namespace='product_feature', key='Slange længde', value='10m', type='single_line_text_field'),
    ShopifyMetaField(namespace='product_feature', key='Indgang', value='3/8" u.g.', type='single_line_text_field'),
    ShopifyMetaField(namespace='product_feature', key='Udgang', value='1/4" u.g.', type='single_line_text_field'),
    ShopifyMetaField(namespace='product_feature', key='Luft', value='true', type='single_line_text_field'),
    ShopifyMetaField(namespace='product_feature', key='Vand', value='false', type='single_line_text_field'),
    ShopifyMetaField(namespace='product_feature', key='Olie', value='false', type='single_line_text_field'),
    ShopifyMetaField(namespace='product_feature', key='Fedt', value='false', type='single_line_text_field'),
    ShopifyMetaField(namespace='product_feature', key='Benzin - Diesel', value='false', type='single_line_text_field'),
    ShopifyMetaField(namespace='product_feature', key='Adblue', value='false', type='single_line_text_field'),
    ShopifyMetaField(namespace='product_feature', key='Gas - Ilt', value='false', type='single_line_text_field'),
    ShopifyMetaField(namespace='product_feature', key='Propan', value='false', type='single_line_text_field'),
    ShopifyMetaField(namespace='product_feature', key='Højtryk', value='false', type='single_line_text_field'),
    ShopifyMetaField(namespace='product_feature', key='Svivel', value='Messing', type='single_line_text_field'),
]

# Pass the parsed data to your function
transformed_metafields = feature_mapping(TEST_DATA)

# Print the transformed metafields
for metafield in transformed_metafields:
    print(metafield) """