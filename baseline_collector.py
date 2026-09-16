from api_client import JiraApiClient
from config import Settings
from logger import get_logger


logger = get_logger(__name__)


def collect_baseline(
    client: JiraApiClient,
    settings: Settings
) -> dict:

    logger.info(
        "Collecte de la baseline Jira..."
    )

    baseline = client.get(
        settings.baseline_endpoint
    )

    if not isinstance(
        baseline,
        dict
    ):
        raise ValueError(
            "La baseline reçue n'est pas "
            "un objet JSON."
        )

    required_sections = [
        "jira",
        "architecture",
        "java",
        "operatingSystem",
        "database"
    ]

    missing = [
        section
        for section in required_sections
        if section not in baseline
    ]

    if missing:
        logger.warning(
            "Sections absentes : %s",
            ", ".join(missing)
        )

    logger.info(
        "Baseline collectée avec succès."
    )

    return baseline