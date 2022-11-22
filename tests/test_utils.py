from src.utils import concat_keys_to_values


def test_concat_keys_to_values():
    d = {
        "A": "A",
        "B": "B",
        "C": "C",
    }
    d = concat_keys_to_values(d)
    assert d == {
        "A": "A | A",
        "B": "B | B",
        "C": "C | C",
    }
