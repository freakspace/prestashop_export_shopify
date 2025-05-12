import json


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


with open("dump/transformed_shopify_products.json", "r") as file:
    data = json.load(file)

for product in data:
    if "handle" in product:
        product["handle"] = ensure_unique_handle(product["handle"])
    if "brand" in product:
        product["brand"]["handle"] = {
            "handle": product["brand"]["handle"],
            "type": "brand",
        }

with open("dump/handles_transformed_shopify_products.json", "w") as file:
    json.dump(data, file, indent=2)
