import sys

import pandas as pd
from app.models.models import SwiftCode


def parse_swift_file(file_path: str) -> None:
    """
    Parses a SWIFT .xlsx file and saves the cleaned data to a database table.

    Parameters
    ----------
        file_path : str
            Path to the .xlsx file

    Returns
    -------
    None
    """
    try:
        df = pd.read_excel(file_path)

        for col in ("COUNTRY ISO2 CODE", "COUNTRY NAME"):
            if col in df.columns:
                df[col] = df[col].str.upper()

        if "SWIFT CODE" in df.columns:
            df["Is Headquarters"] = df["SWIFT CODE"].str.endswith("XXX")
            df["Headquarters CODE"] = df.apply(
                lambda row: row["SWIFT CODE"] if row["Is Headquarters"] else row["SWIFT CODE"][:8] + "XXX", axis=1
            )

        # Time zone is redundant is we know the city.
        redundant_cols = ["TIME ZONE"]
        df = df.drop(columns=[col for col in redundant_cols if col in df.columns])

        return df
    except Exception as e:
        print(f"Error parsing file: {e}")
        return None


def save_swift_codes(df: pd.DataFrame, db_session) -> None:
    """
    Saves the parsed SWIFT codes from a DataFrame to the database.

    Parameters
    ----------
        df : pd.DataFrame
            DataFrame containing the parsed SWIFT code data

    Returns
    -------
    None
    """
    required_columns = [
        "SWIFT CODE",
        "BANK NAME",
        "COUNTRY ISO2 CODE",
        "COUNTRY NAME",
        "Is Headquarters",
        "Headquarters CODE",
    ]

    missing_columns = [col for col in required_columns if col not in df.columns]
    if missing_columns:
        raise KeyError(f"Missing required columns: {', '.join(missing_columns)}")

    try:
        swift_code_entries = []

        for _, row in df.iterrows():
            swift_code_entry = SwiftCode(
                swift_code=row["SWIFT CODE"],
                bank_name=row.get("BANK NAME", ""),
                country_iso2=row.get("COUNTRY ISO2 CODE", ""),
                country_name=row.get("COUNTRY NAME", ""),
                is_headquarter=row.get("Is Headquarters", False),
                headquarters_code=row.get("Headquarters CODE", ""),
            )
            swift_code_entries.append(swift_code_entry)

            if len(swift_code_entries) >= 100:
                db_session.add_all(swift_code_entries)
                swift_code_entries.clear()

        if swift_code_entries:
            db_session.add_all(swift_code_entries)

        db_session.commit()

    except Exception as ex:
        db_session.rollback()
        print(f"Error saving data to the database: {ex}", file=sys.stderr)
        raise

    finally:
        db_session.close()
