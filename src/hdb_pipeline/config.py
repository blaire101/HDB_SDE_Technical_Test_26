from dataclasses import dataclass
from datetime import date


@dataclass  # decorator -> auto __init__(), __repr__(), __eq__()
class PipelineConfig:
    """
    Configuration for the HDB resale ETL pipeline.

    Attributes:
        start_month:
            First resale month included in the pipeline, in YYYY-MM format.

        end_month:
            Last resale month included in the pipeline, in YYYY-MM format.

        lease_years:
            Standard HDB lease duration used to recompute the remaining lease.

        minimum_category_frequency:
            Minimum number of occurrences required for a category value to be
            treated as valid. Values occurring fewer times are considered
            potentially invalid or incorrectly encoded.

        anomaly_iqr_multiplier:
            Multiplier used in the IQR (Interquartile Range) rule for detecting potential price
            anomalies.

            Lower bound = Q1 - multiplier * IQR
            Upper bound = Q3 + multiplier * IQR

        as_of_date:
            Reference date used to calculate the remaining lease.
    """

    start_month: str = "2012-01"
    end_month: str = "2016-12"
    lease_years: int = 99

    minimum_category_frequency: int = 2
    anomaly_iqr_multiplier: float = 1.5

    as_of_date: date = date.today()
