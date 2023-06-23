import gzip
import io
from datetime import timedelta
from typing import Dict, List, Tuple

import eurostat
import numpy as np
import pandas as pd
import pandasdmx as sdmx
import requests_cache

from datawizard.definitions import CACHE_PATH
from datawizard.utils import concat_keys_to_values, quote_sanitizer

CODELIST_ENPOINT = "https://ec.europa.eu/eurostat/api/dissemination/sdmx/2.1/codelist/ESTAT/all?format=json&lang=en"
METABASE_ENDPOINT = (
    "https://ec.europa.eu/eurostat/api/dissemination/catalogue/metabase.txt.gz"
)


def get_cached_session(caching_days: int = 7, fast_save=False):
    return requests_cache.CachedSession(
        cache_name=f"{CACHE_PATH}/sdmx",
        backend="sqlite",
        fast_save=fast_save,
        expire_after=timedelta(days=caching_days),
        stale_if_error=True,
        stale_while_revalidate=True,
    )


def eurostat_sdmx_request(caching_days: int = 7, fast_save=False):
    """Returns a sdmx.Request object for the Eurostat API."""
    if caching_days > 1:
        return sdmx.Request(
            "ESTAT",
            cache_name=f"{CACHE_PATH}/sdmx",
            backend="sqlite",
            fast_save=fast_save,
            expire_after=timedelta(days=caching_days),
            stale_if_error=True,
            stale_while_revalidate=True,
        )
    else:
        return sdmx.Request("ESTAT")


def fetch_table_of_contents(caching_days: int = 7) -> pd.DataFrame:
    """Returns dataset codes along various information about it."""
    with requests_cache.enabled(
        cache_name=f"{CACHE_PATH}/sdmx",
        backend="sqlite",
        expire_after=timedelta(days=caching_days),
        stale_if_error=True,
        stale_while_revalidate=True,
    ):
        return eurostat.get_toc_df().set_index("code").sort_index()


def fetch_dataset(code: str, caching_days: int = 7) -> pd.DataFrame:
    """Returns dataset found from eurostat"""
    with requests_cache.enabled(
        cache_name=f"{CACHE_PATH}/sdmx",
        backend="sqlite",
        expire_after=timedelta(days=caching_days),
        stale_if_error=True,
        stale_while_revalidate=True,
    ):
        dataset = eurostat.get_data_df(code, flags=True)
    dataset = dataset if dataset is not None else pd.DataFrame()
    return dataset


def fetch_dataset_codelist(request: sdmx.Request, dataset: str) -> pd.DataFrame:
    """Returns codelist found from eurostat"""
    metadata = request.datastructure(dataset)
    codelist = pd.DataFrame()
    for codes in metadata.codelist.values():  # type: ignore
        codes = sdmx.to_pandas(codes)
        codelist = pd.concat([codelist, codes])
    codelist.index.name = "code"
    if codelist.empty:
        return pd.DataFrame()
    codelist = codelist.rename(columns={"name": "label", "parent": "dimension"})
    codelist["dimension"] = codelist["dimension"].str.lower()
    codelist = codelist.set_index("dimension", append=True).swaplevel()
    return codelist


def preprocess_dataset(df: pd.DataFrame) -> pd.DataFrame:
    """Preprocess dataset by mangling it in a convenient DataFrame."""
    df = df.rename(columns={"geo\\TIME_PERIOD": "geo"})
    indexes = df.columns[~df.columns.str.contains(r"value|flag")].tolist()
    df = df.set_index(indexes)
    values = df.filter(like="value")
    values.columns = values.columns.str.replace("_value", "")
    values.columns = pd.MultiIndex.from_product(
        [["value"], values.columns.tolist()], names=[None, "time"]
    )
    flags = df.filter(like="flag")
    flags.columns = flags.columns.str.replace("_flag", "")
    flags.columns = pd.MultiIndex.from_product(
        [["flag"], flags.columns.tolist()], names=[None, "time"]
    )
    flags = flags.applymap(lambda s: s.replace(":", "").strip()).replace("", np.nan)
    return pd.concat([values, flags], axis=1).stack("time", dropna=False)[["value", "flag"]].dropna(how="all", axis=0)  # type: ignore


