from importlib import import_module

import numpy as np
import pandas as pd
from pandas.testing import assert_index_equal

from tests.test_eurostat import mock_eust  # flake8: noqa
from tests.test_eurostat import (  # NOTE must be imported in order to let `mock_eust` work
    dataset,
    metadata,
)


# NOTE `mock_eust` must appear as parameter in order to be active
def test_load_dataset(mock_eust):  # flake8: noqa
    r = import_module("pages.2_🗄️_Data").load_dataset("fake-code")
    assert r.index.is_monotonic_increasing
    assert_index_equal(r.columns, pd.Index(["flag", "value"]))
