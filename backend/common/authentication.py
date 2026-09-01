import logging
from django.conf import settings
from django.contrib.auth import get_user_model
from rest_framework.authentication import BaseAuthentication

logger = logging.getLogger(__name__)


class DevBypassAuthentication(BaseAuthentication):
    """
    Authentication class that automatically authenticates any incoming request as a
    mock/dev administrator user when DEV_MODE is set to True.
    """

    def authenticate(self, request):
        if not getattr(settings, "DEV_MODE", False):
            return None

        User = get_user_model()
        try:
            user, _ = User.objects.get_or_create(
                username="dev_admin",
                defaults={
                    "email": "dev@example.com",
                    "role": "ADMIN",
                    "is_staff": True,
                    "is_superuser": True,
                    "is_active": True,
                },
            )
            return (user, None)
        except Exception as e:
            logger.warning("DEV_MODE bypass user get_or_create failed: %s", e)
            dev_user = User(
                username="dev_admin",
                email="dev@example.com",
                role="ADMIN",
                is_staff=True,
                is_superuser=True,
                is_active=True,
            )
            return (dev_user, None)