def fetch_dataset_and_metadata(
    code: str,
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    # TODO remove dependency from `eurostat_sdmx_request``
    data = fetch_dataset(code)
    data = None if data is None else preprocess_dataset(data)
    metadata = fetch_dataset_codelist(eurostat_sdmx_request(), code)
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


def append_code_descriptions(data: pd.DataFrame, codelist: pd.DataFrame):
    df = data.reset_index()
    cols_to_transform = data.index.names.difference(["time"]).union(["flag"])  # type: ignore
    for dimension in cols_to_transform:
        if dimension == "flag":
            # `flag` is served with a different name in codelist
            code2description = quote_sanitizer(
                codelist.squeeze().loc["obs_flag"]
            ).to_dict()
        else:
            code2description = quote_sanitizer(
                codelist.squeeze().loc[dimension]
            ).to_dict()
        code2code_pipe_description = concat_keys_to_values(code2description)
        df[dimension] = df[dimension].map(code2code_pipe_description)
    data = df.set_index(data.index.names)
    return data


def filter_dataset(
    dataset: pd.DataFrame,
    indexes: Dict[str, List[str]],
    flags: list,
) -> pd.DataFrame:
    # Using copies in order to leave the original untouched
    dataset = dataset.copy()
    indexes = dict(indexes)
    start, end = indexes.pop("time")
    complete_index = pd.MultiIndex.from_product(indexes.values(), names=indexes.keys())
    # Make columns time-oriented for easy slicing
    dataset = dataset.unstack("time").swaplevel(axis=1).sort_index(axis=1)  # type: ignore
    dataset = dataset.loc[
        dataset.index.intersection(complete_index),
        str(start) : str(end),  # flake8: noqa
    ].dropna(how="all")
    if dataset.empty:
        # TODO use pandas `orient=tight` syntax
        return pd.DataFrame(
            columns=["flag", "value"],
            index=pd.MultiIndex(levels=[[], []], codes=[[], []], names=["geo", "time"]),
        )
    # Restore index orientation
    dataset = dataset.stack("time")  # type: ignore
    dataset = dataset.loc[dataset.flag.isin(flags)]
    dataset.index = dataset.index.remove_unused_levels()  # type: ignore TODO Cannot access member
    return dataset


def fetch_codelist(session) -> Dict:
    resp = session.get(CODELIST_ENPOINT)
    return resp.json()


def parse_codelist(json: Dict) -> pd.DataFrame:
    df = pd.json_normalize(json)
    df = df.explode(["link.item"])
    df = df["link.item"].apply(pd.Series)
    df = df.rename(columns={"label": "dimension_label"})
    df = pd.concat(
        [df[df.columns.difference(["extension"])], df["extension"].apply(pd.Series)],
        axis=1,
    )
    df["category"] = df["category"].apply(pd.Series)["label"]
    df["category"] = df["category"].apply(lambda d: d.items())
    df = df.explode("category")
    df["code"] = df["category"].str[0]
    df["code_label"] = df["category"].str[1]
    df = df.drop(columns="category")
    df["id"] = df["id"].str.lower()
    df = df.rename(columns={"id": "dimension"})
    df = df.set_index(["dimension", "code"])[
        ["dimension_label", "code_label"]
    ].sort_index()
    return df


def fetch_metabase(session) -> pd.DataFrame:
    resp = session.get(METABASE_ENDPOINT)
    resp = gzip.decompress(resp.content)
    data = resp.decode("utf-8")
    df = pd.read_csv(
        io.StringIO(data),
        delimiter="\t",
        header=None,
        names=["dataset", "dimension", "code"],
    )
    return df
