from datetime import date
from pathlib import Path

import pandas as pd

from .config import PipelineConfig
from .ingestion import CANONICAL_COLUMNS


def normalize_text(series: pd.Series) -> pd.Series:
    """
    Standardize text values in a Pandas Series.
    Example:
        Input:
            "  ANG   MO KIO  "
        Output:
            "ANG MO KIO"
    """
    return series.astype("string").str.strip().str.replace(r"\s+", " ", regex=True)


def profile_dataframe(df: pd.DataFrame, output_dir: Path) -> None:
    """
    Generate compact data-profiling reports for the master dataset.
    Column profile:
        For every column, calculate:
            - data type
            - total row count
            - null count
            - null percentage
            - distinct-value count
        The results are written to:
            column_profile.csv
    Category distributions:
        Count the frequency of each value, including null values, for:
            - town
            - flat_type
            - flat_model
            - storey_range
        Each distribution is written to a separate CSV file.
    Args:
        df:  Input DataFrame to profile.
        output_dir:  Directory where profiling CSV files will be written.
    Returns:  None.
    """
    output_dir.mkdir(parents=True, exist_ok=True)

    profile = pd.DataFrame({
        "column": df.columns,
        "dtype": [str(df[column].dtype) for column in df.columns],
        "row_count": [len(df) for _ in df.columns],
        "null_count": [int(df[column].isna().sum()) for column in df.columns],
        "null_pct": [round(float(df[column].isna().mean() * 100), 4) for column in df.columns],
        "distinct_count": [int(df[column].nunique(dropna=True)) for column in df.columns],
    })
    profile.to_csv(output_dir / "column_profile.csv", index=False)

    for column in ["town", "flat_type", "flat_model", "storey_range"]:
        distribution = df[column].value_counts(dropna=False).rename_axis(column).reset_index(name="row_count")
        distribution.to_csv(output_dir / f"{column}_distribution.csv", index=False)


