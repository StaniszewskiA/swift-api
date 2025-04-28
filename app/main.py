from contextlib import asynccontextmanager
import logging
from app.models.models import SwiftCode
from app.routers import swift_codes
from fastapi import FastAPI

from .core.database import yield_db, Base, engine
from .services.swift_code_parser import parse_swift_file, save_swift_codes

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

app = FastAPI()
app.include_router(swift_codes.router)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting the app")
    Base.metadata.create_all(bind=engine)
    db = next(yield_db())

    # Seeding the database
    if not db.query(SwiftCode).first():
        logger.info("No data found in the database. Seeding the DB with provided .xlsx file.")
        parsed_input = parse_swift_file(r"app\data\Interns_2025_SWIFT_CODES.xlsx")
        save_swift_codes(parsed_input, db)
        logger.info("SWIFT codes parsed and saved to the database.")
    else:
        logger.info("SWIFT codes already exist in the database. Skipping parsing and saving.")

    logger.info("Database connection established")

    yield


app.lifecycle_events = lifespan


@app.get("/")
def read_root():
    return {"message": "Hello, World!"}
