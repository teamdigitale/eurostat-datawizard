import pytest
import numpy as np
import pandas as pd
import pandas.api.types as ptypes
from pandas.testing import assert_frame_equal, assert_index_equal
from src.eurostat import (
    fetch_dataset_and_metadata,
    cast_time_to_datetimeindex,
    split_dimensions_and_attributes_from,
    filter_dataset,
)


@pytest.fixture()
def dataset():
    # Emulate a downloaded dataset from EuroStat
    df = pd.DataFrame(
        {
            "value": {
                ("CB_EU_FOR", "I_IUG_DKPC", "PC_IND", "AL", "2015"): np.nan,
                ("CB_EU_FOR", "I_IUG_DKPC", "PC_IND", "AL", "2016"): 100.0,
                ("CB_EU_FOR", "I_IUG_DKPC", "PC_IND", "IT", "2021"): 100.0,
                ("CB_EU_FOR", "I_IUG_DKPC", "PC_IND", "IT", "2018"): 100.0,
            },
            "flag": {
                ("CB_EU_FOR", "I_IUG_DKPC", "PC_IND", "AL", "2015"): np.nan,
                ("CB_EU_FOR", "I_IUG_DKPC", "PC_IND", "AL", "2016"): np.nan,
                ("CB_EU_FOR", "I_IUG_DKPC", "PC_IND", "IT", "2021"): np.nan,
                ("CB_EU_FOR", "I_IUG_DKPC", "PC_IND", "IT", "2018"): "u",
            },
        }
    )
    df.index = df.index.set_names(["ind_type", "indic_is", "unit", "geo", "time"])
    return df


@pytest.fixture()
def geo_time_inverted_dataset():
    # Emulate a downloaded dataset from EuroStat
    df = pd.DataFrame(
        {
            "value": {
                ("CB_EU_FOR", "I_IUG_DKPC", "PC_IND", "2015", "AL"): np.nan,
                ("CB_EU_FOR", "I_IUG_DKPC", "PC_IND", "2016", "AL"): 100.0,
                ("CB_EU_FOR", "I_IUG_DKPC", "PC_IND", "2021", "IT"): 100.0,
                ("CB_EU_FOR", "I_IUG_DKPC", "PC_IND", "2018", "IT"): 100.0,
            },
            "flag": {
                ("CB_EU_FOR", "I_IUG_DKPC", "PC_IND", "2015", "AL"): np.nan,
                ("CB_EU_FOR", "I_IUG_DKPC", "PC_IND", "2016", "AL"): np.nan,
                ("CB_EU_FOR", "I_IUG_DKPC", "PC_IND", "2021", "IT"): np.nan,
                ("CB_EU_FOR", "I_IUG_DKPC", "PC_IND", "2018", "IT"): "u",
            },
        }
    )
    df.index = df.index.set_names(["ind_type", "indic_is", "unit", "time", "geo"])
    return df


@pytest.fixture()
def monthly_dataset():
    # Emulate a downloaded dataset from EuroStat
    df = pd.DataFrame(
        {
            "value": {
                ("CB_EU_FOR", "I_IUG_DKPC", "PC_IND", "AL", "2015M1"): np.nan,
                ("CB_EU_FOR", "I_IUG_DKPC", "PC_IND", "AL", "2016M3"): 100.0,
                ("CB_EU_FOR", "I_IUG_DKPC", "PC_IND", "AL", "2021M12"): 100.0,
                ("CB_EU_FOR", "I_IUG_DKPC", "PC_IND", "AL", "2018M10"): 100.0,
            },
            "flag": {
                ("CB_EU_FOR", "I_IUG_DKPC", "PC_IND", "AL", "2015M1"): np.nan,
                ("CB_EU_FOR", "I_IUG_DKPC", "PC_IND", "AL", "2016M3"): np.nan,
                ("CB_EU_FOR", "I_IUG_DKPC", "PC_IND", "AL", "2021M12"): np.nan,
                ("CB_EU_FOR", "I_IUG_DKPC", "PC_IND", "AL", "2018M10"): "u",
            },
        }
    )
    df.index = df.index.set_names(["ind_type", "indic_is", "unit", "geo", "time"])
    return df


@pytest.fixture()
def quarterly_dataset():
    # Emulate a downloaded dataset from EuroStat
    df = pd.DataFrame(
        {
            "value": {
                ("CB_EU_FOR", "I_IUG_DKPC", "PC_IND", "AL", "2015Q1"): np.nan,
                ("CB_EU_FOR", "I_IUG_DKPC", "PC_IND", "AL", "2016Q2"): 100.0,
                ("CB_EU_FOR", "I_IUG_DKPC", "PC_IND", "AL", "2021Q3"): 100.0,
                ("CB_EU_FOR", "I_IUG_DKPC", "PC_IND", "AL", "2018Q4"): 100.0,
            },
            "flag": {
                ("CB_EU_FOR", "I_IUG_DKPC", "PC_IND", "AL", "2015Q1"): np.nan,
                ("CB_EU_FOR", "I_IUG_DKPC", "PC_IND", "AL", "2016Q2"): np.nan,
                ("CB_EU_FOR", "I_IUG_DKPC", "PC_IND", "AL", "2021Q3"): np.nan,
                ("CB_EU_FOR", "I_IUG_DKPC", "PC_IND", "AL", "2018Q4"): "u",
            },
        }
    )
    df.index = df.index.set_names(["ind_type", "indic_is", "unit", "geo", "time"])
    return df


