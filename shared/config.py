"""Shared configuration."""

import os
from functools import lru_cache


@lru_cache
def get_config():
    """Load config from environment."""
    return {
        "database_url": os.getenv("DATABASE_URL", "sqlite:///./incident_copilot.db"),
        "youcom_api_key": os.getenv("YOUCOM_API_KEY", ""),
        "sanity_project_id": os.getenv("SANITY_PROJECT_ID", ""),
        "sanity_dataset": os.getenv("SANITY_DATASET", "production"),
        "sanity_token": os.getenv("SANITY_TOKEN", ""),
        "ingestion_url": os.getenv("INGESTION_URL", "http://localhost:8001"),
        "anomaly_url": os.getenv("ANOMALY_URL", "http://localhost:8002"),
        "prediction_url": os.getenv("PREDICTION_URL", "http://localhost:8003"),
        "recommendation_url": os.getenv("RECOMMENDATION_URL", "http://localhost:8004"),
        "knowledge_url": os.getenv("KNOWLEDGE_URL", "http://localhost:8005"),
    }
