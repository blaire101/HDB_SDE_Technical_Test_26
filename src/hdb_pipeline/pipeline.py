from pathlib import Path
from tempfile import TemporaryDirectory

from .config import PipelineConfig
from .data_quality import (
    deduplicate,
    flag_price_anomalies,
    profile_dataframe,
    validate_and_standardize,
)
from .ingestion import copy_raw_files, discover_csv_files, load_master, select_source_files
from .output import write_pipeline_outputs
from .transformation import build_resale_identifier, hash_identifiers


def run_pipeline(input_path: Path, output_dir: Path, config: PipelineConfig) -> dict:
    """Run the complete ETL pipeline."""
    output_dir.mkdir(parents=True, exist_ok=True)

    if input_path.suffix.lower() == ".zip":
        with TemporaryDirectory(prefix="hdb_pipeline_") as temp_dir:
            csv_files = discover_csv_files(input_path, Path(temp_dir))
            source_files = select_source_files(csv_files, config.start_month, config.end_month)
            master = prepare_master(source_files, output_dir, config)
    else:
        csv_files = discover_csv_files(input_path)
        source_files = select_source_files(csv_files, config.start_month, config.end_month)
        master = prepare_master(source_files, output_dir, config)

    profile_dataframe(master, output_dir / "profiling")

    # Validate and standardize:
    #   month, town, flat_type, flat_model, storey_range,
    #   block, street_name, floor_area_sqm,
    #   lease_commence_date and resale_price.
    valid, validation_failed = validate_and_standardize(master, config)

    # Remove duplicate records using all original columns except resale_price,
    #   and keep the record with the highest resale_price.
    deduplicated, duplicate_failed = deduplicate(valid)

    # Price anomaly detection:
    cleaned, anomaly_review = flag_price_anomalies(deduplicated, config)

    transformed = build_resale_identifier(cleaned)
    hashed = hash_identifiers(transformed)

    return write_pipeline_outputs(
        output_dir,
        config,
        source_files,
        master,
        validation_failed,
        duplicate_failed,
        cleaned,
        anomaly_review,
        transformed,
        hashed,
    )


def prepare_master(source_files: list[Path], output_dir: Path, config: PipelineConfig):
    if not source_files:
        raise ValueError("No source files contain rows in the configured month range")

    copy_raw_files(source_files, output_dir / "raw")
    return load_master(source_files, config)
