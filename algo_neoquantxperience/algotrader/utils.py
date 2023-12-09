from collections import defaultdict
from typing import Any, Dict, List, TypeVar, Union

import numpy as np
import pandas as pd

T = TypeVar("T")


def to_list(arg: Union[T, List[T]]) -> List[T]:
    if not isinstance(arg, list):
        return [arg]
    return arg


def to_pivot(df: pd.DataFrame) -> pd.DataFrame:
    df_pivoted = df.pivot(index="time_idx_eq_end", columns="id")
    df_pivoted.columns = df_pivoted.columns.set_names(["feature", "id"])
    return df_pivoted


def to_flatten(df: pd.DataFrame) -> pd.DataFrame:
    segments = df.columns.get_level_values("id").unique()
    dtypes = df.dtypes
    category_columns = dtypes[dtypes == "category"].index.get_level_values("feature").unique()
    columns = df.columns.get_level_values("feature").unique()

    # flatten dataframe
    df_dict: Dict[str, Any] = {}
    df_dict["id"] = np.repeat(segments, len(df.index))
    df_dict["time_idx_eq_end"] = np.tile(df.index, len(segments))
    for column in columns:
        df_cur = df.loc[:, pd.IndexSlice[column, :]]
        if column in category_columns:
            df_dict[column] = pd.api.types.union_categoricals([df_cur[col] for col in df_cur.columns])
        else:
            stacked = df_cur.values.T.ravel()
            df_dict[column] = pd.Series(stacked, dtype=df_cur.dtypes[0])
    df_flat = pd.DataFrame(df_dict)

    return df_flat


def rename_columns(df: pd.DataFrame) -> pd.DataFrame:
    name_counts: Dict[str, int] = defaultdict(int)
    new_col_names = []

    for name in df.columns:
        new_count = name_counts[name] + 1
        new_col_names.append("{}{}".format(name, new_count))
        name_counts[name] = new_count

    df.columns = new_col_names
    return df


def onehot_encode(array: np.ndarray, counts: List[int]) -> np.ndarray:
    """
    Function which individually one-hot encodes every feature column in an n-dimensional array.
    """
    features_storage = []
    for i in range(array.shape[-1]):
        array_slice = array[..., i]
        features_storage.append(np.eye(counts[i])[array_slice])
    result = np.concatenate(features_storage, axis=-1)
    return result


def get_last_time_index(df: pd.DataFrame) -> int:
    return df[["id", "time_idx_eq_end"]].groupby("id").max()["time_idx_eq_end"].unique().item()


def is_subarray_no_repeatition(array: np.ndarray, sub_array: np.ndarray) -> bool:
    try:
        i = np.where(array == sub_array[0])[0][0]
    except IndexError:
        # either sub_array is empty, or sub_array[0] not in array
        return sub_array.size == 0
    array = array[i : i + sub_array.size]
    if array.size < sub_array.size:
        return False
    return (array == sub_array).all()
