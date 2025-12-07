"""SSL certificate management service."""

import asyncio
import ipaddress
import os
import shutil
from datetime import datetime, timedelta, timezone
from pathlib import Path

from cryptography import x509
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.x509.oid import NameOID

from app.models.ssl_config import SSLMode


class SSLManager:
    """Manages SSL certificates for the application."""

    CERT_DIR = Path("/app/certs")
    CERT_FILE = CERT_DIR / "fullchain.pem"
    KEY_FILE = CERT_DIR / "privkey.pem"
    NGINX_SIGNAL_FILE = Path("/app/certs/.reload_nginx")

    def __init__(self):
        """Initialize SSL manager."""
        self.CERT_DIR.mkdir(parents=True, exist_ok=True)

    def get_certificate_info(self) -> dict:
        """Get information about the current certificate."""
        if not self.CERT_FILE.exists():
            return {
                "valid": False,
                "expiry": None,
                "days_until_expiry": None,
                "subject": None,
            }

        try:
            with open(self.CERT_FILE, "rb") as f:
                cert_data = f.read()

            cert = x509.load_pem_x509_certificate(cert_data, default_backend())
            expiry = cert.not_valid_after_utc
            now = datetime.now(timezone.utc)
            days_until_expiry = (expiry - now).days

            # Get subject CN
            try:
                cn = cert.subject.get_attributes_for_oid(NameOID.COMMON_NAME)[0].value
            except (IndexError, AttributeError):
                cn = None

            return {
                "valid": days_until_expiry > 0,
                "expiry": expiry,
                "days_until_expiry": days_until_expiry,
                "subject": cn,
            }
        except Exception as e:
            return {
                "valid": False,
                "expiry": None,
                "days_until_expiry": None,
                "subject": None,
                "error": str(e),
            }

    def generate_self_signed(self, domain: str | None = None) -> tuple[bool, str]:
        """Generate a self-signed certificate."""
        try:
            # Use domain or default
            common_name = domain or "storagehub.local"

            # Generate private key
            key = rsa.generate_private_key(
                public_exponent=65537,
                key_size=2048,
                backend=default_backend(),
            )

            # Generate certificate
            subject = issuer = x509.Name([
                x509.NameAttribute(NameOID.COUNTRY_NAME, "US"),
                x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, "California"),
                x509.NameAttribute(NameOID.LOCALITY_NAME, "San Francisco"),
                x509.NameAttribute(NameOID.ORGANIZATION_NAME, "StorageHub"),
                x509.NameAttribute(NameOID.COMMON_NAME, common_name),
            ])

            # Build certificate with SAN
            san_list = [x509.DNSName(common_name)]
            if domain:
                san_list.append(x509.DNSName(f"*.{domain}"))
            # Add localhost for development
            san_list.extend([
                x509.DNSName("localhost"),
                x509.IPAddress(ipaddress.IPv4Address("127.0.0.1")),
            ])

            cert = (
                x509.CertificateBuilder()
                .subject_name(subject)
                .issuer_name(issuer)
                .public_key(key.public_key())
                .serial_number(x509.random_serial_number())
                .not_valid_before(datetime.now(timezone.utc))
                .not_valid_after(datetime.now(timezone.utc) + timedelta(days=365))
                .add_extension(
                    x509.SubjectAlternativeName(san_list),
                    critical=False,
                )
                .add_extension(
                    x509.BasicConstraints(ca=True, path_length=0),
                    critical=True,
                )
                .sign(key, hashes.SHA256(), default_backend())
            )

            # Write key file
            with open(self.KEY_FILE, "wb") as f:
                f.write(key.private_bytes(
                    encoding=serialization.Encoding.PEM,
                    format=serialization.PrivateFormat.TraditionalOpenSSL,
                    encryption_algorithm=serialization.NoEncryption(),
                ))
            os.chmod(self.KEY_FILE, 0o600)

            # Write cert file
            with open(self.CERT_FILE, "wb") as f:
                f.write(cert.public_bytes(serialization.Encoding.PEM))

            # Signal nginx to reload
            self._signal_nginx_reload()

            return True, f"Self-signed certificate generated for {common_name}"

        except Exception as e:
            return False, f"Failed to generate self-signed certificate: {str(e)}"

    async def request_letsencrypt(self, domain: str, email: str) -> tuple[bool, str]:
        """Request a Let's Encrypt certificate using certbot."""
        if not domain:
            return False, "Domain is required for Let's Encrypt"
        if not email:
            return False, "Email is required for Let's Encrypt"

        try:
            # Check if certbot is available
            certbot_path = "/usr/bin/certbot"
            if not os.path.exists(certbot_path):
                return False, "Certbot is not installed"

            # Run certbot in standalone mode
            # This requires port 80 to be available temporarily
            cmd = [
                certbot_path,
                "certonly",
                "--standalone",
                "--non-interactive",
                "--agree-tos",
                "--email", email,
                "-d", domain,
                "--cert-path", str(self.CERT_FILE),
                "--key-path", str(self.KEY_FILE),
                "--fullchain-path", str(self.CERT_FILE),
            ]

            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await process.communicate()

            if process.returncode == 0:
                # Copy certs from certbot location to our location
                certbot_live = Path(f"/etc/letsencrypt/live/{domain}")
                if certbot_live.exists():
                    shutil.copy(certbot_live / "fullchain.pem", self.CERT_FILE)
                    shutil.copy(certbot_live / "privkey.pem", self.KEY_FILE)
                    os.chmod(self.KEY_FILE, 0o600)

                self._signal_nginx_reload()
                return True, f"Let's Encrypt certificate obtained for {domain}"
            else:
                error_msg = stderr.decode() if stderr else stdout.decode()
                return False, f"Certbot failed: {error_msg}"

        except Exception as e:
            return False, f"Failed to request Let's Encrypt certificate: {str(e)}"

    async def renew_letsencrypt(self) -> tuple[bool, str]:
        """Renew Let's Encrypt certificate."""
        try:
            certbot_path = "/usr/bin/certbot"
            if not os.path.exists(certbot_path):
                return False, "Certbot is not installed"

            cmd = [certbot_path, "renew", "--non-interactive"]

            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await process.communicate()

            if process.returncode == 0:
                self._signal_nginx_reload()
                return True, "Certificate renewed successfully"
            else:
                error_msg = stderr.decode() if stderr else stdout.decode()
                return False, f"Renewal failed: {error_msg}"

        except Exception as e:
            return False, f"Failed to renew certificate: {str(e)}"

    def _signal_nginx_reload(self):
        """Signal nginx to reload configuration."""
        # Create a signal file that the nginx container watches
        self.NGINX_SIGNAL_FILE.touch()

    def remove_certificates(self) -> tuple[bool, str]:
        """Remove existing certificates."""
        try:
            if self.CERT_FILE.exists():
                self.CERT_FILE.unlink()
            if self.KEY_FILE.exists():
                self.KEY_FILE.unlink()
            self._signal_nginx_reload()
            return True, "Certificates removed"
        except Exception as e:
            return False, f"Failed to remove certificates: {str(e)}"

    def certificates_exist(self) -> bool:
        """Check if certificates exist."""
        return self.CERT_FILE.exists() and self.KEY_FILE.exists()
