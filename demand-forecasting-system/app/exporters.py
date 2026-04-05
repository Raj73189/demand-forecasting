import csv
import io
from datetime import UTC, datetime
from typing import Any


def make_safe_filename(raw: str) -> str:
    cleaned = "".join(ch if ch.isalnum() or ch in ("-", "_", ".") else "_" for ch in raw.strip())
    compact = "_".join(part for part in cleaned.split("_") if part)
    return compact or "forecast_export"


def _format_timestamp(value: str | None) -> str:
    if not value:
        return "-"
    return value


def build_forecast_csv_bytes(
    product_name: str,
    historical: list[dict[str, Any]],
    forecast: list[dict[str, Any]],
    summary: dict[str, Any],
    created_at: str | None,
) -> bytes:
    output = io.StringIO()
    writer = csv.writer(output)

    writer.writerow(["Product Name", product_name])
    writer.writerow(["Generated At", _format_timestamp(created_at)])
    writer.writerow([])

    writer.writerow(["Summary"])
    writer.writerow(["High Demand Threshold", summary["high_demand_threshold"]])
    writer.writerow(["Next Month Forecast", summary["next_month"]["forecast"]])
    writer.writerow(["Next Month High Demand", summary["next_month"]["is_high_demand"]])
    writer.writerow(["Next 5 Months Avg Forecast", summary["next_5_months"]["average_forecast"]])
    writer.writerow(["Next 5 Months High-Demand Months", summary["next_5_months"]["months_high_demand"]])
    writer.writerow(["Next 5 Months High Demand", summary["next_5_months"]["is_high_demand"]])
    writer.writerow(["Next 5 Years Growth Percent", summary["next_5_years"]["growth_percent"]])
    writer.writerow(["Next 5 Years High Demand", summary["next_5_years"]["is_high_demand"]])
    writer.writerow([])

    writer.writerow(["Historical Data"])
    writer.writerow(["date", "demand"])
    for row in historical:
        writer.writerow([row["date"], row["demand"]])

    writer.writerow([])
    writer.writerow(["Forecast Data"])
    writer.writerow(["date", "demand"])
    for row in forecast:
        writer.writerow([row["date"], row["demand"]])

    return output.getvalue().encode("utf-8")


def _pdf_escape(text: str) -> str:
    return text.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")


def _to_pdf_document(lines: list[str]) -> bytes:
    printable_lines = lines[:45]
    content_lines = ["BT", "/F1 11 Tf", "50 780 Td", "14 TL"]
    for line in printable_lines:
        safe = _pdf_escape(line.encode("latin-1", "replace").decode("latin-1"))
        content_lines.append(f"({safe}) Tj")
        content_lines.append("T*")
    content_lines.append("ET")
    content_stream = "\n".join(content_lines).encode("latin-1")

    objects = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Resources << /Font << /F1 5 0 R >> >> /Contents 4 0 R >>",
        f"<< /Length {len(content_stream)} >>\nstream\n".encode("ascii") + content_stream + b"\nendstream",
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
    ]

    pdf = b"%PDF-1.4\n"
    offsets: list[int] = []
    for index, obj in enumerate(objects, start=1):
        offsets.append(len(pdf))
        pdf += f"{index} 0 obj\n".encode("ascii")
        pdf += obj
        pdf += b"\nendobj\n"

    xref_start = len(pdf)
    pdf += f"xref\n0 {len(objects) + 1}\n".encode("ascii")
    pdf += b"0000000000 65535 f \n"
    for offset in offsets:
        pdf += f"{offset:010d} 00000 n \n".encode("ascii")
    pdf += f"trailer\n<< /Size {len(objects) + 1} /Root 1 0 R >>\n".encode("ascii")
    pdf += f"startxref\n{xref_start}\n%%EOF".encode("ascii")
    return pdf


def build_forecast_pdf_bytes(
    product_name: str,
    historical: list[dict[str, Any]],
    forecast: list[dict[str, Any]],
    summary: dict[str, Any],
    created_at: str | None,
) -> bytes:
    lines = [
        "Demand Forecast Report",
        f"Product: {product_name}",
        f"Generated At: {_format_timestamp(created_at)}",
        "",
        f"High-Demand Threshold: {summary['high_demand_threshold']}",
        f"Next Month Forecast: {summary['next_month']['forecast']}",
        f"Next Month High Demand: {summary['next_month']['is_high_demand']}",
        f"Next 5 Months Avg: {summary['next_5_months']['average_forecast']}",
        f"Next 5 Months High-Demand Months: {summary['next_5_months']['months_high_demand']}",
        f"Next 5 Months High Demand: {summary['next_5_months']['is_high_demand']}",
        f"Next 5 Years Growth %: {summary['next_5_years']['growth_percent']}",
        f"Next 5 Years High Demand: {summary['next_5_years']['is_high_demand']}",
        "",
        "Recent Historical Data (last 12 points):",
    ]

    for row in historical[-12:]:
        lines.append(f"- {row['date']} : {row['demand']}")

    lines.append("")
    lines.append("Upcoming Forecast (next 12 points):")
    for row in forecast[:12]:
        lines.append(f"- {row['date']} : {row['demand']}")

    lines.append("")
    lines.append(f"Exported at {datetime.now(UTC).isoformat()}")
    return _to_pdf_document(lines)
