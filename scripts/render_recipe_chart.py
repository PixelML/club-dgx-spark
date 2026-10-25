#!/usr/bin/env python3
"""Render a PixelML recipe chart from validated committed result rows."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


WIDTH = 1200
HEIGHT = 675
BACKGROUND = "#08111F"
PANEL = "#101C2E"
GRID = "#2A3950"
TEXT = "#F7FAFC"
MUTED = "#A9B4C4"
ACCENTS = ["#32D4A4", "#F2B84B", "#6EA8FE", "#F2789F"]


def panel_from_rows(panel: dict, rows: list[dict[str, str]]) -> dict:
    """Builds one display panel without accepting values from the style spec."""
    metric_rows = [row for row in rows if row.get("metric") == panel["metric"]]
    if not metric_rows:
        raise ValueError(f"summary has no rows for metric {panel['metric']}")
    values = [float(row["tok_s"]) for row in metric_rows]
    if any(value <= 0 for value in values):
        raise ValueError(f"metric {panel['metric']} contains non-positive tok/s")

    divisor = float(panel.get("x_divisor", 1))
    labels = []
    for row in metric_rows:
        x_value = float(row["x"]) / divisor
        label = f"{x_value:g}"
        labels.append(f"{panel.get('x_prefix', '')}{label}{panel.get('x_suffix', '')}")
    return {
        "title": panel["title"],
        "y_label": panel["y_label"],
        "x": labels,
        "series": [
            {
                "label": panel["series_label"],
                "values": values,
                "color": panel.get("color", ACCENTS[0]),
            }
        ],
    }


def font(size: int, bold: bool = False) -> ImageFont.ImageFont:
    names = [
        "/System/Library/Fonts/Supplemental/Arial Bold.ttf" if bold else "/System/Library/Fonts/Supplemental/Arial.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    ]
    for name in names:
        if Path(name).exists():
            return ImageFont.truetype(name, size=size)
    return ImageFont.load_default()


def draw_panel(draw: ImageDraw.ImageDraw, box: tuple[int, int, int, int], panel: dict) -> None:
    left, top, right, bottom = box
    draw.rounded_rectangle(box, radius=18, fill=PANEL, outline=GRID, width=2)
    draw.text((left + 24, top + 20), panel["title"], font=font(22, True), fill=TEXT)
    draw.text((left + 24, top + 52), panel["y_label"], font=font(14), fill=MUTED)

    plot_left, plot_top = left + 72, top + 92
    plot_right, plot_bottom = right - 28, bottom - 62
    all_values = [float(value) for series in panel["series"] for value in series["values"]]
    maximum = max(all_values) * 1.12 if all_values else 1.0
    if maximum <= 0:
        maximum = 1.0

    for index in range(5):
        y = plot_bottom - (plot_bottom - plot_top) * index / 4
        value = maximum * index / 4
        draw.line((plot_left, y, plot_right, y), fill=GRID, width=1)
        draw.text((left + 12, y - 9), f"{value:.0f}", font=font(13), fill=MUTED)

    labels = [str(value) for value in panel["x"]]
    x_positions = [
        plot_left + (plot_right - plot_left) * index / max(1, len(labels) - 1)
        for index in range(len(labels))
    ]
    for x, label in zip(x_positions, labels, strict=True):
        draw.text((x - 20, plot_bottom + 14), label, font=font(13), fill=MUTED)

    for series_index, series in enumerate(panel["series"]):
        color = series.get("color", ACCENTS[series_index % len(ACCENTS)])
        points = []
        for x, value in zip(x_positions, series["values"], strict=True):
            y = plot_bottom - (plot_bottom - plot_top) * float(value) / maximum
            points.append((x, y))
        if len(points) > 1:
            draw.line(points, fill=color, width=4)
        for (x, y), value in zip(points, series["values"], strict=True):
            draw.ellipse((x - 6, y - 6, x + 6, y + 6), fill=color)
            draw.text((x - 18, y - 27), f"{float(value):g}", font=font(13, True), fill=color)

    legend_x = plot_left
    legend_y = bottom - 30
    for series_index, series in enumerate(panel["series"]):
        color = series.get("color", ACCENTS[series_index % len(ACCENTS)])
        draw.rectangle((legend_x, legend_y, legend_x + 14, legend_y + 14), fill=color)
        draw.text((legend_x + 20, legend_y - 2), series["label"], font=font(13), fill=TEXT)
        legend_x += 24 + int(draw.textlength(series["label"], font=font(13))) + 24


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--spec", required=True, type=Path)
    parser.add_argument("--data", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()

    spec = json.loads(args.spec.read_text(encoding="utf-8"))
    with args.data.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    if not rows:
        raise SystemExit("summary data is empty")
    image = Image.new("RGB", (WIDTH, HEIGHT), BACKGROUND)
    draw = ImageDraw.Draw(image)

    draw.text((46, 30), "PIXELML", font=font(20, True), fill="#32D4A4")
    draw.text((46, 66), spec["title"], font=font(34, True), fill=TEXT)
    draw.text((46, 112), spec["subtitle"], font=font(17), fill=MUTED)

    panels = [panel_from_rows(panel, rows) for panel in spec["panels"]]
    gap = 20
    margin = 46
    panel_top = 160
    panel_bottom = 610
    panel_width = (WIDTH - 2 * margin - gap * (len(panels) - 1)) // len(panels)
    for index, panel in enumerate(panels):
        left = margin + index * (panel_width + gap)
        draw_panel(draw, (left, panel_top, left + panel_width, panel_bottom), panel)

    draw.text((46, 638), spec["footer"], font=font(13), fill=MUTED)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    image.save(args.output, optimize=True)


if __name__ == "__main__":
    main()
