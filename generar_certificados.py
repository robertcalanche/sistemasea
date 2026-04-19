#!/usr/bin/env python3
"""
Generador de certificados SSL locales confiables para SEA.

Este script crea una autoridad certificadora (CA) local y un certificado
firmado por ella para localhost y la IP especificada.

Uso:
    python generar_certificados.py [IP]

Ejemplo:
    python generar_certificados.py 192.168.200.14
"""

import sys
import socket
import ipaddress
from pathlib import Path
from datetime import datetime, timedelta

try:
    from cryptography import x509
    from cryptography.x509.oid import NameOID, ExtensionOID
    from cryptography.hazmat.primitives import hashes, serialization
    from cryptography.hazmat.primitives.asymmetric import rsa
    from cryptography.hazmat.backends import default_backend
except ImportError as e:
    print(f"Error: Se requiere 'cryptography'. Instala con: pip install cryptography")
    sys.exit(1)


def get_local_ip():
    """Obtiene la IP local de la maquina."""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"


def generate_private_key():
    """Genera una clave privada RSA."""
    return rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
        backend=default_backend(),
    )


def generate_ca_cert(cert_dir):
    """Genera una autoridad certificadora local."""
    ca_key_path = cert_dir / "ca_key.pem"
    ca_cert_path = cert_dir / "ca.pem"

    if ca_cert_path.exists() and ca_key_path.exists():
        print(f"[OK] CA local ya existe: {ca_cert_path}")
        return ca_cert_path, ca_key_path

    print("[*] Generando CA (Autoridad Certificadora) local...")

    ca_key = generate_private_key()
    ca_subject = x509.Name(
        [
            x509.NameAttribute(NameOID.COUNTRY_NAME, "CO"),
            x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, "Test"),
            x509.NameAttribute(NameOID.ORGANIZATION_NAME, "SEA Test CA"),
            x509.NameAttribute(NameOID.COMMON_NAME, "SEA Local CA"),
        ]
    )

    ca_cert = (
        x509.CertificateBuilder()
        .subject_name(ca_subject)
        .issuer_name(ca_subject)
        .public_key(ca_key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(datetime.utcnow())
        .not_valid_after(datetime.utcnow() + timedelta(days=3650))
        .add_extension(
            x509.BasicConstraints(ca=True, path_length=None),
            critical=True,
        )
        .sign(ca_key, hashes.SHA256(), default_backend())
    )

    ca_cert_path.write_bytes(ca_cert.public_bytes(serialization.Encoding.PEM))
    ca_key_path.write_bytes(
        ca_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.TraditionalOpenSSL,
            encryption_algorithm=serialization.NoEncryption(),
        )
    )

    print(f"[OK] CA creada: {ca_cert_path}")
    print(
        f"     Guardar este archivo en dispositivos moviles para confiar en el servidor."
    )
    return ca_cert_path, ca_key_path


def generate_server_cert(cert_dir, ca_cert_path, ca_key_path, ip_address):
    """Genera un certificado para el servidor."""
    server_key_path = cert_dir / "server_key.pem"
    server_cert_path = cert_dir / "server.pem"

    if server_cert_path.exists() and server_key_path.exists():
        print(f"[OK] Certificado del servidor ya existe: {server_cert_path}")
        return server_cert_path, server_key_path

    print(
        f"[*] Generando certificado del servidor para: localhost, 127.0.0.1, {ip_address}"
    )

    server_key = generate_private_key()

    ca_cert_data = x509.load_pem_x509_certificate(
        ca_cert_path.read_bytes(), default_backend()
    )
    ca_key_data = serialization.load_pem_private_key(
        ca_key_path.read_bytes(), password=None, backend=default_backend()
    )

    server_subject = x509.Name(
        [
            x509.NameAttribute(NameOID.COUNTRY_NAME, "CO"),
            x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, "Test"),
            x509.NameAttribute(NameOID.ORGANIZATION_NAME, "SEA"),
            x509.NameAttribute(NameOID.COMMON_NAME, f"SEA Server ({ip_address})"),
        ]
    )

    san_list = [
        x509.DNSName("localhost"),
        x509.DNSName("127.0.0.1"),
        x509.IPAddress(ipaddress.ip_address(ip_address)),
    ]

    try:
        san_list.append(x509.IPAddress(ipaddress.ip_address(get_local_ip())))
    except Exception:
        pass

    server_cert = (
        x509.CertificateBuilder()
        .subject_name(server_subject)
        .issuer_name(ca_cert_data.subject)
        .public_key(server_key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(datetime.utcnow())
        .not_valid_after(datetime.utcnow() + timedelta(days=365))
        .add_extension(
            x509.SubjectAlternativeName(san_list),
            critical=False,
        )
        .sign(ca_key_data, hashes.SHA256(), default_backend())
    )

    server_cert_path.write_bytes(server_cert.public_bytes(serialization.Encoding.PEM))
    server_key_path.write_bytes(
        server_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.TraditionalOpenSSL,
            encryption_algorithm=serialization.NoEncryption(),
        )
    )

    print(f"[OK] Certificado generado: {server_cert_path}")
    return server_cert_path, server_key_path


def setup_certificates(ip_address=None):
    """Configura todos los certificados necesarios."""
    if ip_address is None:
        ip_address = get_local_ip()

    cert_dir = Path(__file__).parent / "certs"
    cert_dir.mkdir(exist_ok=True)

    print("=" * 60)
    print("  SEA -- Generador de Certificados SSL Locales")
    print("=" * 60)
    print(f"  Directorio: {cert_dir}")
    print(f"  IP del servidor: {ip_address}")
    print("=" * 60)

    ca_cert_path, ca_key_path = generate_ca_cert(cert_dir)
    server_cert_path, server_key_path = generate_server_cert(
        cert_dir, ca_cert_path, ca_key_path, ip_address
    )

    print("=" * 60)
    print("  [OK] Certificados listos para usar")
    print("=" * 60)
    print(f"  Certificado del servidor (cert): {server_cert_path}")
    print(f"  Clave privada del servidor (key): {server_key_path}")
    print()
    print("  Para dispositivos moviles:")
    print(f"  1. Copiar CA: {ca_cert_path}")
    print("  2. Instalar en Configuracion > Seguridad > Certificados")
    print("=" * 60)

    return server_cert_path, server_key_path, ca_cert_path


if __name__ == "__main__":
    ip = sys.argv[1] if len(sys.argv) > 1 else None
    try:
        setup_certificates(ip)
    except KeyboardInterrupt:
        print("\n[!] Cancelado por el usuario.")
        sys.exit(1)
    except Exception as e:
        print(f"\n[ERROR] Error: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)
