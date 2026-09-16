import os
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlparse

from dotenv import load_dotenv


# ============================================================
# CHEMINS
# ============================================================

BASE_DIR = Path(__file__).resolve().parent

load_dotenv(BASE_DIR / ".env")


# ============================================================
# OUTILS
# ============================================================

def env_bool(name: str, default: bool = True) -> bool:
    """
    Lit une variable d'environnement de type booléen.
    """

    value = os.getenv(name)

    if value is None:
        return default

    return value.strip().lower() in {
        "1",
        "true",
        "yes",
        "y",
        "on",
    }


# ============================================================
# CONFIGURATION
# ============================================================

@dataclass(frozen=True)
class Settings:

    # Jira
    jira_url: str
    jira_pat: str
    instance_name: str

    # Version cible
    target_jira_family: str
    target_jira_version: str

    # ScriptRunner REST Endpoint
    baseline_endpoint: str

    # HTTP
    request_timeout: int
    max_retries: int
    verify_ssl: bool

    # Output
    output_dir: Path


    @classmethod
    def from_env(cls):

        # ----------------------------------------------------
        # Jira URL
        # ----------------------------------------------------

        jira_url = (
            os.getenv(
                "JIRA_URL",
                ""
            )
            .strip()
            .rstrip("/")
        )

        if not jira_url:
            raise ValueError(
                "JIRA_URL absent du fichier .env"
            )


        # ----------------------------------------------------
        # Jira PAT
        # ----------------------------------------------------

        jira_pat = os.getenv(
            "JIRA_PAT",
            ""
        ).strip()

        if not jira_pat:
            raise ValueError(
                "JIRA_PAT absent du fichier .env"
            )


        # ----------------------------------------------------
        # Nom de l'instance
        # ----------------------------------------------------

        instance_name = os.getenv(
            "INSTANCE_NAME",
            ""
        ).strip()

        if not instance_name:

            hostname = urlparse(
                jira_url
            ).hostname

            instance_name = (
                hostname
                or "JIRA"
            )


        # ----------------------------------------------------
        # Version cible Jira
        #
        # Exemple actuel :
        #
        # TARGET_JIRA_FAMILY=11.3
        # TARGET_JIRA_VERSION=
        #
        # La version exacte pourra ensuite devenir :
        #
        # TARGET_JIRA_VERSION=11.3.11
        # ----------------------------------------------------

        target_jira_family = os.getenv(
            "TARGET_JIRA_FAMILY",
            ""
        ).strip()

        target_jira_version = os.getenv(
            "TARGET_JIRA_VERSION",
            ""
        ).strip()


        # ----------------------------------------------------
        # ScriptRunner Endpoint
        # ----------------------------------------------------

        endpoint = os.getenv(
            "BASELINE_ENDPOINT",
            "/rest/scriptrunner/latest/custom/upgradeBaseline"
        ).strip()

        if not endpoint.startswith("/"):
            endpoint = "/" + endpoint


        # ----------------------------------------------------
        # Output
        # ----------------------------------------------------

        output_value = os.getenv(
            "OUTPUT_DIR",
            "output"
        ).strip()

        output_path = Path(
            output_value
        )

        if not output_path.is_absolute():

            output_path = (
                BASE_DIR
                / output_path
            )


        # ----------------------------------------------------
        # Construction de la configuration
        # ----------------------------------------------------

        return cls(

            jira_url=jira_url,

            jira_pat=jira_pat,

            instance_name=instance_name,

            target_jira_family=target_jira_family,

            target_jira_version=target_jira_version,

            baseline_endpoint=endpoint,

            request_timeout=int(
                os.getenv(
                    "REQUEST_TIMEOUT",
                    "30"
                )
            ),

            max_retries=int(
                os.getenv(
                    "MAX_RETRIES",
                    "4"
                )
            ),

            verify_ssl=env_bool(
                "VERIFY_SSL",
                True
            ),

            output_dir=output_path,
        )