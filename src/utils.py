import os
import numpy
import pandas as pd
from json import JSONEncoder
from datetime import datetime


def concat_keys_to_values(d: dict, sep=" | "):
    d = pd.Series(d)  # type: ignore
    d = d.index + sep + d  # type: ignore
    return d.to_dict()  # type: ignore


class PandasJSONEncoder(JSONEncoder):
    """Use this custom encoder to allow json-serialization of pandas objects.
    Example:
    ```
    json.dumps({
        'my_pandas_type': pandas_value,
        'my_numpy_type': numpy_value
    }, cls=PandasJSONEncoder)
    ```
    """

    # Credits: https://rymc.io/blog/2019/using-a-custom-jsonencoder-for-pandas-and-numpy/
    def default(self, obj_to_encode):
        """Pandas and Numpy have some specific types that we want to ensure
        are coerced to Python types, for JSON generation purposes. This attempts
        to do so where applicable.
        """
        # Pandas dataframes have a to_json() method
        if hasattr(obj_to_encode, "to_json"):
            return obj_to_encode.to_json()

        # Numpy objects report themselves oddly in error logs, but this generic
        # type mostly captures what we're after.
        if isinstance(obj_to_encode, numpy.generic):
            return numpy.asscalar(obj_to_encode)  # type: ignore

        if isinstance(obj_to_encode, numpy.ndarray):
            return obj_to_encode.to_list()  # type: ignore

        if isinstance(obj_to_encode, pd.Timestamp):
            return str(obj_to_encode)

        # If none of the above apply, fall back to the standard JSON encoding
        return super().default(obj_to_encode)


def get_last_file_update(filepath: str) -> datetime | None:
    if os.path.exists(filepath):
        return datetime.fromtimestamp(os.path.getmtime(filepath))
    return None
