from contextlib import asynccontextmanager

from app.crud.swift_code_crud import create_tables, seed_swift_codes
from fastapi import FastAPI

from app.api.v1 import swift_code
from app.core.logger import logger


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
    title="SWIFT Code Service",
    description="API for querying bank SWIFT codes",
    version="1.0.0",
    lifespan=lifespan,
)

app.include_router(swift_code.router)


@app.get("/")
async def read_root():
    return {"message": "Hello, World!"}
