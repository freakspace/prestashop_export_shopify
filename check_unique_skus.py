import json

INPUT_PATH = "dump/transformed_shopify_products_with_skus.json"

def get_all_variant_skus(products):
    skus = []
    for product in products:
        for variant in product.get("variants", []):
            sku = variant.get("inventoryItem", {}).get("sku", "")
            if sku:
                skus.append(sku)
    return skus

def main():
    with open(INPUT_PATH, "r") as f:
        products = json.load(f)

    skus = get_all_variant_skus(products)
    unique_skus = set(skus)

    print(f"Total SKUs: {len(skus)}")
    print(f"Unique SKUs: {len(unique_skus)}")

    if len(skus) == len(unique_skus):
        print("✅ All variant SKUs are unique.")
    else:
        print("❌ Duplicate SKUs found!")
        # Print duplicates
        from collections import Counter
        for sku, count in Counter(skus).items():
            if count > 1:
                print(f"{sku}: {count} times")

if __name__ == "__main__":
    main()