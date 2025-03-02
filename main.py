from fastapi import FastAPI, HTTPException, UploadFile, File, Depends
import requests
from bs4 import BeautifulSoup
import logging
import csv
import io
import re
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy import Column, Integer, String, MetaData, Table
import os

app = FastAPI()

# Load PostgreSQL connection URL from environment variable (recommended for security)
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://postgres.kyjqfeyfsnvsyvugsncy:GIE92mhtkxdJw1SD@aws-0-us-west-1.pooler.supabase.com:5432/postgres")

# Enable connection pooling
engine = create_async_engine(
    DATABASE_URL,
    echo=True,
    pool_size=10,        # Number of connections in the pool
    max_overflow=20,     # Max extra connections if pool is full
    connect_args={"timeout": 120}
)

async_session = sessionmaker(
    engine, expire_on_commit=False, class_=AsyncSession
)

# Set up SQLAlchemy engine & session
engine = create_async_engine(DATABASE_URL, echo=True)
async_session = sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

metadata = MetaData()

# Define validation results table
validations = Table(
    "validations",
    metadata,
    Column("id", Integer, primary_key=True, index=True),
    Column("business_type", String),
    Column("brand_status", String),
    Column("campaign_id", String, nullable=True),
    Column("campaign_status", String, nullable=True),
)

# Function to save validation results to PostgreSQL
async def save_validation_result(business_type, brand_status, campaign_id=None, campaign_status=None):
    async with async_session() as session:
        async with session.begin():
            stmt = validations.insert().values(
                business_type=business_type, brand_status=brand_status,
                campaign_id=campaign_id, campaign_status=campaign_status
            )
            await session.execute(stmt)

# Function to initialize database schema
async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(metadata.create_all)

@app.on_event("startup")
async def startup():
    await init_db()

# API Endpoints (same logic, just using async save function now)
@app.get("/validate/business")
async def validate_business(business_type: str):
    result = check_prohibited_business(business_type)
    await save_validation_result(business_type, result["status"])
    return result

@app.post("/validate/brand")
async def validate_brand(brand_data: dict):
    result = validate_brand_info(brand_data)
    await save_validation_result(brand_data.get("Legal Business Name", "Unknown"), result["status"])
    return result

@app.get("/validate/campaign_status")
async def validate_campaign_status(campaign_id: str):
    result = check_campaign_status(campaign_id)
    await save_validation_result("N/A", "N/A", campaign_id, result.get("status", "Error"))
    return result

@app.post("/validate/bulk_csv")
async def validate_bulk_csv(file: UploadFile = File(...)):
    try:
        file_content = file.file.read()
        results = process_bulk_csv(file_content)
        return {"status": "Success", "results": results}
    except Exception as e:
        logging.error(f"Error processing CSV file: {str(e)}")
        raise HTTPException(status_code=500, detail="Error processing CSV file.")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
