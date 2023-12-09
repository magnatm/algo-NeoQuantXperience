import warnings
from dataclasses import dataclass
from typing import Dict, List, Optional

import numpy as np
import pandas as pd

from .utils import to_flatten, to_pivot


@dataclass
class MakeFutureDateArgs:
    date_column_name: str
    freq: str


@dataclass
class MakeFutureKnownDataArgs:
    df: pd.DataFrame
    common_column_names: List[str]


def make_future_timesteps(
    df: pd.DataFrame,
    add_timesteps: int,
    forward_fill_column_names: Optional[List[str]] = None,
    date_args: Optional[MakeFutureDateArgs] = None,
    known_data_args: Optional[MakeFutureKnownDataArgs] = None,
) -> pd.DataFrame:
    df_original = df
    column_order = df.columns
    df = df.copy(deep=True)
    df["__keep__"] = "__keep__"

    df_pivoted = to_pivot(df)
    all_ids = df_pivoted.columns.get_level_values("id").unique()
    all_features = df_pivoted.columns.get_level_values("feature").unique()

    last_timestep = df_pivoted.index[-1]
    last_and_future_timesteps = np.arange(last_timestep, last_timestep + add_timesteps + 1)
    future_timesteps = last_and_future_timesteps[1:]
    past_and_future_timesteps = df_pivoted.index.append(pd.Index(future_timesteps))
    df_pivoted = df_pivoted.reindex(past_and_future_timesteps)
    df_pivoted.loc[last_and_future_timesteps, (["__keep__"], all_ids)] = df_pivoted.loc[
        last_and_future_timesteps, (["__keep__"], all_ids)
    ].ffill()

    if date_args:
        if date_args.date_column_name not in all_features:
            raise ValueError(f"{date_args.date_column_name} not found in 'df'.")
        last_date = df[date_args.date_column_name].max()
        future_dates = pd.date_range(start=last_date, periods=add_timesteps + 1, freq=date_args.freq)[1:]
        df_pivoted.loc[future_timesteps, (date_args.date_column_name, all_ids)] = df_pivoted.loc[
            future_timesteps, (date_args.date_column_name, all_ids)
        ].apply(lambda x: future_dates)

    if forward_fill_column_names:
        if not all(col in all_features for col in forward_fill_column_names):
            raise ValueError(f"Some of {forward_fill_column_names} not found in 'df'.")
        df_pivoted.loc[last_and_future_timesteps, (forward_fill_column_names, all_ids)] = df_pivoted.loc[
            last_and_future_timesteps, (forward_fill_column_names, all_ids)
        ].ffill()

    df_flattened_future = to_flatten(df_pivoted)
    df_flattened_future = df_flattened_future.dropna(subset=["__keep__"])
    df_flattened_future = df_flattened_future.drop(columns=["__keep__"])
    df_flattened_future = df_flattened_future.reset_index(drop=True)
    all_features = df_flattened_future.columns

    if known_data_args:
        if not all(col in all_features for col in known_data_args.common_column_names):
            raise ValueError(f"Some of {known_data_args.common_column_names} not found in 'df'.")
        category_columns_df_flattened = df_flattened_future.dtypes[df_flattened_future.dtypes == "category"].index
        category_columns_known_data_df = known_data_args.df.dtypes[known_data_args.df.dtypes == "category"].index
        category_columns = list(set(category_columns_df_flattened) & set(category_columns_known_data_df))

        df_flattened_future = df_flattened_future.set_index(known_data_args.common_column_names)
        df_flattened_future.update(known_data_args.df.set_index(known_data_args.common_column_names))
        df_flattened_future = df_flattened_future.reset_index()

        if category_columns:
            for category_column in category_columns:
                original_categories = df_original[category_column].cat.categories
                df_flattened_future[category_column] = df_flattened_future[category_column].astype("category")
                df_flattened_future[category_column] = df_flattened_future[category_column].cat.set_categories(
                    original_categories
                )

    df_flattened_future = df_flattened_future[column_order]

    if not df_original.equals(
        df_flattened_future[lambda x: x["time_idx_eq_end"] <= last_timestep].reset_index(drop=True)
    ):
        warnings.warn(
            "History of returned dataframe is not equal to the dataframe, that passed to the function. "
            "Please check 'known_data_args'."
        )

    return df_flattened_future
