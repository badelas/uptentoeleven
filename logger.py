import logging
from pathlib import Path


def configure_logging(log_dir: Path):
    log_dir.mkdir(
        parents=True,
        exist_ok=True
    )

    log_file = log_dir / "jira_upgrade_toolkit.log"

    logging.basicConfig(
        level=logging.INFO,
        format=(
            "%(asctime)s | "
            "%(levelname)s | "
            "%(name)s | "
            "%(message)s"
        ),
        handlers=[
            logging.FileHandler(
                log_file,
                encoding="utf-8"
            ),
            logging.StreamHandler()
        ],
        force=True
    )


def get_logger(name: str):
    return logging.getLogger(name)