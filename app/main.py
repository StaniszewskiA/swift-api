import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from sqlalchemy.future import select

from app.api.v1 import swift_code
from app.core.database import async_yield_db, AsyncBase, async_engine
from app.core.logger import logger
from app.models.models import SwiftCode
from app.services.swift_code_parser import parse_swift_file, save_swift_codes


async def create_tables():
    logger.info("Creating database tables...")
    try:
        async with async_engine.begin() as conn:
            await conn.run_sync(AsyncBase.metadata.create_all)
        logger.info("Tables created successfully")
    except Exception as e:
        logger.error(f"Failed to create tables: {e}")
        raise


async def seed_swift_codes():
    logger.info("Checking if SWIFT codes data exists...")
    file_path = os.path.join(os.path.dirname(__file__), "data", "Interns_2025_SWIFT_CODES.xlsx")

    async for db in async_yield_db():
        try:
            result = await db.execute(select(SwiftCode).limit(1))
            first_row = result.fetchone()

            if first_row is None:
                logger.info("No SWIFT codes found in database. Seeding from file...")
                parsed_input = parse_swift_file(file_path)
                if not parsed_input.empty:
                    logger.info(f"Successfully parsed SWIFT codes file with {len(parsed_input)} entries")
                    await save_swift_codes(parsed_input, db)
                    logger.info("Successfully saved SWIFT codes to database")
                else:
                    logger.warning(f"No data found in SWIFT codes file: {file_path}")
            else:
                logger.info("SWIFT codes already exist in database, skipping seed")
            return
        except Exception as e:
            logger.error(f"Error checking or seeding database: {e}")
            raise


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting the app")

    try:
        await create_tables()
        await seed_swift_codes()
        logger.info("Database initialization complete")
        yield
    except Exception as e:
        logger.error(f"Error during app startup: {e}")
        raise
    finally:
        logger.info("Shutting down the app")


app = FastAPI(
    title="Remitly SWIFT Code Service",
    description="API for querying bank SWIFT codes",
    version="1.0.0",
    lifespan=lifespan,
)

app.include_router(swift_code.router)


@app.get("/")
async def read_root():
    """Root endpoint that returns a welcome message."""
    return {"message": "Hello, World!"}
