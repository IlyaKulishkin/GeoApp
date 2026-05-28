import logging
import requests
from django.db import transaction
from django.utils import timezone
from rest_framework_simplejwt.tokens import AccessToken

from points.models.api import Artifact

logger = logging.getLogger(__name__)

FASTAPI_URL = "http://fastapi:8001"


def sync_artifacts_http(user):
    token = str(AccessToken.for_user(user))
    headers = {"Authorization": f"Bearer {token}"}

    logger.info(f"Starting HTTP sync for user {user.username}")

    try:
        response = requests.get(
            f"{FASTAPI_URL}/api/artifacts",
            headers=headers,
            timeout=30
        )
        response.raise_for_status()
        artifacts = response.json()
    except requests.RequestException as e:
        logger.error(f"HTTP sync failed for user {user.username}: {e}")
        raise

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

    logger.info(f"HTTP sync completed: {len(artifacts)} artifacts for user {user.username}")

    return {
        "synced": len(artifacts),
        "transport": "http"
    }
