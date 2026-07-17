from dataclasses import dataclass
from datetime import date


@dataclass
class PipelineConfig:
    """Runtime settings kept in one place to avoid scattered constants."""

    start_month: str = "2012-01"
    end_month: str = "2016-12"
    lease_years: int = 99
    anomaly_mad_threshold: float = 5.0
    minimum_peer_group_size: int = 20
    minimum_category_frequency: int = 5
    as_of_date: date = date.today()
