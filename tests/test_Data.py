import numpy as np
import pandas as pd
import pandas.api.types as ptypes
import pytest
from pandas.testing import assert_frame_equal, assert_index_equal

from datawizard.data import (
    append_code_descriptions,
    cast_time_to_datetimeindex,
    fetch_dataset,
    fetch_dataset_and_metadata,
    fetch_table_of_contents,
    filter_dataset,
    parse_codelist,
    preprocess_dataset,
)


@pytest.fixture()
def raw_table_of_contents():
    # Emulate toc from EuroStat
    return pd.DataFrame(
        {
            "title": {
                1: "Consumers - monthly data",
                2: "Consumers - quarterly data",
            },
            "code": {1: "EI_BSCO_M", 2: "EI_BSCO_Q"},
            "type": {1: "dataset", 2: "dataset"},
            "last update of data": {
                1: "2023-05-30T11:00:00+0200",
                2: "2023-05-30T11:00:00+0200",
            },
            "last table structure change": {
                1: "2023-05-30T11:00:00+0200",
                2: "2023-05-30T11:00:00+0200",
            },
            "data start": {1: "1980-01", 2: "1980-01"},
            "data end": {1: "2023-01", 2: "2023-01"},
        }
    )


@pytest.fixture()
def raw_dataset():
    # Emulate a downloaded dataset from `eurostat`
    df = pd.DataFrame.from_dict(
        {
            "ind_type": {0: "CB_EU_FOR", 1: "CB_EU_FOR"},
            "indic_is": {0: "I_IUG_DKPC", 1: "I_IUG_DKPC"},
            "unit": {0: "PC_IND", 1: "PC_IND"},
            "geo\\TIME_PERIOD": {0: "AL", 1: "IT"},
            "2015_value": {0: np.nan, 1: np.nan},
            "2015_flag": {0: ":", 1: ""},
            "2016_value": {0: 100.0, 1: np.nan},
            "2016_flag": {0: ":", 1: ""},
            "2021_value": {0: np.nan, 1: 100.0},
            "2021_flag": {0: "", 1: ":"},
            "2018_value": {0: np.nan, 1: 100.0},
            "2018_flag": {0: "", 1: "u"},
        }
    )
    return df


@pytest.fixture()
def dataset():
    # Emulate a processed dataset
    df = pd.DataFrame(
        {
            "value": {
                ("CB_EU_FOR", "I_IUG_DKPC", "PC_IND", "AL", "2016"): 100.0,
                ("CB_EU_FOR", "I_IUG_DKPC", "PC_IND", "IT", "2018"): 100.0,
                ("CB_EU_FOR", "I_IUG_DKPC", "PC_IND", "IT", "2021"): 100.0,
            },
            "flag": {
                ("CB_EU_FOR", "I_IUG_DKPC", "PC_IND", "AL", "2016"): np.nan,
                ("CB_EU_FOR", "I_IUG_DKPC", "PC_IND", "IT", "2018"): "u",
                ("CB_EU_FOR", "I_IUG_DKPC", "PC_IND", "IT", "2021"): np.nan,
            },
        }
    )
    df.index = df.index.set_names(["ind_type", "indic_is", "unit", "geo", "time"])
    return df


@pytest.fixture()
def geo_time_inverted_dataset():
    # Emulate a processed dataset
    df = pd.DataFrame(
        {
            "value": {
                ("CB_EU_FOR", "I_IUG_DKPC", "PC_IND", "2016", "AL"): 100.0,
                ("CB_EU_FOR", "I_IUG_DKPC", "PC_IND", "2018", "IT"): 100.0,
                ("CB_EU_FOR", "I_IUG_DKPC", "PC_IND", "2021", "IT"): 100.0,
            },
            "flag": {
                ("CB_EU_FOR", "I_IUG_DKPC", "PC_IND", "2016", "AL"): np.nan,
                ("CB_EU_FOR", "I_IUG_DKPC", "PC_IND", "2018", "IT"): "u",
                ("CB_EU_FOR", "I_IUG_DKPC", "PC_IND", "2021", "IT"): np.nan,
            },
        }
    )
    df.index = df.index.set_names(["ind_type", "indic_is", "unit", "time", "geo"])
    return df


