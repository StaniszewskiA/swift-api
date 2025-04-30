import logging
import pandas as pd
from app.crud.swift_code_crud import save_swift_codes_to_db
from app.models.models import SwiftCode
from sqlalchemy.orm import Session

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


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
        # Time zone is redundant is we know the city.
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


def validate_swift_file_columns(df: pd.DataFrame) -> None:
    """
    Validates that the required columns are present in the DataFrame.

    Parameters
    ----------
    df : pd.DataFrame
        DataFrame to validate

    Returns
    -------
    None
    """
    required_columns = [
        "SWIFT CODE",
        "NAME",
        "ADDRESS",
        "COUNTRY ISO2 CODE",
        "COUNTRY NAME",
        "Is Headquarters",
        "Headquarters CODE",
    ]

    missing_columns = [col for col in required_columns if col not in df.columns]
    if missing_columns:
        logger.error(f"Missing required columns: {', '.join(missing_columns)}")
        raise KeyError(f"Missing required columns: {', '.join(missing_columns)}")


def create_swift_code_entries(df: pd.DataFrame) -> list[SwiftCode]:
    """
    Creates a list of SwiftCode objects from the DataFrame.

    Parameters
    ----------
    df : pd.DataFrame
        DataFrame containing the parsed SWIFT code data

    Returns
    -------
    list
        List of SwiftCode objects
    """
    return [
        SwiftCode(
            swift_code=row["SWIFT CODE"],
            name=row.get("NAME", ""),
            address=row.get("ADDRESS", ""),
            country_iso2=row.get("COUNTRY ISO2 CODE", ""),
            country_name=row.get("COUNTRY NAME", ""),
            is_headquarter=row.get("Is Headquarters", False),
            headquarters_code=row.get("Headquarters CODE", ""),
        )
        for _, row in df.iterrows()
    ]


def save_swift_codes(df: pd.DataFrame, db: Session) -> None:
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
        validate_swift_file_columns(df)
        swift_code_entries = create_swift_code_entries(df)
        logger.info("Started saving SWIFT codes to the database")
        save_swift_codes_to_db(db, swift_code_entries)
        logger.info("Finished saving SWIFT codes to the database")
    except Exception as ex:
        logger.error(f"Error saving data to the database: {ex}")
        raise
