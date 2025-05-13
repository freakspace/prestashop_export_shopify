import json

# Extract unique keys from "metafields"
keys = []

with open("dump/shopify_products.jsonl", "r") as file:
    data = [json.loads(line)["input"] for line in file]

for product in data:
    if "metafields" in product:
        for metafield in product["metafields"]:
            keys.append(metafield["key"])

# Convert the set to a sorted list (optional)
unique_keys = set(keys)

provided_keys = {
    "app--3890849--eligibility.eligibility_details",
    "name_extra.name_extra",
    "prestashop_product_id.id",
    "prestashop_url.url",
    "product_feature.areal",
    "product_feature.bredde",
    "product_feature.dimension",
    "product_feature.dobbeltspaerring",
    "product_feature.hojde",
    "product_feature.hojtryk",
    "product_feature.indgang",
    "product_feature.laengde",
    "product_feature.liter-min",
    "product_feature.maks-tryk",
    "product_feature.materiale",
    "product_feature.nw-standard",
    "product_feature.pakning",
    "product_feature.profil-standard",
    "product_feature.serie",
    "product_feature.sikkerhed",
    "product_feature.skotgennemforing",
    "product_feature.slange-laengde",
    "product_feature.svivel",
    "product_feature.tilslutning",
    "product_feature.tilslutning-1",
    "product_feature.tilslutning-2",
    "product_feature.tilslutnings-str",
    "product_feature.tilslutnings-type",
    "product_feature.udgang",
    "product_feature.vandstop",
    "short_description.description",
    "supplier.supplier",
}

processed_provided_keys = {key.split(".", 1)[-1] for key in provided_keys}
print(f"processed_provided_keys: {processed_provided_keys}")
print(f"unique_keys: {unique_keys}")
missing_keys = unique_keys - processed_provided_keys


# Print the result
print(f"missing_keys: {missing_keys}")
