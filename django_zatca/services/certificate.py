import subprocess
import tempfile
import os
import logging
from ..exceptions import CertificateException

logger = logging.getLogger("django_zatca")


def generate_ec_key_pair():
    logger.info("Generating secp256k1 EC key pair")
    try:
        result = subprocess.check_output(
            ["openssl", "ecparam", "-name", "secp256k1", "-genkey"],
            stderr=subprocess.STDOUT,
        ).decode("utf-8").strip()
    except (subprocess.CalledProcessError, FileNotFoundError) as e:
        raise CertificateException(f"Failed to generate EC key pair. OpenSSL may not be available: {e}")

    lines = result.splitlines()
    # Strip OpenSSL loading/random state messages (common on Windows)
    relevant = []
    for l in lines:
        if not l.startswith("Loading") and not l.startswith(".") and "random state" not in l and "unable to write" not in l:
            relevant.append(l)
    result = "\n".join(relevant)
    # Extract only from BEGIN EC PRIVATE KEY to END EC PRIVATE KEY
    start = result.find("-----BEGIN EC PRIVATE KEY-----")
    end = result.find("-----END EC PRIVATE KEY-----")
    if start >= 0 and end >= 0:
        result = result[start:end + len("-----END EC PRIVATE KEY-----")]

    if "BEGIN EC PRIVATE KEY" not in result:
        raise CertificateException("Invalid EC private key generated")
    return result


def _write_csr_config(cnf_file, dn_only=False, **kwargs):
    if dn_only:
        cnf = f"""[req]
prompt = no
distinguished_name = dn

[dn]
commonName = {kwargs['taxpayer_provided_id']}
organizationalUnitName = {kwargs['branch_name']}
organizationName = {kwargs['taxpayer_name']}
countryName = SA
"""
    else:
        production_val = "ZATCA-Code-Signing" if kwargs.get('production') else "TSTZATCA-Code-Signing"
        egs_serial = f"1-{kwargs['solution_name']}|2-{kwargs['egs_serial_number']}"
        cnf = f"""[req]
prompt = no
utf8 = no
distinguished_name = dn
req_extensions = ext

[ext]
1.3.6.1.4.1.311.20.2 = ASN1:UTF8String:{production_val}
subjectAltName = dirName:dir_sect

[dir_sect]
SN = {egs_serial}
UID = {kwargs['vat_number']}
title = 0100
registeredAddress = {kwargs['branch_location']}
businessCategory = {kwargs['branch_industry']}

[dn]
commonName = {kwargs['taxpayer_provided_id']}
organizationalUnitName = {kwargs['branch_name']}
organizationName = {kwargs['taxpayer_name']}
countryName = SA
"""
    with open(cnf_file, "w") as f:
        f.write(cnf)


def generate_csr(private_key, solution_name, egs_serial_number, vat_number,
                 branch_location, branch_industry, branch_name, taxpayer_name,
                 taxpayer_provided_id, production=False):
    logger.info(f"Generating CSR for solution: {solution_name}")
    tmp_dir = tempfile.mkdtemp(prefix="zatca_")
    key_file = os.path.join(tmp_dir, "key.pem")
    cnf_file = os.path.join(tmp_dir, "csr.cnf")

    ctx = dict(
        solution_name=solution_name, egs_serial_number=egs_serial_number,
        vat_number=vat_number, branch_location=branch_location,
        branch_industry=branch_industry, branch_name=branch_name,
        taxpayer_name=taxpayer_name, taxpayer_provided_id=taxpayer_provided_id,
        production=production,
    )
    try:
        with open(key_file, "w") as f:
            f.write(private_key)

        _write_csr_config(cnf_file, dn_only=False, **ctx)

        try:
            result = subprocess.check_output(
                ["openssl", "req", "-new", "-sha256", "-key", key_file, "-config", cnf_file],
                stderr=subprocess.STDOUT,
            ).decode("utf-8").strip()
        except subprocess.CalledProcessError:
            _write_csr_config(cnf_file, dn_only=True, **ctx)
            result = subprocess.check_output(
                ["openssl", "req", "-new", "-sha256", "-key", key_file, "-config", cnf_file],
                stderr=subprocess.STDOUT,
            ).decode("utf-8").strip()

        if "BEGIN CERTIFICATE REQUEST" not in result:
            raise CertificateException(f"CSR generation failed: {result}")
        return result
    finally:
        for f in [key_file, cnf_file]:
            try:
                os.remove(f)
            except OSError:
                pass
        try:
            os.rmdir(tmp_dir)
        except OSError:
            pass
        try:
            os.rmdir(tmp_dir)
        except OSError:
            pass


def parse_certificate_info(certificate):
    import base64 as b64
    cleaned = clean_certificate(certificate)
    pem = f"-----BEGIN CERTIFICATE-----\n{cleaned}\n-----END CERTIFICATE-----"

    with tempfile.NamedTemporaryFile(mode="w", suffix=".pem", delete=False) as f:
        f.write(pem)
        pem_path = f.name

    try:
        result = subprocess.check_output(
            ["openssl", "x509", "-in", pem_path, "-noout", "-text"],
            stderr=subprocess.STDOUT,
        ).decode("utf-8")
    except subprocess.CalledProcessError as e:
        raise CertificateException(f"Failed to parse certificate: {e}")
    finally:
        os.remove(pem_path)

    serial = ""
    for line in result.splitlines():
        line = line.strip()
        if line.startswith("Serial Number:"):
            serial = line.split(":", 1)[1].strip()
            break

    try:
        pubkey_result = subprocess.check_output(
            ["openssl", "x509", "-in", pem_path, "-noout", "-pubkey"],
            stderr=subprocess.STDOUT,
        ).decode("utf-8")
    except subprocess.CalledProcessError:
        pubkey_result = ""

    pubkey_clean = ""
    for line in pubkey_result.splitlines():
        if "BEGIN PUBLIC KEY" not in line and "END PUBLIC KEY" not in line:
            pubkey_clean += line.strip()
    try:
        pubkey_bytes = b64.b64decode(pubkey_clean)
    except Exception:
        pubkey_bytes = b""

    hash_bytes = __import__("hashlib").sha256(cleaned.encode("utf-8")).digest()
    cert_hash = b64.b64encode(hash_bytes).decode("ascii")

    issuer = ""
    for line in result.splitlines():
        line = line.strip()
        if line.startswith("Issuer:"):
            issuer = line.split(":", 1)[1].strip()
            break

    sig = _extract_cert_signature(pem)
    return {
        "hash": cert_hash,
        "issuer": issuer,
        "serial_number": serial,
        "public_key": pubkey_bytes,
        "signature": sig,
    }


def _extract_cert_signature(cert_pem):
    try:
        sig_result = subprocess.check_output(
            ["openssl", "x509", "-in", "-", "-noout", "-text"],
            input=cert_pem.encode("utf-8"),
            stderr=subprocess.STDOUT,
        ).decode("utf-8")
        for line in sig_result.splitlines():
            line = line.strip()
            if "Signature Value" in line or "signature" in line.lower():
                parts = line.split(":")
                if len(parts) > 1:
                    return parts[1].strip().replace(" ", "").replace("\n", "")
    except Exception:
        pass
    return ""


def clean_certificate(certificate):
    out = certificate.replace("-----BEGIN CERTIFICATE-----", "")
    out = out.replace("-----END CERTIFICATE-----", "")
    return out.strip()


def clean_private_key(private_key):
    out = private_key.replace("-----BEGIN EC PRIVATE KEY-----", "")
    out = out.replace("-----END EC PRIVATE KEY-----", "")
    return out.strip()
