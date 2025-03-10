import os
import json

def remove_id_keys(data):
    if isinstance(data, dict):
        return {k: remove_id_keys(v) for k, v in data.items() if k != "id"}
    elif isinstance(data, list):
        return [remove_id_keys(item) for item in data]
    else:
        return data

input_file = 'shopify_products.jsonl'
output_file = 'shopify_products_no_id.jsonl'

with open(os.path.join("dump", input_file), 'r') as infile, open(os.path.join("dump", output_file), 'w') as outfile:
    for line in infile:
        product = json.loads(line)
        product_no_id = remove_id_keys(product)
        outfile.write(json.dumps(product_no_id) + '\n')

print(f"Processed file saved as {output_file}")