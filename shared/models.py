"""Shared data models for Incident Copilot."""

from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class LogLevel(str, Enum):
    DEBUG = "debug"
    INFO = "info"
    WARN = "warn"
    ERROR = "error"


class LogEntry(BaseModel):
    """Log event from application or infrastructure."""

    id: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    level: LogLevel = LogLevel.INFO
    message: str
    source: str = "unknown"
    service: Optional[str] = None
    metadata: dict = Field(default_factory=dict)


class Metric(BaseModel):
    """Metric sample (Prometheus-style)."""

    name: str
    value: float
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    labels: dict = Field(default_factory=dict)
    service: Optional[str] = None


class Anomaly(BaseModel):
    """Detected anomaly."""

    id: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    metric_or_log: str
    expected_value: Optional[float] = None
    actual_value: Optional[float] = None
    deviation_score: float
    service: Optional[str] = None
    severity: str = "medium"


class Prediction(BaseModel):
    """Failure probability prediction."""

    id: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    service: Optional[str] = None
    failure_probability: float = Field(ge=0, le=100)
    time_to_failure_minutes: Optional[float] = None
    contributing_factors: list[str] = Field(default_factory=list)


class Incident(BaseModel):
    """Incident record for root cause and remediation."""

    id: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    anomaly_ids: list[str] = Field(default_factory=list)
    service: Optional[str] = None
    root_cause: Optional[str] = None
    evidence: list[str] = Field(default_factory=list)
    recommendations: list[str] = Field(default_factory=list)
    youcom_citations: list[dict] = Field(default_factory=list)
    status: str = "open"


class Remediation(BaseModel):
    """Remediation suggestion or script."""

    id: str
    incident_id: str
    action_type: str  # scaling, rollback, config
    description: str
    script_content: Optional[str] = None
    citations: list[dict] = Field(default_factory=list)
