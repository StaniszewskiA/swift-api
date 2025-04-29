import logging
import pandas as pd
from app.models.models import SwiftCode

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

    try:
        logger.info("Started saving SWIFT codes to the database.")
        swift_code_entries = [
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

        batch_size = 100
        for i in range(0, len(swift_code_entries), batch_size):
            logger.info(f"Inserting batch {i // batch_size + 1} of size {batch_size}.")
            db_session.bulk_save_objects(swift_code_entries[i : i + batch_size])

        db_session.commit()

    except Exception as ex:
        db_session.rollback()
        logger.error(f"Error saving data to the database: {ex}")
        raise

    finally:
        db_session.close()
        logger.info("Database session closed.")
