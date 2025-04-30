from contextlib import asynccontextmanager
from app.models.models import SwiftCode
from app.api.v1 import swift_code
from fastapi import FastAPI

from .core.logger import logger
from .core.database import async_yield_db, AsyncBase, async_engine
from .services.swift_code_parser import parse_swift_file, save_swift_codes

from sqlalchemy.future import select

app = FastAPI()
app.include_router(swift_code.router)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting the app")
    async with async_engine.begin() as conn:
        await conn.run_sync(AsyncBase.metadata.create_all)

    async for db in async_yield_db():
        # Seeding the database
        result = await db.execute(select(SwiftCode).limit(1))
        if not result.scalars().first():
            logger.info("No data found in the database. Seeding the DB with provided .xlsx file.")
            parsed_input = parse_swift_file("/app/app/data/Interns_2025_SWIFT_CODES.xlsx")
            await save_swift_codes(parsed_input, db)
            logger.info("SWIFT codes parsed and saved to the database.")
        else:
            logger.info("SWIFT codes already exist in the database. Skipping parsing and saving.")

        logger.info("Database connection established")
        yield


app = FastAPI(lifespan=lifespan)
app.include_router(swift_code.router)


@app.get("/")
async def read_root():
    return {"message": "Hello, World!"}
