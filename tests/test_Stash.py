from importlib import import_module

import numpy as np
import pandas as pd
from pandas.testing import assert_index_equal

from tests.test_eurostat import (
    dataset,
)  # NOTE must be imported in order to let `mock_eust` work
from tests.test_eurostat import (
    metadata,
)  # NOTE must be imported in order to let `mock_eust` work
from tests.test_eurostat import mock_eust  # flake8: noqa


# NOTE `mock_eust` must appear as parameter in order to be active
def test_load_stash(mock_eust):  # flake8: noqa
    stash = {
        "fake-code": {
            "indexes": {
                "ind_type": [
                    "CB_EU_FOR | Individuals who are born in another EU Member State"
                ],
                "indic_is": [
                    "I_IUG_DKPC | Individuals used the internet on a desktop computer"
                ],
                "unit": ["PC_IND | Percentage of individuals"],
                "geo": ["AL | Albania", "IT | Italy"],
                "time": [2016, 2021],
            },
            "flags": [np.nan, "low reliability"],
            "stash": True,
        },
        "code_not_stashed": {
            "indexes": None,
            "flags": None,
            "stash": False,
        },
    }
    df = import_module("pages.3_🛒_Stash").load_stash(stash)
    assert len(df) == 3
    assert "dataset" in df.index.names
    assert "geo" in df.index.names
    assert "time" in df.index.names
    assert_index_equal(df.columns, pd.Index(["flag", "value"]))
