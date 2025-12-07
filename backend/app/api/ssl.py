"""SSL configuration API routes."""

from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select

from app.api.deps import CurrentUser, DbSession
from app.models.ssl_config import SSLConfig, SSLMode
from app.models.user import UserRole
from app.schemas.ssl_config import (
    CertificateActionResponse,
    GenerateCertificateRequest,
    SSLConfigResponse,
    SSLConfigUpdate,
    SSLStatusResponse,
)
from app.services.ssl_manager import SSLManager

router = APIRouter()


def require_admin(user: CurrentUser):
    """Require admin role for SSL operations."""
    if user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )


async def get_or_create_config(db: DbSession) -> SSLConfig:
    """Get the SSL config, creating default if needed."""
    result = await db.execute(select(SSLConfig).limit(1))
    config = result.scalar_one_or_none()

    if not config:
        config = SSLConfig()
        db.add(config)
        await db.flush()
        await db.refresh(config)

    return config


@router.get("", response_model=SSLConfigResponse)
async def get_ssl_config(
    db: DbSession,
    current_user: CurrentUser,
) -> SSLConfigResponse:
    """Get current SSL configuration."""
    require_admin(current_user)
    config = await get_or_create_config(db)
    return SSLConfigResponse.model_validate(config)


@router.get("/status", response_model=SSLStatusResponse)
async def get_ssl_status(
    db: DbSession,
    current_user: CurrentUser,
) -> SSLStatusResponse:
    """Get SSL status including certificate validity."""
    require_admin(current_user)

    config = await get_or_create_config(db)
    ssl_manager = SSLManager()
    cert_info = ssl_manager.get_certificate_info()

    return SSLStatusResponse(
        mode=config.mode,
        enabled=config.mode != SSLMode.DISABLED,
        certificate_valid=cert_info.get("valid", False),
        certificate_expiry=cert_info.get("expiry"),
        days_until_expiry=cert_info.get("days_until_expiry"),
        domain=config.domain,
        last_error=config.last_error,
    )


@router.patch("", response_model=SSLConfigResponse)
async def update_ssl_config(
    config_data: SSLConfigUpdate,
    db: DbSession,
    current_user: CurrentUser,
) -> SSLConfigResponse:
    """Update SSL configuration."""
    require_admin(current_user)

    config = await get_or_create_config(db)

    # Update fields
    config.mode = config_data.mode
    config.domain = config_data.domain
    config.email = config_data.email
    config.auto_renew = config_data.auto_renew

    await db.flush()
    await db.refresh(config)

    return SSLConfigResponse.model_validate(config)


@router.post("/generate", response_model=CertificateActionResponse)
async def generate_certificate(
    request: GenerateCertificateRequest,
    db: DbSession,
    current_user: CurrentUser,
) -> CertificateActionResponse:
    """Generate or request a new certificate."""
    require_admin(current_user)

    config = await get_or_create_config(db)
    ssl_manager = SSLManager()

    if request.mode == SSLMode.DISABLED:
        # Remove certificates and disable SSL
        success, message = ssl_manager.remove_certificates()
        config.mode = SSLMode.DISABLED
        config.certificate_valid = False
        config.certificate_expiry = None
        config.last_error = None if success else message

    elif request.mode == SSLMode.SELF_SIGNED:
        # Generate self-signed certificate
        success, message = ssl_manager.generate_self_signed(request.domain)
        if success:
            cert_info = ssl_manager.get_certificate_info()
            config.mode = SSLMode.SELF_SIGNED
            config.domain = request.domain
            config.certificate_valid = cert_info.get("valid", False)
            config.certificate_expiry = cert_info.get("expiry")
            config.last_error = None
        else:
            config.last_error = message

    elif request.mode == SSLMode.LETSENCRYPT:
        # Request Let's Encrypt certificate
        if not request.domain:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Domain is required for Let's Encrypt",
            )
        if not request.email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email is required for Let's Encrypt",
            )

        config.last_renewal_attempt = datetime.now(timezone.utc)
        success, message = await ssl_manager.request_letsencrypt(request.domain, request.email)

        if success:
            cert_info = ssl_manager.get_certificate_info()
            config.mode = SSLMode.LETSENCRYPT
            config.domain = request.domain
            config.email = request.email
            config.certificate_valid = cert_info.get("valid", False)
            config.certificate_expiry = cert_info.get("expiry")
            config.last_error = None
        else:
            config.last_error = message

    await db.flush()
    await db.refresh(config)

    cert_info = ssl_manager.get_certificate_info()
    return CertificateActionResponse(
        success=config.last_error is None,
        message=message if 'message' in dir() else "Configuration updated",
        certificate_valid=cert_info.get("valid", False),
        certificate_expiry=cert_info.get("expiry"),
    )


@router.post("/renew", response_model=CertificateActionResponse)
async def renew_certificate(
    db: DbSession,
    current_user: CurrentUser,
) -> CertificateActionResponse:
    """Renew Let's Encrypt certificate."""
    require_admin(current_user)

    config = await get_or_create_config(db)

    if config.mode != SSLMode.LETSENCRYPT:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Renewal is only available for Let's Encrypt certificates",
        )

    ssl_manager = SSLManager()
    config.last_renewal_attempt = datetime.now(timezone.utc)

    success, message = await ssl_manager.renew_letsencrypt()

    if success:
        cert_info = ssl_manager.get_certificate_info()
        config.certificate_valid = cert_info.get("valid", False)
        config.certificate_expiry = cert_info.get("expiry")
        config.last_error = None
    else:
        config.last_error = message

    await db.flush()
    await db.refresh(config)

    cert_info = ssl_manager.get_certificate_info()
    return CertificateActionResponse(
        success=success,
        message=message,
        certificate_valid=cert_info.get("valid", False),
        certificate_expiry=cert_info.get("expiry"),
    )


@router.post("/test", response_model=CertificateActionResponse)
async def test_certificate(
    db: DbSession,
    current_user: CurrentUser,
) -> CertificateActionResponse:
    """Test if current certificate is valid."""
    require_admin(current_user)

    ssl_manager = SSLManager()
    cert_info = ssl_manager.get_certificate_info()

    if not ssl_manager.certificates_exist():
        return CertificateActionResponse(
            success=False,
            message="No certificates found",
            certificate_valid=False,
            certificate_expiry=None,
        )

    if cert_info.get("valid"):
        return CertificateActionResponse(
            success=True,
            message=f"Certificate is valid for {cert_info.get('days_until_expiry')} more days",
            certificate_valid=True,
            certificate_expiry=cert_info.get("expiry"),
        )
    else:
        return CertificateActionResponse(
            success=False,
            message=cert_info.get("error", "Certificate is invalid or expired"),
            certificate_valid=False,
            certificate_expiry=cert_info.get("expiry"),
        )