@pytest.fixture()
def monthly_dataset():
    # Emulate a processed dataset
    df = pd.DataFrame(
        {
            "value": {
                ("CB_EU_FOR", "I_IUG_DKPC", "PC_IND", "AL", "2016M3"): 100.0,
                ("CB_EU_FOR", "I_IUG_DKPC", "PC_IND", "AL", "2018M10"): 100.0,
                ("CB_EU_FOR", "I_IUG_DKPC", "PC_IND", "AL", "2021M12"): 100.0,
            },
            "flag": {
                ("CB_EU_FOR", "I_IUG_DKPC", "PC_IND", "AL", "2016M3"): np.nan,
                ("CB_EU_FOR", "I_IUG_DKPC", "PC_IND", "AL", "2018M10"): "u",
                ("CB_EU_FOR", "I_IUG_DKPC", "PC_IND", "AL", "2021M12"): np.nan,
            },
        }
    )
    df.index = df.index.set_names(["ind_type", "indic_is", "unit", "geo", "time"])
    return df


@pytest.fixture()
def quarterly_dataset():
    # Emulate a processed dataset
    df = pd.DataFrame(
        {
            "value": {
                ("CB_EU_FOR", "I_IUG_DKPC", "PC_IND", "AL", "2016Q2"): 100.0,
                ("CB_EU_FOR", "I_IUG_DKPC", "PC_IND", "AL", "2018Q4"): 100.0,
                ("CB_EU_FOR", "I_IUG_DKPC", "PC_IND", "AL", "2021Q3"): 100.0,
            },
            "flag": {
                ("CB_EU_FOR", "I_IUG_DKPC", "PC_IND", "AL", "2016Q2"): np.nan,
                ("CB_EU_FOR", "I_IUG_DKPC", "PC_IND", "AL", "2018Q4"): "u",
                ("CB_EU_FOR", "I_IUG_DKPC", "PC_IND", "AL", "2021Q3"): np.nan,
            },
        }
    )
    df.index = df.index.set_names(["ind_type", "indic_is", "unit", "geo", "time"])
    return df


@pytest.fixture()
def weekly_dataset():
    # Emulate a processed dataset
    df = pd.DataFrame(
        {
            "value": {
                ("CB_EU_FOR", "I_IUG_DKPC", "PC_IND", "AL", "2016W12"): 100.0,
                ("CB_EU_FOR", "I_IUG_DKPC", "PC_IND", "AL", "2018W45"): 100.0,
                ("CB_EU_FOR", "I_IUG_DKPC", "PC_IND", "AL", "2021W30"): 100.0,
            },
            "flag": {
                ("CB_EU_FOR", "I_IUG_DKPC", "PC_IND", "AL", "2016W12"): np.nan,
                ("CB_EU_FOR", "I_IUG_DKPC", "PC_IND", "AL", "2018W45"): "u",
                ("CB_EU_FOR", "I_IUG_DKPC", "PC_IND", "AL", "2021W30"): np.nan,
            },
        }
    )
    df.index = df.index.set_names(["ind_type", "indic_is", "unit", "geo", "time"])
    return df


@pytest.fixture()
def codelist():
    # Emulate a processed codelist
    meta = pd.DataFrame(
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
                ("obs_flag", "f"): "forecast",
                ("obs_flag", "u"): "low reliability",
                ("obs_flag", "d"): "definition differs, see metadata",
            }
        }
    )
    meta.index = meta.index.set_names(["dimension", "code"])
    return meta


def test_fetch_table_of_contents(mocker, raw_table_of_contents):
    mocker.patch(
        "datawizard.data.eurostat.get_toc_df",
        return_value=raw_table_of_contents,
    )
    toc = fetch_table_of_contents()
    assert isinstance(toc, pd.DataFrame)
    assert toc.index.name == "code"
    assert toc.index.is_monotonic_increasing


