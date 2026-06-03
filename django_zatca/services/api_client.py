import json
import logging
import base64
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError
from ..exceptions import ZatcaException
from ..defaults import zatca_setting

logger = logging.getLogger("django_zatca")


class ApiClient:
    def __init__(self, environment=None):
        from ..enums import Environment as Env
        self.environment = environment or Env.SANDBOX
        self.base_url = zatca_setting(
            f"API_{self.environment.value.upper()}_BASE",
            f"https://gw-fatoora.zatca.gov.sa/e-invoicing/{'developer-portal' if self.environment.is_sandbox() else ''}",
        )
        self.version = zatca_setting("API_VERSION", "V2")
        self.timeout = zatca_setting("API_TIMEOUT", 60)

    def post(self, endpoint, data, certificate=None, secret=None, otp=None):
        url = f"{self.base_url.rstrip('/')}/{endpoint.lstrip('/')}"
        headers = self._build_headers(certificate, secret, otp)
        body = json.dumps(data).encode("utf-8")

        logger.info(f"ZATCA API request: {endpoint}")
        req = Request(url, data=body, headers=headers, method="POST")

        try:
            resp = urlopen(req, timeout=self.timeout)
            response_data = json.loads(resp.read().decode("utf-8"))
            logger.info(f"ZATCA API success: {endpoint}")
            return response_data
        except HTTPError as e:
            err_body = e.read().decode("utf-8", errors="replace")
            try:
                err_json = json.loads(err_body)
                err_msg = err_json.get("errors", [{}])[0].get("message", err_json.get("error", str(e)))
            except (json.JSONDecodeError, IndexError):
                err_msg = err_body or str(e)
            logger.error(f"ZATCA API error ({e.code}): {err_msg}")
            raise ZatcaException(f"ZATCA API error ({e.code}): {err_msg}", code=e.code)
        except URLError as e:
            logger.error(f"ZATCA API connection error: {e.reason}")
            raise ZatcaException(f"ZATCA API connection failed: {e.reason}")

    def _build_headers(self, certificate, secret, otp):
        headers = {
            "Accept-Version": self.version,
            "Content-Type": "application/json",
            "Accept-Language": "en",
            "Cache-Control": "no-cache",
        }
        if otp:
            headers["OTP"] = otp
        if certificate and secret:
            cleaned = certificate.replace("-----BEGIN CERTIFICATE-----", "")
            cleaned = cleaned.replace("-----END CERTIFICATE-----", "").strip()
            creds = base64.b64encode(
                base64.b64encode(cleaned.encode("utf-8")) + b":" + secret.encode("utf-8")
            ).decode("ascii")
            headers["Authorization"] = f"Basic {creds}"
        return headers
