import csv
from ps_services import get_categories

categories = get_categories(limit=2)

def build_category_tree(categories):
    category_dict = {int(cat['id']): cat for cat in categories}
    tree = {}
    for cat in categories:
        parent_id = int(cat['id_parent'])
        if parent_id == 0:
            tree[int(cat['id'])] = {'category': cat, 'children': []}
        else:
            if parent_id not in category_dict:
                continue
            parent = category_dict[parent_id]
            if 'children' not in parent:
                parent['children'] = []
            parent['children'].append(cat)
    return tree


def flatten_category_tree(tree, level=0, parent_name=""):
    rows = []
    for cat_id, node in tree.items():
        category_name = node['category']['name']['language']['value']
        rows.append([cat_id, category_name, level, parent_name])
        if 'children' in node['category']:
            rows.extend(flatten_category_tree(
                {int(child['id']): {'category': child} for child in node['category']['children']},
                level + 1,
                category_name
            ))
    return rows


def print_category_tree(tree, level=0):
    for cat_id, node in tree.items():
        print('  ' * level + f"{node['category']['name']['language']['value']} (ID: {cat_id})")
        if 'children' in node['category']:
            print_category_tree({int(child['id']): {'category': child} for child in node['category']['children']}, level + 1)


def visualize_categories():
    categories_data = get_categories(limit=1000)
    categories = categories_data['categories']['category']
    tree = build_category_tree(categories)
    print_category_tree(tree)


def export_categories_to_csv(filename="categories.csv"):
    categories_data = get_categories(limit=1000)
    categories = categories_data['categories']['category']
    tree = build_category_tree(categories)
    rows = flatten_category_tree(tree)

    with open(filename, mode='w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(["ID", "Name", "Level", "Parent Name"])
        writer.writerows(rows)

if __name__ == "__main__":
    export_categories_to_csv()