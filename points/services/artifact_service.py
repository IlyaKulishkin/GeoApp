import requests
from rest_framework_simplejwt.tokens import AccessToken
from .rabbitmq_service import publish_message, RabbitMQUnavailable
from points.models.api import Artifact
from django.db import transaction
from django.utils import timezone


FASTAPI_URL = "http://fastapi:8001"


def sync_artifacts_http(user):
    response = requests.get(
        f"{FASTAPI_URL}/api/artifacts",
        headers={"Authorization": f"Bearer {str(AccessToken.for_user(user))}"},
        timeout=30
    )

    response.raise_for_status()

    artifacts = response.json()

    with transaction.atomic():
        for art in artifacts:
            Artifact.objects.update_or_create(
                fastapi_id=art["id"],
                defaults={
                    "name": art["name"],
                    "description": art.get("description", ""),
                    "owner": user,
                    "synced_at": timezone.now(),
                }
            )

    return {
        "synced": len(artifacts),
        "transport": "http"
    }


def sync_artifacts_from_fastapi(user):
    try:
        publish_message(
            "artifacts_request",
            {
                "user_id": user.id
            }
        )

        return {
            "status": "queued",
            "transport": "rabbitmq"
        }

    except RabbitMQUnavailable:
        return sync_artifacts_http(user)
