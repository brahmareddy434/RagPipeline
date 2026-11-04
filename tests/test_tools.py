import pytest

from app.tools import Calculator, OrderRepository


def test_calculator():
    assert Calculator().run("(10 + 2) * 3") == 36


def test_calculator_blocks_code():
    with pytest.raises(ValueError):
        Calculator().run("__import__('os').system('whoami')")


def test_order_lookup():
    assert OrderRepository().lookup("ord-1001") == "Shipped"

