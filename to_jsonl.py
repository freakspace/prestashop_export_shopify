import json
import os


def convert_to_jsonl():
    # Ensure the output directory exists
    os.makedirs("dump", exist_ok=True)

    try:
        # Step 1: Load the existing JSON file
        with open("dump/transformed_shopify_products.json", "r", encoding="utf-8") as f:
            data = json.load(
                f
            )  # Assuming the JSON file contains a list or other iterable structure

        # Step 2: Dump the data as JSONL to the output file
        with open(
            os.path.join("dump", "shopify_products.jsonl"), "w", encoding="utf-8"
        ) as f:
            for item in data:
                # Dump each item as a single line JSON object
                json.dump({"input": item}, f, ensure_ascii=False)
                f.write("\n")  # Write each JSON object on a new line

        print("JSONL file created successfully.")
    except Exception as e:
        print(f"Error while processing files: {e}")


if __name__ == "__main__":
    convert_to_jsonl()
