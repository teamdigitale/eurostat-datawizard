import pandas as pd


def concat_keys_to_values(d: dict, sep=" | "):
    d = pd.Series(d)  # type: ignore
    d = d.index + " | " + d  # type: ignore
    return d.to_dict()  # type: ignore
