from dataclasses import dataclass
from pathlib import Path


@dataclass
class BaselineSnapshot:
    phase: str
    data: dict
    json_path: Path | None = None