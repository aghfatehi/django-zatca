import os
import subprocess
from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = "Onboard EGS unit with ZATCA and obtain compliance certificate"

    def add_arguments(self, parser):
        parser.add_argument("--otp", type=str, help="OTP received from ZATCA portal")
        parser.add_argument("--solution-name", type=str, default="ERP", help="Solution/Application name")
        parser.add_argument("--production", action="store_true", help="Use production environment")
        parser.add_argument("--save", action="store_true", help="Save credentials to .env file")

    def handle(self, *args, **options):
        from django_zatca.services.phase2 import Phase2Service
        from django_zatca.defaults import get_egs_config

        self.stdout.write(self.style.SUCCESS("ZATCA Onboarding Wizard\n"))

        egs_config = get_egs_config()
        egs_unit = {
            "uuid": input(f"EGS UUID [{egs_config['uuid']}]: ") or egs_config["uuid"],
            "custom_id": input(f"EGS Custom ID [{egs_config['uuid']}]: ") or egs_config["uuid"],
            "model": input("EGS Model [Desktop]: ") or "Desktop",
            "vat_number": input(f"VAT Number [{egs_config['vat_number']}]: ") or egs_config["vat_number"],
            "vat_name": input(f"VAT Name [{egs_config['vat_name']}]: ") or egs_config["vat_name"],
            "crn_number": input(f"CRN Number [{egs_config['crn_number']}]: ") or egs_config["crn_number"],
            "location": {
                "city": input(f"City [{egs_config['location']['city']}]: ") or egs_config["location"]["city"],
                "city_subdivision": input(f"City Subdivision [{egs_config['location']['city_subdivision']}]: ") or egs_config["location"]["city_subdivision"],
                "street": input(f"Street [{egs_config['location']['street']}]: ") or egs_config["location"]["street"],
                "building": input(f"Building Number [{egs_config['location']['building']}]: ") or egs_config["location"]["building"],
                "plot_identification": input(f"Plot Identification [{egs_config['location']['plot_identification']}]: ") or egs_config["location"]["plot_identification"],
                "postal_zone": input(f"Postal Zone [{egs_config['location']['postal_zone']}]: ") or egs_config["location"]["postal_zone"],
            },
            "branch_name": input(f"Branch Name [{egs_config['branch_name']}]: ") or egs_config["branch_name"],
            "branch_industry": input(f"Branch Industry [{egs_config['branch_industry']}]: ") or egs_config["branch_industry"],
        }

        solution_name = options["solution_name"]
        self.stdout.write("\nGenerating EC key pair and CSR...\n")

        try:
            phase2 = Phase2Service()
            keys = phase2.generate_keys_and_csr(egs_unit, solution_name)

            self.stdout.write(self.style.SUCCESS("Private Key generated successfully."))
            self.stdout.write(keys["private_key"])
            self.stdout.write("")

            self.stdout.write(self.style.SUCCESS("CSR generated successfully."))
            self.stdout.write(keys["csr"])
            self.stdout.write("")

            otp = options["otp"] or input("Enter OTP from ZATCA portal: ")

            self.stdout.write("Issuing compliance certificate...\n")
            result = phase2.issue_compliance_certificate(keys["csr"], otp)

            if result.success:
                self.stdout.write(self.style.SUCCESS("Compliance certificate issued successfully!\n"))
                self.stdout.write("Certificate:")
                self.stdout.write(result.binary_security_token)
                self.stdout.write(f"\nSecret: {result.secret}\n")

                if options["save"]:
                    self._save_credentials(result.binary_security_token, result.secret, keys["private_key"])
            else:
                self.stdout.write(self.style.ERROR(f'Failed: {result.error_message or "Unknown error"}'))
                return

        except Exception as e:
            raise CommandError(str(e))

    def _save_credentials(self, certificate, secret, private_key):
        import base64
        env_file = ".env"
        if not os.path.exists(env_file):
            env_file = ".env.example"

        with open(env_file, "r") as f:
            content = f.read()

        replacements = {
            "ZATCA_CERTIFICATE": base64.b64encode(certificate.encode("utf-8")).decode("ascii"),
            "ZATCA_SECRET": secret,
            "ZATCA_PRIVATE_KEY": base64.b64encode(private_key.encode("utf-8")).decode("ascii"),
        }

        for key, value in replacements.items():
            import re
            pattern = rf"^{key}=.*"
            if re.search(pattern, content, re.MULTILINE):
                content = re.sub(pattern, f"{key}={value}", content, flags=re.MULTILINE)
            else:
                content += f"\n{key}={value}"

        with open(".env", "w") as f:
            f.write(content)

        self.stdout.write(self.style.SUCCESS("Credentials saved to .env file."))
