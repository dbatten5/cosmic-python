from datetime import date, timedelta

import pytest
from models import Batch, OrderLine, OutOfStockError, Product, allocate

today = date.today()
tomorrow = today + timedelta(days=1)
later = tomorrow + timedelta(days=10)

chair = Product("RED-CHAIR")
lamp = Product("TASTELESS-LAMP")
trinket = Product("DECORATIVE-TRINKET")


def make_batch_and_line(product, batch_qty, line_qty):
    return (
        Batch("batch-001", product, batch_qty, eta=today),
        OrderLine("order-123", product, line_qty),
    )


def test_allocating_to_a_batch_reduces_the_available_quantity():
    batch, line = make_batch_and_line(chair, 20, 10)
    batch.allocate(line)
    assert batch.available_quantity == 10


def test_can_allocate_if_available_greater_than_required():
    batch, line = make_batch_and_line(chair, 20, 10)
    assert batch.can_allocate(line)


def test_cannot_allocate_if_available_smaller_than_required():
    batch, line = make_batch_and_line(chair, 5, 10)
    assert batch.can_allocate(line) is False


def test_can_allocate_if_available_equal_to_required():
    batch, line = make_batch_and_line(chair, 5, 5)
    assert batch.can_allocate(line)


def test_can_only_deallocate_allocated_lines():
    batch, unallocated_line = make_batch_and_line(trinket, 20, 2)
    batch.deallocate(unallocated_line)
    assert batch.available_quantity == 20


def test_allocation_is_idempotent():
    batch, line = make_batch_and_line(lamp, 20, 2)
    batch.allocate(line)
    batch.allocate(line)
    assert batch.available_quantity == 18


def test_prefers_warehouse_batches_to_shipments():
    in_stock_batch = Batch("in-stock-batch", lamp, 100, eta=None)
    shipment_batch = Batch("shipment-batch", lamp, 100, eta=tomorrow)
    line = OrderLine("oref", lamp, 10)

    allocate(line, [in_stock_batch, shipment_batch])

    assert in_stock_batch.available_quantity == 90
    assert shipment_batch.available_quantity == 100


def test_prefers_earlier_batches():
    earliest = Batch("speedy-batch", chair, 100, eta=today)
    medium = Batch("normal-batch", chair, 100, eta=tomorrow)
    latest = Batch("slow-batch", chair, 100, eta=later)
    line = OrderLine("order1", chair, 10)

    allocate(line, [medium, earliest, latest])

    assert earliest.available_quantity == 90
    assert medium.available_quantity == 100
    assert latest.available_quantity == 100


def test_raises_out_of_stock_exception_if_cannot_allocate():
    batch = Batch("batch1", chair, 10, eta=today)
    allocate(OrderLine("order1", chair, 10), [batch])

    with pytest.raises(OutOfStockError, match=str(chair)):
        allocate(OrderLine("order2", chair, 1), [batch])
