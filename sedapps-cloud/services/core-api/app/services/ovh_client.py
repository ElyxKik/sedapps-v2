from __future__ import annotations

import logging
import ovh
from app.config import settings

logger = logging.getLogger(__name__)


class OvhClient:
    """Client wrapper for OVH API to check domain availability."""

    def __init__(self) -> None:
        self.enabled = bool(
            settings.OVH_APP_KEY and settings.OVH_APP_SECRET and settings.OVH_CONSUMER_KEY
        )
        self._client = None
        if self.enabled:
            try:
                self._client = ovh.Client(
                    endpoint=settings.OVH_ENDPOINT,
                    application_key=settings.OVH_APP_KEY,
                    application_secret=settings.OVH_APP_SECRET,
                    consumer_key=settings.OVH_CONSUMER_KEY,
                )
            except Exception as e:
                logger.error(f"Failed to initialize OVH client: {e}")
                self.enabled = False

    def is_domain_available(self, domain: str) -> bool:
        """
        Check if a custom domain is available for registration using OVH API.
        If credentials are not configured, defaults to True for UX flexibility.
        """
        if not self.enabled or not self._client:
            logger.warning(
                "OVH Client credentials not configured or initialization failed. Defaulting domain availability to True."
            )
            return True

        try:
            # Check domain availability status
            # API endpoint: GET /domain/zone
            # Or simpler, check using /domain/register/merchant/status or /domain/zone/{zoneName}/status
            # A cleaner approach in OVH API to check availability is checking the domain directly:
            # GET /domain/register/search?domain={domain}
            results = self._client.get("/domain/register/search", domain=domain)
            for res in results:
                if res.get("domain") == domain:
                    # check if the action is 'create' (it means it is available to purchase)
                    # and not 'none' or 'transfer' or 'import'
                    # Available states in OVH register status:
                    # create: domain is free and can be registered
                    # deliverable / available: free
                    action = res.get("action", "none")
                    return action == "create"
            return True
        except Exception as e:
            logger.error(f"OVH API check failed for {domain}: {e}")
            # If API fails (e.g. rate limit, invalid credentials), default to True to not block the onboarding
            return True
