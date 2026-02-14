from app.models import Product, ProductCreate


class ProductStore:
    def __init__(self) -> None:
        self._products: dict[int, Product] = {}
        self._next_id = 1

    def add(self, payload: ProductCreate) -> Product:
        product = Product(id=self._next_id, **payload.model_dump())
        self._products[self._next_id] = product
        self._next_id += 1
        return product

    def list(self) -> list[Product]:
        return list(self._products.values())

    def get(self, product_id: int) -> Product | None:
        return self._products.get(product_id)
