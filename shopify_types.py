from dataclasses import dataclass
from dataclasses_json import (
    dataclass_json,
    DataClassJsonMixin,
    LetterCase,
    config,
    Undefined,
)

from typing import List, Optional


class ExcludeNullMixin(DataClassJsonMixin):
    dataclass_json_config = config(  # type: ignore
        letter_case=LetterCase.CAMEL,  # type: ignore
        undefined=Undefined.EXCLUDE,
        exclude=lambda f: f is None,  # type: ignore
    )["dataclasses_json"]


@dataclass_json
@dataclass
class Image(ExcludeNullMixin):
    src: str
    alt: Optional[str] = None


@dataclass_json
@dataclass
class File(ExcludeNullMixin):
    contentType: str
    originalSource: str
    alt: Optional[str] = None
    filename: Optional[str] = None


@dataclass_json
@dataclass
class MoneyV2(ExcludeNullMixin):
    amount: str
    currencyCode: str


@dataclass_json
@dataclass
class InventoryItem(ExcludeNullMixin):
    cost: MoneyV2
    sku: str
    tracked: bool


@dataclass_json
@dataclass
class VariantOptionValue(ExcludeNullMixin):
    name: str  # Specifies the product option value by name.
    optionName: str  # Specifies the product option by name.


@dataclass_json
@dataclass
class OptionValue(ExcludeNullMixin):
    name: str  # Specifies the name of the option value.


@dataclass_json
@dataclass
class ProductOptionValue(ExcludeNullMixin):
    name: str  # Specifies the product option value by name.
    values: List[OptionValue]  # Specifies the product option by name.


@dataclass_json
@dataclass
class CreateShopifyProductVariantInput(ExcludeNullMixin):
    barcode: str
    inventoryItem: InventoryItem
    inventoryPolicy: str  # CONTINUE = Customers can buy this product variant after it's out of stock.
    price: MoneyV2
    optionValues: List[VariantOptionValue]


@dataclass_json
@dataclass
class SEO(ExcludeNullMixin):
    description: str
    title: str


@dataclass_json
@dataclass
class Product(ExcludeNullMixin):
    title: str
    descriptionHtml: str
    handle: str
    seo: SEO
    status: str
    productOptions: List[ProductOptionValue]
    vendor: str = "Induclean"


@dataclass_json
@dataclass
class CreateShopifyMediaPayload(ExcludeNullMixin):
    alt: str
    mediaContentType: str
    originalSource: str


@dataclass_json
@dataclass
class ShopifyMetaField(ExcludeNullMixin):
    namespace: str
    key: str
    value: str
    type: str


@dataclass_json
@dataclass
class CreateShopifyMediaPayload(ExcludeNullMixin):
    alt: str
    mediaContentType: str
    originalSource: str


@dataclass_json
@dataclass
class CreateShopifyProductInput(ExcludeNullMixin):
    product: Product
    media: List[CreateShopifyMediaPayload]
    metafields: List[ShopifyMetaField]
    variants: List[CreateShopifyProductVariantInput]


@dataclass_json
@dataclass
class CreateCollectionInput(ExcludeNullMixin):
    title: str
    descriptionHtml: Optional[str] = None
    image: Optional[Image] = None
    handle: Optional[str] = None
    seo: Optional[SEO] = None
    metafields: Optional[List[ShopifyMetaField]] = None


@dataclass_json
@dataclass
class ProductSet(ExcludeNullMixin):
    title: str
    descriptionHtml: str
    handle: str
    seo: SEO
    status: str
    vendor: str
    files: List[File]  # TODO Give file a better name
    metafields: List[ShopifyMetaField]
    variants: List[CreateShopifyProductVariantInput]
    id: Optional[str] = None # Supply id if updating an existing product
    productOptions: Optional[List[ProductOptionValue]] = None
    collections: Optional[List[CreateCollectionInput]] = None
