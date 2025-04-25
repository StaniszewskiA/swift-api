import pandas as pd


def parse_swift_file(file_path: str) -> None:
    try:
        df = pd.read_excel(file_path)

        if "COUNTRY ISO2 CODE" in df.columns:
            df["COUNTRY ISO2 CODE"] = df["COUNTRY ISO2 CODE"].str.upper()
        if "COUNTRY NAME" in df.columns:
            df["COUNTRY NAME"] = df["COUNTRY NAME"].str.upper()

        df["Is Headquarters"] = df["SWIFT CODE"].str.endswith("XXX")
        df["Headquarters CODE"] = df.apply(
            lambda row: row["SWIFT CODE"] if row["Is Headquarters"] else row["SWIFT CODE"][:8] + "XXX", axis=1
        )

        """
            I think that time zone may be omitted - we can figure it out based on 
            TOWN NAME and COUNTRY NAME columns.
        """
        redundant_cols = ["TIME ZONE"]
        df = df.drop(columns=[col for col in redundant_cols if col in df.columns])

        return df
    except Exception as e:
        print(f"Error parsing file: {e}")
        return None
