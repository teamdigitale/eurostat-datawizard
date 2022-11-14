import eust
import pandas as pd
from typing import Mapping, Tuple, Dict, List


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
    # Access by position it's the most efficient way found to access unique levels
    time_levels = data.index.levels[-1]  # type: ignore TODO Cannot access member
    if len(str(time_levels[0])) == 4:
        format = "%Y"
    elif "M" in time_levels[0]:
        format = "%YM%m"
    elif "Q" in time_levels[0]:
        raise NotImplementedError("Quarterly data not implemented yet.")
    else:
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
        dataset.index.intersection(complete_index), str(start) : str(end)
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
