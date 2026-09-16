import json
import re
from datetime import datetime
from pathlib import Path


def safe_filename(value: str) -> str:
    return re.sub(
        r"[^A-Za-z0-9_.-]+",
        "_",
        value
    )


def timestamp() -> str:
    return datetime.now().strftime(
        "%Y%m%d_%H%M%S"
    )


def save_json(
    data: dict,
    directory: Path,
    filename: str
) -> Path:

    directory.mkdir(
        parents=True,
        exist_ok=True
    )

    path = directory / filename

    with path.open(
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            data,
            file,
            indent=4,
            ensure_ascii=False
        )

    return path


def load_json(
    path: Path
) -> dict:

    with path.open(
        "r",
        encoding="utf-8"
    ) as file:

        return json.load(file)


def latest_file(
    directory: Path,
    pattern: str
) -> Path | None:

    files = list(
        directory.glob(pattern)
    )

    if not files:
        return None

    return max(
        files,
        key=lambda item: item.stat().st_mtime
    )