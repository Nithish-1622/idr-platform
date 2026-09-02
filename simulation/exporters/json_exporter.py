import json
from pathlib import Path
from typing import Any, Dict


class JSONExporter:
    """Exports structured simulation evaluation reports and scenario metadata to JSON files."""

    @staticmethod
    def export_report(report_data: Dict[str, Any], file_path: Path) -> Path:
        file_path = Path(file_path)
        file_path.parent.mkdir(parents=True, exist_ok=True)

        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(report_data, f, indent=2)

        return file_path
