import numpy as np
import pandas as pd
from pandas.testing import assert_index_equal
from tests.test_eurostat import (
    mock_eust,
    dataset,  # NOTE must be imported in order to let `mock_eust` work
    metadata,  # NOTE must be imported in order to let `mock_eust` work
)  # flake8: noqa
from pages.Data_Import import load_dataset, load_stash


# NOTE `mock_eust` must appear as parameter in order to be active
def test_load_dataset(mock_eust):  # flake8: noqa
    r = load_dataset("fake-code")
    assert r.index.is_monotonic_increasing
    assert_index_equal(r.columns, pd.Index(["flag", "value"]))


# NOTE `mock_eust` must appear as parameter in order to be active
def test_load_stash(mock_eust):  # flake8: noqa
    stash = {
        "fake-code": {
            "indexes": {
                "ind_type": ["Individuals who are born in another EU Member State"],
                "indic_is": ["Individuals used the internet on a desktop computer"],
                "unit": ["Percentage of individuals"],
                "geo": ["Albania", "Italy"],
                "time": [2016, 2021],
            },
            "flags": [np.nan, "low reliability"],
        },
    }
    df = load_stash(stash)
    assert len(df) == 3
    assert_index_equal(df.columns, pd.Index(["flag", "value"]))
