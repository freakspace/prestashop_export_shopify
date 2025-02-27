from ps_services import get_features

def print_features():
    features = get_features()

    for feature in features["product_features"]["product_feature"]:
        print(feature["id"],  feature["name"]["language"]["value"])
        #print(f"{feature['id']} - {feature['name']['language']['value']}")


if __name__ == "__main__":
    print_features()