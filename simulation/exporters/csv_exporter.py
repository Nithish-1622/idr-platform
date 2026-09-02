import csv
from pathlib import Path
from typing import Any, Dict, List


class CSVExporter:
    """Exports ground truth and sensor observations streams to clean CSV files."""

    @staticmethod
    def export_ground_truth(states: List[Any], file_path: Path) -> Path:
        file_path = Path(file_path)
        file_path.parent.mkdir(parents=True, exist_ok=True)

        with open(file_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(
                [
                    "timestamp",
                    "x",
                    "y",
                    "z",
                    "speed",
                    "vx",
                    "vy",
                    "heading_deg",
                    "latitude",
                    "longitude",
                    "altitude",
                ]
            )
            for s in states:
                writer.writerow(
                    [
                        s.timestamp,
                        s.x,
                        s.y,
                        s.z,
                        s.speed,
                        s.vx,
                        s.vy,
                        s.heading_deg,
                        s.latitude,
                        s.longitude,
                        s.altitude,
                    ]
                )

        return file_path

    @staticmethod
    def export_sensor_stream(sensor_records: List[Dict[str, Any]], file_path: Path) -> Path:
        file_path = Path(file_path)
        file_path.parent.mkdir(parents=True, exist_ok=True)

        if not sensor_records:
            return file_path

        # Gather all field names dynamically across sensor types
        fieldnames = set()
        for r in sensor_records:
            fieldnames.update(r.keys())

        fields = sorted(list(fieldnames))
        if "timestamp" in fields:
            fields.remove("timestamp")
            fields = ["timestamp"] + fields

        with open(file_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fields)
            writer.writeheader()
            for r in sensor_records:
                writer.writerow(r)

        return file_path
