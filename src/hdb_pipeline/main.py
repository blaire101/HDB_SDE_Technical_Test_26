import argparse
import json
from datetime import date
from pathlib import Path

from .config import PipelineConfig
from .pipeline import run_pipeline


def main() -> None:
    """Parse command-line arguments and run the ETL pipeline."""
    parser = argparse.ArgumentParser(description="Run the HDB resale flat price ETL pipeline")
    parser.add_argument(
        "--input-path",
        type=Path,
        required=True,
        help="ZIP archive, directory containing CSV files, or a single CSV file",
    )
    parser.add_argument("--output-dir", type=Path, default=Path("output"))
    parser.add_argument("--as-of-date", type=date.fromisoformat, default=date.today())
    args = parser.parse_args()

    config = PipelineConfig(as_of_date=args.as_of_date)
    manifest = run_pipeline(args.input_path, args.output_dir, config)
    print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    main()