@pytest.fixture()
def weekly_dataset():
    # Emulate a downloaded dataset from EuroStat
    df = pd.DataFrame(
        {
            "value": {
                ("CB_EU_FOR", "I_IUG_DKPC", "PC_IND", "AL", "2015W01"): np.nan,
                ("CB_EU_FOR", "I_IUG_DKPC", "PC_IND", "AL", "2016W12"): 100.0,
                ("CB_EU_FOR", "I_IUG_DKPC", "PC_IND", "AL", "2021W30"): 100.0,
                ("CB_EU_FOR", "I_IUG_DKPC", "PC_IND", "AL", "2018W45"): 100.0,
            },
            "flag": {
                ("CB_EU_FOR", "I_IUG_DKPC", "PC_IND", "AL", "2015W01"): np.nan,
                ("CB_EU_FOR", "I_IUG_DKPC", "PC_IND", "AL", "2016W12"): np.nan,
                ("CB_EU_FOR", "I_IUG_DKPC", "PC_IND", "AL", "2021W30"): np.nan,
                ("CB_EU_FOR", "I_IUG_DKPC", "PC_IND", "AL", "2018W45"): "u",
            },
        }
    )
    df.index = df.index.set_names(["ind_type", "indic_is", "unit", "geo", "time"])
    return df


@pytest.fixture()
def metadata():
    # Emulate a downloaded metadata from EuroStat
    dimensions = pd.DataFrame(
        {
            "label": {
                (
                    "ind_type",
                    "CB_EU_FOR",
                ): "Individuals who are born in another EU Member State",
                (
                    "indic_is",
                    "I_IUG_DKPC",
                ): "Individuals used the internet on a desktop computer",
                ("unit", "PC_IND"): "Percentage of individuals",
                ("geo", "AL"): "Albania",
                ("geo", "IT"): "Italy",
            }
        }
    )
    dimensions.index = dimensions.index.set_names(["dimension", "code"])
    attributes = pd.DataFrame(
        {
            "label": {
                ("obs_flag", "f"): "forecast",
                ("obs_flag", "u"): "low reliability",
                ("obs_flag", "d"): "definition differs, see metadata",
            }
        }
    )
    attributes.index = attributes.index.set_names(["attribute", "code"])
    meta = {
        "dimensions": dimensions,
        "attributes": attributes,
    }
    return meta


@pytest.fixture()
def mock_eust(mocker, dataset, metadata):
    mocker.patch(
        "src.eurostat.eust.download_table",
        return_value=None,
    )
    mocker.patch(
        "src.eurostat.eust.read_table_data",
        return_value=dataset,
    )
    mocker.patch(
        "src.eurostat.eust.read_table_metadata",
        return_value=metadata,
    )


def test_fetch_dataset_and_metadata(mock_eust):
    r = fetch_dataset_and_metadata("fake-code")
    assert isinstance(r, tuple)
    assert isinstance(r[0], pd.DataFrame)
    assert isinstance(r[1], dict)
    assert len(r[0]) == 3
    assert len(r[0].index.levels[-1]) == 3  # type: ignore TODO Cannot access member


def test_cast_time_to_datetimeindex(
    dataset,
    geo_time_inverted_dataset,
    monthly_dataset,
    quarterly_dataset,
    weekly_dataset,
):
    dataset = cast_time_to_datetimeindex(dataset)
    assert ptypes.is_datetime64_dtype(dataset.index.get_level_values("time"))  # type: ignore
    assert dataset.index.is_monotonic_increasing

    dataset = cast_time_to_datetimeindex(geo_time_inverted_dataset)
    assert ptypes.is_datetime64_dtype(dataset.index.get_level_values("time"))  # type: ignore
    assert dataset.index.is_monotonic_increasing

    dataset = cast_time_to_datetimeindex(monthly_dataset)
    assert ptypes.is_datetime64_dtype(monthly_dataset.index.get_level_values("time"))  # type: ignore

    with pytest.raises((AssertionError, NotImplementedError)):
        cast_time_to_datetimeindex(quarterly_dataset)
        cast_time_to_datetimeindex(weekly_dataset)


def test_split_dimensions_and_attributes_from(metadata):
    r = split_dimensions_and_attributes_from(metadata, "fake-code")
    assert isinstance(r, tuple)
    assert isinstance(r[0], pd.Series)
    assert isinstance(r[1], pd.Series)
    assert r[0].name == r[1].name == "fake-code"


def test_filter_dataset(dataset):
    original = cast_time_to_datetimeindex(dataset)
    indexes = {
        "ind_type": ["CB_EU_FOR"],
        "indic_is": ["I_IUG_DKPC"],
        "unit": ["PC_IND"],
        "geo": ["AL", "IT"],
        "time": [2015, 2021],
    }
    flags = [np.nan, "u"]
    dataset = filter_dataset(original, indexes, flags)
    expected = original[["flag", "value"]].iloc[1:]
    assert_frame_equal(dataset, expected)

    indexes["geo"] = ["IT"]
    indexes["time"] = [2021, 2021]
    flags = [np.nan]
    dataset = filter_dataset(original, indexes, flags)
    expected = original[["flag", "value"]].iloc[[-1]]
    assert_frame_equal(dataset, expected)

    indexes["geo"] = ["AL"]
    dataset = filter_dataset(original, indexes, flags)
    assert dataset.empty
    assert_index_equal(dataset.columns, pd.Index(["flag", "value"]))
    assert dataset.index.names == ["unit", "geo", "time"]
