import hashlib

import pandas as pd


def build_resale_identifier(df: pd.DataFrame) -> pd.DataFrame:
    """
    Build the required resale identifier for each HDB resale record.
    Identifier format:
        S + BBB + AA + MM + T
    Components:
        S:
            Fixed prefix.
        BBB:
            First three numeric digits extracted from the block value.
            The result is left-padded with zeros to three digits.
        AA:
            First two digits of the rounded average resale price for records
            in the same month, town and flat_type group.
        MM:
            Two-digit resale month.
        T:
            First character of the town name.
    Grouping rule:
        Average resale price is calculated using:
            month + town + flat_type
    Example:
        block = "12A"
        average resale price = 456789
        month = "2016-07"
        town = "TAMPINES"
        BBB = "012"
        AA = "45"
        MM = "07"
        T = "T"
        resale_identifier = "S0124507T"
    Args:
        df:
            Input DataFrame containing at least:
            block, month_date, town, flat_type and resale_price.
    Returns:
        A copy of the input DataFrame with a new column:
            resale_identifier
    """
    out = df.copy()

    average_price = out.groupby([out["month_date"].dt.to_period("M"), "town", "flat_type"])["resale_price"].transform("mean")

    block3 = out["block"].str.replace(r"\D", "", regex=True).str[:3].str.zfill(3)  # zfill means “zero fill
    average2 = average_price.round().astype("Int64").astype("string").str.zfill(2).str[:2]
    month2 = out["month_date"].dt.strftime("%m")
    town1 = out["town"].str[0]

    out["resale_identifier"] = "S" + block3 + average2 + month2 + town1
    return out


def hash_identifiers(df: pd.DataFrame) -> pd.DataFrame:
    """
    Create an irreversible SHA-256 hash for each resale identifier.
    Hashing process:
        1. Read the clear-text resale_identifier.
        2. Encode it as UTF-8 bytes.
        3. Apply the SHA-256 hashing algorithm.
        4. Store the hexadecimal hash value in a new column.
        5. Verify that hashing does not reduce the number of unique identifiers.
    Example:
        resale_identifier:
            S0124507T
        hashed_resale_identifier:
            A 64-character hexadecimal SHA-256 value, for example: 8f7c...e21a
    Uniqueness check:
        The number of unique clear-text identifiers must equal the number of unique hashed identifiers.
        If the counts differ, the function raises RuntimeError because uniqueness was not preserved.

    Args:
        df:
            Input DataFrame containing the resale_identifier column.
    Returns:
        A copy of the input DataFrame with a new column:
            hashed_resale_identifier
    Raises:
        RuntimeError:
            If the number of unique hashed identifiers differs from the
            number of unique original identifiers.
    """
    out = df.copy()
    out["hashed_resale_identifier"] = out["resale_identifier"].map(
        lambda value: hashlib.sha256(value.encode("utf-8")).hexdigest()
        #  hexdigest() converts the hash result into a readable hexadecimal string.
    )

    if out["resale_identifier"].nunique() != out["hashed_resale_identifier"].nunique():
        #  nunique() means “number of unique values.”
        raise RuntimeError("Hash uniqueness was not preserved")

    return out
