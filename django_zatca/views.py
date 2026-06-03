import logging
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django_zatca.defaults import zatca_setting, get_egs_config
from django_zatca.enums import Environment as Env

logger = logging.getLogger("django_zatca")


@csrf_exempt
def zatca_status(request):
    from django_zatca.enums import ZatcaPhase
    phase = ZatcaPhase(zatca_setting("PHASE", "both"))
    env = Env(zatca_setting("ENVIRONMENT", "sandbox"))
    return JsonResponse({
        "phase": phase.value,
        "environment": env.value,
        "phase1_enabled": phase in (ZatcaPhase.PHASE1, ZatcaPhase.BOTH),
        "phase2_enabled": phase in (ZatcaPhase.PHASE2, ZatcaPhase.BOTH),
    })


@csrf_exempt
def zatca_onboard(request):
    if request.method != "POST":
        return JsonResponse({"error": "POST required"}, status=405)

    import json
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON"}, status=400)

    otp = data.get("otp")
    solution_name = data.get("solution_name", "ERP")

    if not otp:
        return JsonResponse({"error": "OTP is required"}, status=422)

    try:
        from django_zatca.services.phase2 import Phase2Service
        phase2 = Phase2Service()
        egs_unit = get_egs_config()
        keys = phase2.generate_keys_and_csr(egs_unit, solution_name)
        compliance = phase2.issue_compliance_certificate(keys["csr"], otp)

        return JsonResponse({
            "success": compliance.success,
            "request_id": compliance.request_id,
            "binary_security_token": compliance.binary_security_token,
            "secret": compliance.secret,
            "error_message": compliance.error_message,
        })
    except Exception as e:
        logger.exception("Onboarding failed")
        return JsonResponse({"error": str(e)}, status=500)


@csrf_exempt
def zatca_sync_invoice(request):
    if request.method != "POST":
        return JsonResponse({"error": "POST required"}, status=405)

    import json
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON"}, status=400)

    serial = data.get("invoice_serial_number")
    if not serial:
        return JsonResponse({"error": "invoice_serial_number is required"}, status=422)

    try:
        from django_zatca.tasks import sync_invoice_to_zatca
        sync_invoice_to_zatca(
            invoice_data=data,
            egs_unit=get_egs_config(),
            certificate=zatca_setting("CERTIFICATE"),
            private_key=zatca_setting("PRIVATE_KEY"),
            secret=zatca_setting("SECRET"),
        )
        return JsonResponse({"message": "Job dispatched", "serial": serial})
    except Exception as e:
        logger.exception("Invoice sync failed")
        return JsonResponse({"error": str(e)}, status=500)
