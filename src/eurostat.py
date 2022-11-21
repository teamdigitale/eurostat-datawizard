from datetime import timedelta
from typing import Dict, List, Mapping, Tuple

import eust
import pandas as pd
import pandasdmx as sdmx


def eurostat_sdmx_request():
    return sdmx.Request(
        "ESTAT",
        cache_name="cache/sdmx",
        backend="sqlite",
        expire_after=timedelta(days=7),
        stale_if_error=True,
        stale_while_revalidate=True,
    )


def fetch_table_of_contents() -> pd.Series:
    """Returns dataset codes as keys and titles as values."""
    # NOTE Access to txt seems quicker than a SDMX call
    return (
        pd.read_table(
            "https://ec.europa.eu/eurostat/estat-navtree-portlet-prod/BulkDownloadListing?file=table_of_contents_en.txt",
            usecols=[0, 1, 2],
            engine="c",
        )
        .query("type == 'dataset'")
        .drop(columns=["type"])
        .transform(lambda x: x.str.strip())
        .set_index("code")
        .squeeze()
        .sort_index()
        .drop_duplicates()
    )


def fetch_dataset_codelist(
    request: sdmx.Request, dataset: str
) -> Tuple[pd.DataFrame, bool]:
    metadata = request.datastructure(f"DSD_{dataset}")
    codelist = pd.DataFrame()
    for codes in metadata.codelist.values():  # type: ignore
        codes = sdmx.to_pandas(codes)
        codes.parent = codes.parent.str[3:]  # Trim unnecessary `CL_`
        codelist = pd.concat([codelist, codes])
    codelist.index.name = "dimension"
    return (
        codelist,
        metadata.response.from_cache,  # type: ignore
    )


def fetch_dataset_and_metadata(
    code: str,
) -> Tuple[pd.DataFrame, Mapping[str, pd.DataFrame]]:
    eust.download_table(code)
    # Datasets in long format happens to have a lot of NA
    data = eust.read_table_data(code).dropna(how="all")
    data.index = data.index.remove_unused_levels()  # type: ignore TODO Cannot access member
    metadata = eust.read_table_metadata(code)
    return data, metadata  # type: ignore TODO Type checking fails


def cast_time_to_datetimeindex(data: pd.DataFrame):
    time_levels = data.index.levels[data.index.names.index("time")]  # type: ignore
    if len(str(time_levels[0])) == 4:
        format = "%Y"
    elif "M" in time_levels[0]:
        format = "%YM%m"
    elif "Q" in time_levels[0]:
        raise NotImplementedError("Quarterly data not implemented yet.")
    elif "W" in time_levels[0]:
        raise NotImplementedError("Weekly data not implemented yet.")
    else:  # NOTE This should never occured, according to date format specification
        format = None
    assert format, f"Cannot convert {time_levels[0]} into valid date."
    time_index = pd.to_datetime(time_levels, format=format)
    data.index = data.index.set_levels(time_index, level="time")  # type: ignore TODO Cannot access member
    return data.sort_index()


def split_dimensions_and_attributes_from(
    meta: Mapping[str, pd.DataFrame], code: str
) -> Tuple[pd.Series, pd.Series]:
    return (
        meta["dimensions"]
        .rename(columns={"label": code})
        .droplevel("dimension")
        .squeeze(),
        meta["attributes"]
        .rename(columns={"label": code})
        .droplevel("attribute")
        .squeeze(),
    )


def filter_dataset(
    dataset: pd.DataFrame,
    indexes: Dict[str, List[str]],
    flags: list,
) -> pd.DataFrame:
    indexes = dict(indexes)  # Use a copy in order to leave the original untouched
    start, end = indexes.pop("time")
    complete_index = pd.MultiIndex.from_product(indexes.values(), names=indexes.keys())
    # Make columns time-oriented for easy slicing
    dataset = dataset.unstack("time").swaplevel(axis=1).sort_index(axis=1)  # type: ignore
    dataset = dataset.loc[
        dataset.index.intersection(complete_index),
        str(start) : str(end),  # flake8: noqa
    ].dropna(how="all")
    if dataset.empty:
        return pd.DataFrame(
            columns=["flag", "value"],
            index=pd.MultiIndex(
                levels=[[], [], []], codes=[[], [], []], names=["unit", "geo", "time"]
            ),
        )
    # Restore index orientation
    dataset = dataset.stack("time")  # type: ignore
    dataset = dataset.loc[dataset.flag.isin(flags)]
    return dataset
