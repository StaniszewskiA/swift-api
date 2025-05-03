"""
SWIFT code file parser.
"""

import pandas as pd

from app.core.logger import logger


def parse_swift_file(file_path: str) -> pd.DataFrame:
    """
    Parses a SWIFT .xlsx file and saves the cleaned data to a database table.
    """
    try:
        df = pd.read_excel(file_path, usecols=["SWIFT CODE", "NAME", "ADDRESS", "COUNTRY ISO2 CODE", "COUNTRY NAME"])

        for col in ("COUNTRY ISO2 CODE", "COUNTRY NAME"):
            if col in df.columns:
                df[col] = df[col].str.upper()

        if "SWIFT CODE" in df.columns:
            df["Is Headquarters"] = df["SWIFT CODE"].str.endswith("XXX")
            df["Headquarters CODE"] = df.apply(
                lambda row: row["SWIFT CODE"] if row["Is Headquarters"] else row["SWIFT CODE"][:8] + "XXX", axis=1
            )

        logger.info(f"Finished parsing file: {file_path}")
        return df
    except Exception as e:
        logger.error(f"Error parsing file {file_path}: {e}")
        return pd.DataFrame()
