from datetime import date

import attrs


class OutOfStockError(Exception):
    pass


@attrs.frozen
class Product:
    sku: str

    def __str__(self) -> str:
        return self.sku


@attrs.frozen
class OrderLine:
    orderid: str
    product: Product
    quantity: int


@attrs.frozen
class Order:
    reference: str
    lines: list[OrderLine]


class Batch:
    def __init__(
        self,
        reference: str,
        product: Product,
        quantity: int,
        eta: date | None,
    ):
        self.reference = reference
        self.product = product
        self._available_quantity = quantity
        self.eta = eta
        self._allocations: set[OrderLine] = set()

    def __eq__(self, other) -> bool:
        if not isinstance(other, Batch):
            return False
        return other.reference == self.reference

    def __hash__(self):
        return hash(self.reference)

    def __gt__(self, other) -> bool:
        if self.eta is None:
            return False
        if other.eta is None:
            return True
        return self.eta > other.eta

    @property
    def available_quantity(self) -> int:
        return self._available_quantity - self.allocated_quantity

    @property
    def allocated_quantity(self) -> int:
        return sum(line.quantity for line in self._allocations)

    def allocate(self, line: OrderLine) -> None:
        if self.can_allocate(line):
            self._allocations.add(line)

    def can_allocate(self, line: OrderLine) -> bool:
        return line.product == self.product and line.quantity <= self.available_quantity

    def deallocate(self, line: OrderLine) -> None:
        if line in self._allocations:
            self._allocations.remove(line)


def allocate(line: OrderLine, batches: list[Batch]) -> str:
    try:
        batch = next(b for b in sorted(batches) if b.can_allocate(line))
    except StopIteration as e:
        raise OutOfStockError(f"Out of stock for product {line.product}") from e
    batch.allocate(line)
    return batch.reference
