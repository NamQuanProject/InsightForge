import csv
from pathlib import Path


class PlatformMockService:
    def __init__(self, platform: str) -> None:
        self.platform = platform
        self.data_dir = Path(__file__).resolve().parents[1] / "mock_data" / platform

    def _load_single(self, filename: str) -> dict[str, str]:
        rows = self._read_rows(filename)
        if not rows:
            raise ValueError(f"Mock data file is empty: {self.data_dir / filename}")
        return rows[0]

    def _read_rows(self, filename: str) -> list[dict[str, str]]:
        path = self.data_dir / filename
        with path.open("r", encoding="utf-8", newline="") as file:
            return list(csv.DictReader(file))

    def _split(self, value: str) -> list[str]:
        return [item.strip() for item in value.split("|") if item.strip()]

    def _to_int(self, value: str) -> int:
        return int(value)

    def _to_float(self, value: str) -> float:
        return float(value)
