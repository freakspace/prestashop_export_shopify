from dump_products import dump_products
from feature_mapping import run_feature_mapping
from to_jsonl import convert_to_jsonl

if __name__ == "__main__":
    # Dump products
    path = dump_products()

    # Feature mapping
    path = run_feature_mapping(path)

    # To jsonl
    convert_to_jsonl(path)
