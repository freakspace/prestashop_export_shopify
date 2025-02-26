from dataclasses import dataclass
from dataclasses_json import (
    dataclass_json,
    DataClassJsonMixin,
    LetterCase,
    config,
    Undefined,
)

from typing import List, Optional


class Mixin(DataClassJsonMixin):
    dataclass_json_config = config(  # type: ignore
        letter_case=LetterCase.CAMEL,  # type: ignore
        undefined=Undefined.EXCLUDE,
        exclude=lambda f: f is None,  # type: ignore
    )["dataclasses_json"]


@dataclass_json
@dataclass
class MoneyV2:
    amount: str
    currencyCode: str


@dataclass_json
@dataclass
class InventoryItem:
    cost: MoneyV2
    sku: str
    tracked: bool


@dataclass_json
@dataclass
class VariantOptionValue:
    name: str  # Specifies the product option value by name.
    optionName: str  # Specifies the product option by name.


@dataclass_json
@dataclass
class OptionValue:
    name: str  # Specifies the name of the option value.


@dataclass_json
@dataclass
class ProductOptionValue:
    name: str  # Specifies the product option value by name.
    values: List[OptionValue]  # Specifies the product option by name.


@dataclass_json
@dataclass
class CreateShopifyProductVariantInput:
    barcode: str
    inventoryItem: InventoryItem
    inventoryPolicy: str  # CONTINUE = Customers can buy this product variant after it's out of stock.
    price: MoneyV2
    optionValues: List[VariantOptionValue]


@dataclass_json
@dataclass
class SEO:
    description: str
    title: str


@dataclass_json
@dataclass
class Product:
    title: str
    descriptionHtml: str
    handle: str
    seo: SEO
    status: str
    vendor: str
    productOptions: List[ProductOptionValue]


@dataclass_json
@dataclass
class CreateShopifyMediaPayload:
    alt: str
    mediaContentType: str
    originalSource: str


@dataclass_json
@dataclass
class ShopifyMetaField:
    namespace: str
    key: str
    value: str
    type: str


@dataclass_json
@dataclass
class CreateShopifyMediaPayload:
    alt: str
    mediaContentType: str
    originalSource: str


@dataclass_json
@dataclass
class CreateShopifyProductInput:
    product: Product
    media: List[CreateShopifyMediaPayload]
    metafields: List[ShopifyMetaField]
    variants: List[CreateShopifyProductVariantInput]


@dataclass_json
@dataclass
class ProductSet(Mixin):
    title: str
    descriptionHtml: str
    handle: str
    seo: SEO
    status: str
    vendor: str
    metafields: List[ShopifyMetaField]
    variants: List[CreateShopifyProductVariantInput]
    productOptions: Optional[List[ProductOptionValue]] = None
