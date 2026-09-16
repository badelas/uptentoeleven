import time

import requests

from config import Settings
from logger import get_logger


logger = get_logger(__name__)


class JiraApiClient:

    def __init__(self, settings: Settings):
        self.settings = settings

        self.session = requests.Session()

        self.session.headers.update({
            "Authorization": (
                f"Bearer {settings.jira_pat}"
            ),
            "Accept": "application/json"
        })

        self.stats = {
            "requests_total": 0,
            "retries_total": 0,
            "rate_limits_429": 0,
            "server_errors_5xx": 0,
            "network_errors": 0
        }

    def _build_url(self, path: str) -> str:
        if path.startswith("http://") or path.startswith("https://"):
            return path

        return (
            f"{self.settings.jira_url}/"
            f"{path.lstrip('/')}"
        )

    def _backoff(self, attempt: int) -> int:
        return min(
            2 ** attempt,
            30
        )

    def get(self, path: str):
        url = self._build_url(path)

        max_attempts = (
            self.settings.max_retries + 1
        )

        for attempt in range(max_attempts):

            self.stats["requests_total"] += 1

            try:
                logger.info(
                    "GET %s",
                    url
                )

                response = self.session.get(
                    url,
                    timeout=self.settings.request_timeout,
                    verify=self.settings.verify_ssl
                )

            except requests.RequestException as exc:

                self.stats["network_errors"] += 1

                if attempt >= (
                    max_attempts - 1
                ):
                    raise RuntimeError(
                        f"Erreur réseau : {exc}"
                    ) from exc

                self.stats["retries_total"] += 1

                delay = self._backoff(attempt)

                logger.warning(
                    "Erreur réseau. Retry dans %ss",
                    delay
                )

                time.sleep(delay)
                continue

            # --------------------------------------------
            # 429 RATE LIMIT
            # --------------------------------------------

            if response.status_code == 429:

                self.stats[
                    "rate_limits_429"
                ] += 1

                if attempt >= (
                    max_attempts - 1
                ):
                    raise RuntimeError(
                        "Rate limit 429 après "
                        "plusieurs tentatives."
                    )

                retry_after = (
                    response.headers.get(
                        "Retry-After"
                    )
                )

                try:
                    delay = int(retry_after)
                except (
                    TypeError,
                    ValueError
                ):
                    delay = self._backoff(
                        attempt
                    )

                self.stats[
                    "retries_total"
                ] += 1

                logger.warning(
                    "HTTP 429. Retry dans %ss",
                    delay
                )

                time.sleep(delay)
                continue

            # --------------------------------------------
            # 5xx SERVER ERRORS
            # --------------------------------------------

            if 500 <= response.status_code <= 599:

                self.stats[
                    "server_errors_5xx"
                ] += 1

                if attempt >= (
                    max_attempts - 1
                ):
                    response.raise_for_status()

                self.stats[
                    "retries_total"
                ] += 1

                delay = self._backoff(
                    attempt
                )

                logger.warning(
                    "HTTP %s. Retry dans %ss",
                    response.status_code,
                    delay
                )

                time.sleep(delay)
                continue

            # --------------------------------------------
            # AUTH
            # --------------------------------------------

            if response.status_code == 401:
                raise RuntimeError(
                    "HTTP 401 : PAT invalide, "
                    "expiré ou non reconnu."
                )

            if response.status_code == 403:
                raise RuntimeError(
                    "HTTP 403 : utilisateur "
                    "authentifié mais non autorisé."
                )

            response.raise_for_status()

            try:
                return response.json()

            except ValueError as exc:
                raise RuntimeError(
                    "La réponse Jira n'est pas "
                    "un JSON valide."
                ) from exc

        raise RuntimeError(
            "Erreur HTTP inattendue."
        )