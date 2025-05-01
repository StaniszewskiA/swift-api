import logging
import pandas as pd
from sqlalchemy.ext.asyncio import AsyncSession

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


async def save_swift_codes(df: pd.DataFrame, db: AsyncSession) -> None:
    """
    Saves the parsed SWIFT codes from a DataFrame to the database using pandas to_sql.

    Parameters
    ----------
        df : pd.DataFrame
            DataFrame containing the parsed SWIFT code data
        db : AsyncSession
            Database session

    Returns
    -------
    None
    """
    try:
        validate_swift_file_columns(df)

        df_to_save = df.rename(
            columns={
                "SWIFT CODE": "swift_code",
                "NAME": "name",
                "ADDRESS": "address",
                "COUNTRY ISO2 CODE": "country_iso2",
                "COUNTRY NAME": "country_name",
                "Is Headquarters": "is_headquarter",
                "Headquarters CODE": "headquarters_code",
            }
        )

        logger.info("Started saving SWIFT codes to the database")

        conn = await db.connection()
        await conn.run_sync(
            lambda sync_conn: df_to_save.to_sql(
                "swift_codes", sync_conn, if_exists="append", index=False, method="multi"
            )
        )

        logger.info(f"Successfully saved {len(df)} SWIFT codes to database")
    except Exception as ex:
        logger.error(f"Error saving data to the database: {ex}")
        raise
