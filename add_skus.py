import json
import re

INPUT_PATH = "dump/transformed_shopify_products.json"
OUTPUT_PATH = "dump/transformed_shopify_products_with_skus.json"

def find_highest_ic_sku(products):
    max_num = 0
    ic_pattern = re.compile(r"^IC(\d+)$", re.IGNORECASE)
    for product in products:
        for variant in product.get("variants", []):
            sku = variant.get("inventoryItem", {}).get("sku", "")
            match = ic_pattern.match(sku)
            if match:
                num = int(match.group(1))
                if num > max_num:
                    max_num = num
    return max_num

def assign_ic_variant_skus(products, start_num):
    next_num = start_num + 1
    ic_pattern = re.compile(r"^IC(\d+)$", re.IGNORECASE)
    for product in products:
        for variant in product.get("variants", []):
            inv_item = variant.get("inventoryItem", {})
            vsku = inv_item.get("sku", "")
            # Only assign if missing or empty (not if already a non-empty SKU)
            if not vsku or not vsku.strip():
                inv_item["sku"] = f"IC{next_num}"
                variant["inventoryItem"] = inv_item
                next_num += 1
    return products

def run_skus(path: str):
    with open(path, "r") as f:
        products = json.load(f)

    highest_ic = find_highest_ic_sku(products)
    products = assign_ic_variant_skus(products, highest_ic)

    with open(OUTPUT_PATH, "w") as f:
        json.dump(products, f, indent=2, ensure_ascii=False)
    print(f"Variant SKUs assigned (no override). Output written to {OUTPUT_PATH}")

    return OUTPUT_PATH