def compute_remaining_lease(commence_year: pd.Series, as_of_date: date, lease_years: int = 99) -> tuple[pd.Series, pd.Series, pd.Series]:
    """
    Recalculate the remaining HDB lease as of a reference date.
    Assumption:
        The dataset provides only the lease commencement year.
        Therefore, every lease is assumed to start on 1 January of its commencement year.
    Calculation:
        expiry year = commencement year + lease duration
        remaining months = (expiry year - reference year) * 12 + (January - reference month)
        Negative remaining values are replaced with zero.
    Example:
        Commencement year: 1985
        Lease duration: 99 years
        Reference date: 2026-07-18
        Result: 57 years 05 months
    Args:
        commence_year:  Series containing lease commencement years.
        as_of_date:     Reference date used to calculate the remaining lease.
        lease_years:    Standard lease duration. Defaults to 99 years.
    Returns:
        A tuple containing:
            1. Remaining whole years.
            2. Remaining additional months.
            3. Readable labels such as "57 years 05 months".
    """
    start_year = pd.to_numeric(commence_year, errors="coerce")
    total_months = (
        (start_year + lease_years - as_of_date.year) * 12
        + (1 - as_of_date.month)
    ).clip(lower=0)

    years = (total_months // 12).astype("Int64")
    months = (total_months % 12).astype("Int64")
    labels = years.astype("string") + " years " + months.astype("string").str.zfill(2) + " months"
    return years, months, labels


def validate_and_standardize(master: pd.DataFrame, config: PipelineConfig) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
     Standardise fields and separate valid and invalid rows.
     Validation rules:
        month:
            - must follow YYYY-MM format
            - must fall within the configured source period
        town, flat_type and flat_model:
            - must not be null
            - must appear at least the configured minimum number
              of times in the master dataset
        storey_range:
            - must follow the NN TO NN format
            - lower floor must not be greater than upper floor
        block:
            - must contain at least one digit
        street_name:
            - must not be null or empty
        floor_area_sqm:
            - must be numeric and greater than zero
        lease_commence_date:
            - must be numeric
            - must be greater than zero
            - must not be later than the reference year
        resale_price:
            - must be numeric and greater than zero
    """
    df = master.copy()

    text_columns = [
        "month", "town", "flat_type", "block", "street_name",
        "storey_range", "flat_model", "remaining_lease",
    ]
    #  Text fields:
    for column in text_columns:
        df[column] = normalize_text(df[column])

    #  Uppercase fields:
    for column in ["town", "flat_type", "street_name", "storey_range"]:
        df[column] = df[column].str.upper()

    #  Numeric fields:
    df["month_date"] = pd.to_datetime(df["month"], format="%Y-%m", errors="coerce")
    for column in ["floor_area_sqm", "lease_commence_date", "resale_price"]:
        df[column] = pd.to_numeric(df[column], errors="coerce")

    failures = pd.Series("", index=df.index, dtype="string")


    def add_failure(mask: pd.Series, code: str) -> None:
        failures.loc[mask] = failures.loc[mask].apply(
            lambda value: code if value == "" else f"{value}|{code}"
        )

    start = pd.Timestamp(config.start_month + "-01")
    end = pd.Timestamp(config.end_month + "-01")
    add_failure(df["month_date"].isna(), "INVALID_MONTH_FORMAT")
    add_failure(df["month_date"].notna() & ~df["month_date"].between(start, end), "MONTH_OUT_OF_SCOPE")

    # The category domains are derived from master-data frequencies, as requested.
    for column, code in [("town", "INVALID_TOWN"), ("flat_type", "INVALID_FLAT_TYPE"), ("flat_model", "INVALID_FLAT_MODEL")]:
        normalized = normalize_text(df[column]).str.upper()
        counts = normalized.value_counts(dropna=True)
        valid_values = counts[counts >= config.minimum_category_frequency].index
        add_failure(normalized.isna() | ~normalized.isin(valid_values), code)

    # storey_range: 07 TO 09
    storey = df["storey_range"].fillna("")
    add_failure(~storey.str.match(r"^\d{2} TO \d{2}$"), "INVALID_STOREY_RANGE")
    low = pd.to_numeric(storey.str[:2], errors="coerce")
    high = pd.to_numeric(storey.str[-2:], errors="coerce")
    add_failure(low.notna() & high.notna() & (low > high), "INVALID_STOREY_ORDER")

    # Simple additional checks required for downstream calculations.
    # block: 147， floofailedr_area_sqm: 60
    add_failure(df["block"].isna() | ~df["block"].fillna("").str.contains(r"\d"), "INVALID_BLOCK")
    add_failure(df["street_name"].isna() | df["street_name"].eq(""), "MISSING_STREET_NAME")
    add_failure(df["floor_area_sqm"].isna() | (df["floor_area_sqm"] <= 0), "INVALID_FLOOR_AREA")
    add_failure(
        df["lease_commence_date"].isna() | (df["lease_commence_date"] <= 0) | (df["lease_commence_date"] > config.as_of_date.year),
        "INVALID_LEASE_COMMENCE_YEAR",
    )
    add_failure(df["resale_price"].isna() | (df["resale_price"] <= 0), "INVALID_RESALE_PRICE")

    # This line selects all rows that have at least one failure reason and copies them into failed.
    failed = df.loc[failures.ne("")].copy()
    failed["failure_reason"] = failures.loc[failures.ne("")]

    valid = df.loc[failures.eq("")].copy()
    years, months, labels = compute_remaining_lease(
        valid["lease_commence_date"],
        config.as_of_date,
        config.lease_years,
    )
    valid["remaining_lease_years"] = years.values
    valid["remaining_lease_months"] = months.values
    valid["remaining_lease_recomputed"] = labels.values  # Add a readable text version. 57 years 05 months
    valid["remaining_lease_as_of_date"] = config.as_of_date.isoformat()  # date to str

    return valid.reset_index(drop=True), failed.reset_index(drop=True)


def deduplicate(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Remove duplicate HDB resale records using the required composite key.
    Duplicate key: Every original source column in CANONICAL_COLUMNS except: resale_price
    Winner-selection rule:
        1. Sort records by all composite-key columns.
        2. Sort resale_price in descending order.
        3. Keep the first record for each composite key.
        4. Mark all later records as duplicates.
    Because resale_price is sorted in descending order, the record with the highest price is retained.
    Example:
        Input:
            Same composite key, resale_price = 500000
            Same composite key, resale_price = 520000
        Kept:
            resale_price = 520000
        Failed:
            resale_price = 500000
            failure_reason = DUPLICATE_LOWER_PRICE
    Args:
        df: Valid and standardized DataFrame.
    Returns:
        A tuple containing:
            1. Deduplicated records.
            2. Rejected duplicate records with failure_reason.
    """
    key_columns = [column for column in CANONICAL_COLUMNS if column != "resale_price"]

    ranked = df.sort_values(
        key_columns + ["resale_price"], ascending=[True] * len(key_columns) + [False], kind="mergesort",
    )
    duplicate_mask = ranked.duplicated(subset=key_columns, keep="first")

    failed = ranked.loc[duplicate_mask].copy()
    failed["failure_reason"] = "DUPLICATE_LOWER_PRICE"
    kept = ranked.loc[~duplicate_mask].copy().sort_index()

    return kept.reset_index(drop=True), failed.reset_index(drop=True)  # discard the old index instead of keeping it as a new column.


def flag_price_anomalies(df: pd.DataFrame, config: PipelineConfig) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Flag potential resale-price anomalies using a peer-group IQR rule.
    Purpose:
        Identify records whose price per square metre is unusually
        high or low compared with similar HDB resale records.
    Metric:
        price_per_sqm = resale_price / floor_area_sqm
    Peer group:
        Each record is compared only with records having the same:
            - year
            - town
            - flat_type
    Statistical method:
        Q1:  25th percentile of price_per_sqm.
        Q3:  75th percentile of price_per_sqm.
        IQR: Interquartile Range = Q3 - Q1.
    Thresholds:
        Lower bound:  Q1 - anomaly_iqr_multiplier (1.5) * IQR
        Upper bound:  Q3 + anomaly_iqr_multiplier (1.5) * IQR
    Output handling:
        All rows remain in the returned cleaned DataFrame, with:
            - is_anomalous_price
            - anomaly_reason
        Flagged rows are also copied into a separate review DataFrame.
    Example:
        Peer-group price_per_sqm values:
            4000, 4200, 4400, 4600, 4800, 9000
        If 9000 exceeds the calculated upper IQR bound:
            is_anomalous_price = True
            anomaly_reason = POTENTIAL_PRICE_ANOMALY_IQR
    Args:
        df:      Deduplicated DataFrame containing month_date, town, flat_type, resale_price and floor_area_sqm.
        config:  Pipeline configuration containing the IQR multiplier.
    Returns:
        A tuple containing:
            1. All records with anomaly fields added.
            2. Only the records flagged for anomaly review.
    """
    out = df.copy()
    out["price_per_sqm"] = out["resale_price"] / out["floor_area_sqm"]
    out["year"] = out["month_date"].dt.year
    group_columns = ["year", "town", "flat_type"]

    q1 = out.groupby(group_columns)["price_per_sqm"].transform("quantile", 0.25)
    q3 = out.groupby(group_columns)["price_per_sqm"].transform("quantile", 0.75)
    iqr = q3 - q1

    lower = q1 - config.anomaly_iqr_multiplier * iqr
    upper = q3 + config.anomaly_iqr_multiplier * iqr

    out["is_anomalous_price"] = ((out["price_per_sqm"] < lower) | (out["price_per_sqm"] > upper)).fillna(False)

    out["anomaly_reason"] = pd.Series(pd.NA, index=out.index, dtype="string")
    out.loc[out["is_anomalous_price"], "anomaly_reason"] = "POTENTIAL_PRICE_ANOMALY_IQR"
    #  For rows where is_anomalous_price is True, write the anomaly reason.

    review = out.loc[out["is_anomalous_price"]].copy()
    #  Select only the anomalous rows and copy them into review.

    # Flagged rows remain in Cleaned and are also written to Review.
    return out.reset_index(drop=True), review.reset_index(drop=True)
