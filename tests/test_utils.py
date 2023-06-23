import pandas as pd
from pandas.testing import assert_series_equal
from datawizard.utils import concat_keys_to_values, quote_sanitizer


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


def test_quote_sanitizer():
    s = pd.Series(["A", "'B'", "C"])
    assert_series_equal(quote_sanitizer(s), pd.Series(["A", "-B-", "C"]))
