import subprocess
from django.core.management.base import BaseCommand
from django_zatca.defaults import zatca_setting


class Command(BaseCommand):
    help = "Check ZATCA package readiness"

    def add_arguments(self, parser):
        parser.add_argument("--openssl", action="store_true", help="Check OpenSSL availability")
        parser.add_argument("--config", action="store_true", help="Display current configuration")

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS("ZATCA Package Readiness Check\n"))

        check_openssl = options.get("openssl")
        check_config = options.get("config")

        if not check_openssl and not check_config:
            check_openssl = True
            check_config = True

        if check_openssl:
            self._check_openssl()

        if check_openssl and check_config:
            self.stdout.write("")

        if check_config:
            self._display_config()

    def _check_openssl(self):
        self.stdout.write("Checking OpenSSL...")
        try:
            version = subprocess.check_output(["openssl", "version"]).decode("utf-8").strip()
            self.stdout.write(self.style.SUCCESS(f"OpenSSL: {version}"))
            curves = subprocess.check_output(["openssl", "ecparam", "-list_curves"]).decode("utf-8")
            if "secp256k1" in curves:
                self.stdout.write(self.style.SUCCESS("secp256k1 curve: Available"))
            else:
                self.stdout.write(self.style.WARNING("secp256k1 curve: Not found"))
        except (subprocess.CalledProcessError, FileNotFoundError):
            self.stdout.write(self.style.ERROR("OpenSSL is not available or not in PATH"))

    def _display_config(self):
        self.stdout.write("Current Configuration:")
        self.stdout.write(f"  Phase:       {zatca_setting('PHASE', 'not set')}")
        self.stdout.write(f"  Environment: {zatca_setting('ENVIRONMENT', 'not set')}")
        self.stdout.write(f"  Queue:       {zatca_setting('QUEUE_CONNECTION', 'sync')}")
        self.stdout.write(f"  Queue Name:  {zatca_setting('QUEUE_NAME', 'zatca')}")
        self.stdout.write(f"  Logging:     {'enabled' if zatca_setting('LOGGING_ENABLED', True) else 'disabled'}")

        env = zatca_setting("ENVIRONMENT", "sandbox")
        if env == "sandbox":
            api_url = zatca_setting("API_SANDBOX_BASE")
        else:
            api_url = zatca_setting("API_PRODUCTION_BASE")
        self.stdout.write(f"  API URL:     {api_url or 'not set'}")
