import shutil
import zipfile
from pathlib import Path
from typing import Iterable

import pandas as pd

from .config import PipelineConfig

CANONICAL_COLUMNS = [
    "month", "town", "flat_type", "block", "street_name", "storey_range",
    "floor_area_sqm", "flat_model", "lease_commence_date", "remaining_lease",
    "resale_price",
]
# 4. Assume HDB lease is 99 years old, recompute remaining lease as of today. Remaining lease
# should be rounded down to Years and Months.
# some older source CSV files do not contain a remaining_lease column.
REQUIRED_COLUMNS = [c for c in CANONICAL_COLUMNS if c != "remaining_lease"]


def extract_zip(input_zip: Path, extraction_dir: Path) -> list[Path]:
    """Extract a source archive programmatically without modifying source files."""
    if not zipfile.is_zipfile(input_zip):
        raise ValueError(f"Input is not a valid ZIP archive: {input_zip}")
    with zipfile.ZipFile(input_zip) as archive:
        archive.extractall(extraction_dir)
    return sorted(extraction_dir.rglob("*.csv"))


def discover_csv_files(input_path: Path, extraction_dir: Path | None = None,) -> list[Path]:
    """Return CSV files from a ZIP archive, directory, or single CSV file."""

    if not input_path.exists():
        raise FileNotFoundError(f"Input path does not exist: {input_path}")

    if input_path.is_dir():
        csv_files = sorted(input_path.rglob("*.csv"))
        if not csv_files:
            raise FileNotFoundError(f"No CSV files found in directory: {input_path}")
        return csv_files

    if input_path.suffix.lower() == ".csv":
        return [input_path]

    if input_path.suffix.lower() == ".zip":
        if extraction_dir is None:
            raise ValueError("extraction_dir is required when the input is a ZIP file")

        return extract_zip(
            input_path,
            extraction_dir,
        )

    raise ValueError(
        "Unsupported input type. Expected a ZIP file, "
        "CSV directory, or single CSV file."
    )


def select_source_files(csv_files: Iterable[Path], start_month: str, end_month: str) -> list[Path]:
    """Select files containing at least one row in the requested period."""
    selected = []
    start = pd.Period(start_month, freq="M")  # single values: start → Period("2012-01", "M")
    end = pd.Period(end_month, freq="M")  # single values: end   → Period("2016-12", "M")
    for path in csv_files:
        months = pd.read_csv(path, usecols=["month"], dtype={"month": "string"})["month"]  # It returns a Pandas Series containing only the values from the month column.
        periods = pd.to_datetime(months, format="%Y-%m", errors="coerce").dt.to_period("M")  # A Series of Period values
        # 0    2012-01
        # 1    2014-06
        # 2        NaT
        # dtype: period[M]
        if ((periods >= start) & (periods <= end)).any():
            # a lower-bound check; AND an upper-bound check;
            # a check for whether any row matches.
            selected.append(path)
    return selected


def copy_raw_files(source_files: Iterable[Path], raw_dir: Path) -> None:
    raw_dir.mkdir(parents=True, exist_ok=True)
    for path in source_files:
        shutil.copy2(path, raw_dir / path.name)


def load_master(source_files: Iterable[Path], config: PipelineConfig) -> pd.DataFrame:
    """Union schemas by column name and filter records to the required month range."""
    frames = []
    for path in source_files:
        frame = pd.read_csv(path, dtype={"month": "string", "block": "string"}, low_memory=False)
        missing = set(REQUIRED_COLUMNS) - set(frame.columns)
        if missing:
            raise ValueError(f"{path.name} is missing required columns: {sorted(missing)}")
        for column in CANONICAL_COLUMNS:
            if column not in frame.columns:
                frame[column] = pd.NA
        frame = frame[CANONICAL_COLUMNS].copy()
        frame["source_file"] = path.name
        frame["source_row_number"] = range(2, len(frame) + 2)
        frames.append(frame)
    master = pd.concat(frames, ignore_index=True, sort=False)
    month_dt = pd.to_datetime(master["month"], format="%Y-%m", errors="coerce")  # YYYY-MM-DD 00:00:00
    in_scope = month_dt.between(pd.Timestamp(config.start_month + "-01"), pd.Timestamp(config.end_month + "-01"))
    return master.loc[in_scope | month_dt.isna()].reset_index(drop=True)
