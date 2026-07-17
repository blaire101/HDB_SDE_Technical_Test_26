from dataclasses import dataclass
from datetime import date


@dataclass  # decorator -> auto __init__(), __repr__(), __eq__()
class PipelineConfig:
    start_month: str = "2012-01"
    end_month: str = "2016-12"
    lease_years: int = 99

    # Flag a price when its robust Z-score is greater than 5.
    # The value 5.0 means that only prices more than five robust deviation units
    # away from the peer-group median are flagged for review.
    anomaly_mad_threshold: float = 5.0

    # a peer group has at least 20 records.
    minimum_peer_group_size: int = 20

    # Treat a category appearing fewer than 5 times.
    minimum_category_frequency: int = 5
    
    # Reference date used to calculate the remaining lease.
    as_of_date: date = date.today()