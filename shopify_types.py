from dataclasses import dataclass
from dataclasses_json import dataclass_json

from typing import List, Optional


@dataclass_json
@dataclass
class MoneyV2:
    amount: float
    currencyCode: str


@dataclass_json
@dataclass
class InventoryItem:
    cost: MoneyV2
    sku: str
    tracked: bool


@dataclass_json
@dataclass
class OptionValue:
    name: str  # Specifies the product option value by name.
    optionName: str  # Specifies the product option by name.


@dataclass_json
@dataclass
class CreateShopifyProductVariantInput:
    inventoryItem: InventoryItem
    inventoryPolicy: str
    optionValues: List[OptionValue]
    price: MoneyV2


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
