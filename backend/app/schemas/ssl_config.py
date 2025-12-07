"""SSL configuration schemas."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field

from app.models.ssl_config import SSLMode


class SSLConfigUpdate(BaseModel):
    """Schema for updating SSL configuration."""

    mode: SSLMode
    domain: str | None = Field(None, max_length=255)
    email: EmailStr | None = None
    auto_renew: bool = True


class SSLConfigResponse(BaseModel):
    """Schema for SSL configuration response."""

    id: UUID
    mode: SSLMode
    domain: str | None
    email: str | None
    certificate_valid: bool
    certificate_expiry: datetime | None
    last_renewal_attempt: datetime | None
    last_error: str | None
    auto_renew: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class SSLStatusResponse(BaseModel):
    """Schema for SSL status check response."""

    mode: SSLMode
    enabled: bool
    certificate_valid: bool
    certificate_expiry: datetime | None
    days_until_expiry: int | None
    domain: str | None
    last_error: str | None


class GenerateCertificateRequest(BaseModel):
    """Schema for certificate generation request."""

    mode: SSLMode
    domain: str | None = Field(None, max_length=255)
    email: EmailStr | None = None


class CertificateActionResponse(BaseModel):
    """Schema for certificate action response."""

    success: bool
    message: str
    certificate_valid: bool = False
    certificate_expiry: datetime | None = None
