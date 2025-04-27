import pandas as pd
from app.models.models import SwiftCode
from app.core.database import SessionLocal


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


def save_swift_codes(df: pd.DataFrame) -> None:
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
    try:
        db = SessionLocal()

        for _, row in df.iterrows():
            swift_code_entry = SwiftCode(
                swift_code=row["SWIFT CODE"],
                bank_name=row.get("BANK NAME", ""),
                country_iso2=row.get("COUNTRY ISO2 CODE", ""),
                country_name=row.get("COUNTRY NAME", ""),
                is_headquarter=row.get("Is Headquarters", False),
                headquarters_code=row.get("Headquarters CODE", ""),
            )
            db.add(swift_code_entry)

        db.commit()

    except Exception as e:
        print(f"Error saving data to the database: {e}")
        db.rollback()

    finally:
        db.close()
