import numpy as np
import pandas as pd
from pandas.testing import assert_index_equal
from tests.test_eurostat import (
    mock_eust,
    dataset,  # NOTE must be imported in order to let `mock_eust` work
    metadata,  # NOTE must be imported in order to let `mock_eust` work
)  # flake8: noqa
from pages.Data_Import import load_dataset


# NOTE `mock_eust` must appear as parameter in order to be active
def test_load_dataset(mock_eust):  # flake8: noqa
    r = load_dataset("fake-code")
    assert r.index.is_monotonic_increasing
    assert_index_equal(r.columns, pd.Index(["flag", "value"]))