def test_fetch_dataset(mocker, raw_dataset):
    mocker.patch(
        "datawizard.data.eurostat.get_data_df",
        return_value=raw_dataset,
    )
    data = fetch_dataset("fake-code")
    assert_frame_equal(data, raw_dataset)

    mocker.patch(
        "datawizard.data.eurostat.get_data_df",
        return_value=None,
    )
    data = fetch_dataset("fake-code")
    assert data.empty


def test_preprocess_dataset(mocker, raw_dataset, dataset):
    mocker.patch(
        "datawizard.data.fetch_dataset",
        return_value=dataset,
    )
    data = preprocess_dataset(raw_dataset)
    assert_frame_equal(data, dataset)


def test_fetch_dataset_and_metadata(mocker, raw_dataset, codelist):
    mocker.patch(
        "datawizard.data.fetch_dataset",
        return_value=raw_dataset,
    )
    mocker.patch(
        "datawizard.data.fetch_dataset_codelist",
        return_value=codelist,
    )
    data, metadata = fetch_dataset_and_metadata("fake-code")
    assert isinstance(data, pd.DataFrame)
    assert isinstance(metadata, pd.DataFrame)


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

    with pytest.raises(NotImplementedError):
        cast_time_to_datetimeindex(quarterly_dataset)
        cast_time_to_datetimeindex(weekly_dataset)


def test_append_code_descriptions(dataset, codelist):
    df = append_code_descriptions(dataset, codelist)
    assert_index_equal(
        df.index.get_level_values("geo"),
        pd.Index(
            ["AL | Albania", "IT | Italy", "IT | Italy"], dtype="object", name="geo"
        ),
    )
    assert df["flag"].iloc[1] == "u | low reliability"


def test_filter_dataset(dataset):
    original = cast_time_to_datetimeindex(dataset)
    indexes = {
        "ind_type": ["CB_EU_FOR"],
        "indic_is": ["I_IUG_DKPC"],
        "unit": ["PC_IND"],
        "geo": ["AL", "IT"],
        "time": [2017, 2021],
    }
    flags = [np.nan, "u"]
    dataset = filter_dataset(original, indexes, flags)
    expected = original[["flag", "value"]].iloc[1:]
    print(dataset)
    print(expected)
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
    assert dataset.index.names == ["geo", "time"]


@pytest.fixture
def codelist_response():
    return {
        "version": "2.0",
        "class": "collection",
        "updated": "2023-06-21T09:49:08.027Z",
        "link": {
            "item": [
                {
                    "class": "dimension",
                    "source": "ESTAT",
                    "category": {
                        "label": {
                            "M12": "Last 12 months",
                            "Y5": "Last 5 years",
                            "ADLH": "Adulthood",
                        },
                        "index": ["M12", "Y5", "ADLH"],
                    },
                    "label": "Occurence",
                    "extension": {"lang": "EN", "id": "OCCUR", "version": "1.1"},
                }
            ]
        },
    }


@pytest.fixture
def metabase():
    return pd.DataFrame.from_dict(
        {
            "index": [8603, 309796, 580303, 904900, 1145375],
            "columns": ["dataset", "dimension", "code"],
            "data": [
                ["aei_ps_inp", "geo", "PL22"],
                ["ef_olsecsreg", "geo", "SK03"],
                ["irt_lt_mcby_d", "time", "1997M07D17"],
                ["rail_tf_ns15_ch", "net_seg15", "CHS20146_TEN"],
                ["tps00194", "time", "2015"],
            ],
            "index_names": [None],
            "column_names": [None],
        },
        orient="tight",
    )


def test_parse_codelist(codelist_response):
    df = parse_codelist(codelist_response)
    expected = pd.DataFrame.from_dict(
        {
            "index": [("occur", "ADLH"), ("occur", "M12"), ("occur", "Y5")],
            "columns": ["dimension_label", "code_label"],
            "data": [
                ["Occurence", "Adulthood"],
                ["Occurence", "Last 12 months"],
                ["Occurence", "Last 5 years"],
            ],
            "index_names": ["dimension", "code"],
            "column_names": [None],
        },
        orient="tight",
    )
    print(df)
    print(expected)
    assert_frame_equal(df, expected)
