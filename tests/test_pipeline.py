from datetime import date

import pandas as pd

from hdb_pipeline.config import PipelineConfig
from hdb_pipeline.data_quality import compute_remaining_lease, deduplicate
from hdb_pipeline.ingestion import CANONICAL_COLUMNS
from hdb_pipeline.transformation import build_resale_identifier, hash_identifiers


def sample_row(price: int) -> dict:
    row = {
        "month": "2016-01",
        "town": "TAMPINES",
        "flat_type": "4 ROOM",
        "block": "19",
        "street_name": "TAMPINES ST 21",
        "storey_range": "07 TO 09",
        "floor_area_sqm": 90.0,
        "flat_model": "Model A",
        "lease_commence_date": 1985,
        "remaining_lease": "68 years",
        "resale_price": price,
        "month_date": pd.Timestamp("2016-01-01"),
    }
    return row


def test_remaining_lease():
    years, months, _ = compute_remaining_lease(
        pd.Series([1985]),
        date(2026, 7, 17),
    )
    assert years.iloc[0] == 57
    assert months.iloc[0] == 6


def test_deduplicate_keeps_higher_price():
    data = pd.DataFrame([sample_row(400000), sample_row(450000)])
    kept, failed = deduplicate(data)
    assert kept.iloc[0]["resale_price"] == 450000
    assert failed.iloc[0]["resale_price"] == 400000


def test_identifier_and_hash_cardinality():
    data = pd.DataFrame([sample_row(450000)])
    transformed = build_resale_identifier(data)
    hashed = hash_identifiers(transformed)
    assert transformed.iloc[0]["resale_identifier"].startswith("S019")
    assert transformed["resale_identifier"].nunique() == hashed["hashed_resale_identifier"].nunique()
