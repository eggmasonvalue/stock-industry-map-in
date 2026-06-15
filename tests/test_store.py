from src.store import Store

def test_update_stock_valid_length():
    """Verify that update_stock correctly updates the data dictionary when info has 4 elements."""
    store = Store()
    symbol = "TEST_SYM"
    info = ["Macro1", "Sector1", "Industry1", "Basic Industry1"]

    store.update_stock(symbol, info)

    assert store.get_stock(symbol) == info
    assert store.data[symbol] == info

def test_update_stock_invalid_length_short():
    """Verify that update_stock does not update data when info has fewer than 4 elements."""
    store = Store()
    symbol = "TEST_SYM"
    info = ["Macro1", "Sector1", "Industry1"]

    store.update_stock(symbol, info)

    assert store.get_stock(symbol) is None
    assert symbol not in store.data

def test_update_stock_invalid_length_long():
    """Verify that update_stock does not update data when info has more than 4 elements."""
    store = Store()
    symbol = "TEST_SYM"
    info = ["Macro1", "Sector1", "Industry1", "Basic Industry1", "Extra"]

    store.update_stock(symbol, info)

    assert store.get_stock(symbol) is None
    assert symbol not in store.data

def test_update_stock_overwrite():
    """Verify that update_stock overwrites existing data with valid info."""
    store = Store()
    symbol = "TEST_SYM"
    initial_info = ["M1", "S1", "I1", "B1"]
    new_info = ["M2", "S2", "I2", "B2"]

    store.update_stock(symbol, initial_info)
    assert store.get_stock(symbol) == initial_info

    store.update_stock(symbol, new_info)
    assert store.get_stock(symbol) == new_info
