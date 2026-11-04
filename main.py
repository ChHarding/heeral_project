"""ContrastCheck: check text contrast in a Figma file.

The app reads a Figma file through the REST API, finds text layers, matches
them with the nearest supported solid ancestor background, and writes a WCAG
report. Complex backgrounds are sent to manual review instead of receiving a
misleading score.
"""

from __future__ import annotations

import argparse
import os
from pathlib import Path
from urllib.parse import urlparse

import requests


DEFAULT_FILE_KEY = "Rznp5ERB6Jr2p4Xneg8r7g"
WCAG_AA_THRESHOLD = 4.5
BACKGROUND_NODE_TYPES = {"FRAME", "COMPONENT", "INSTANCE", "SECTION", "COMPONENT_SET"}


def fetch_figma_file(file_key: str, token: str) -> dict | None:
    """Fetch a Figma file, returning decoded JSON or ``None`` on failure."""
    print("\nConnecting to Figma API...")
    try:
        response = requests.get(
            f"https://api.figma.com/v1/files/{file_key}",
            headers={"X-Figma-Token": token},
            timeout=30,
        )
        response.raise_for_status()
        data = response.json()
    except requests.Timeout:
        print("Error: The Figma request timed out. Check your connection and try again.")
        return None
    except requests.RequestException as error:
        status = getattr(error.response, "status_code", None)
        if status in (401, 403):
            print("Error: Figma rejected the token or file access permission.")
        elif status == 404:
            print("Error: The Figma file was not found. Check the URL or file key.")
        else:
            print(f"Error: Could not connect to Figma ({error}).")
        return None
    except ValueError:
        print("Error: Figma returned data that could not be read as JSON.")
        return None
    print("Connected successfully!")
    return data


def convert_figma_color_to_rgb(color: dict) -> tuple[int, int, int]:
    """Convert Figma's zero-to-one RGB values to integer RGB values."""
    return tuple(round(color[channel] * 255) for channel in ("r", "g", "b"))


def get_background_from_node(node: dict) -> tuple[tuple[int, int, int] | None, str | None]:
    """Return a solid container background or the reason it is unsupported."""
    if node.get("type") not in BACKGROUND_NODE_TYPES:
        return None, None
    fills = [fill for fill in node.get("fills", []) if fill.get("visible", True)]
    if not fills:
        return None, None
    if node.get("opacity", 1) < 1 or any(fill.get("opacity", 1) < 1 for fill in fills):
        return None, "transparent background"
    if len(fills) != 1 or fills[0].get("type") != "SOLID":
        return None, "gradient, image, or multiple background fills"
    color = fills[0].get("color")
    if not color:
        return None, "solid background has no readable color"
    return convert_figma_color_to_rgb(color), None


def get_text_color(node: dict) -> tuple[tuple[int, int, int] | None, str | None]:
    """Return a text layer's single opaque solid foreground color."""
    fills = [fill for fill in node.get("fills", []) if fill.get("visible", True)]
    if not fills:
        return None, "text has no visible fill"
    if node.get("opacity", 1) < 1 or any(fill.get("opacity", 1) < 1 for fill in fills):
        return None, "transparent text"
    if len(fills) != 1 or fills[0].get("type") != "SOLID":
        return None, "text uses a gradient, image, or multiple fills"
    color = fills[0].get("color")
    if not color:
        return None, "text fill has no readable color"
    return convert_figma_color_to_rgb(color), None


def extract_text_nodes(
    node: dict,
    results: list[dict] | None = None,
    background: tuple[int, int, int] | None = None,
    background_source: str | None = None,
    background_issue: str | None = None,
) -> list[dict]:
    """Recursively find text and track its nearest ancestor background."""
    if results is None:
        results = []

    node_background, node_issue = get_background_from_node(node)
    if node_background is not None:
        background = node_background
        background_source = node.get("name") or node.get("id") or "unnamed container"
        background_issue = None
    elif node_issue is not None:
        background = None
        background_source = node.get("name") or node.get("id") or "unnamed container"
        background_issue = node_issue

    if node.get("type") == "TEXT":
        foreground, foreground_issue = get_text_color(node)
        issue = foreground_issue or background_issue
        if issue is None and background is None:
            issue = "no supported solid ancestor background found"
        results.append(
            {
                "text": node.get("characters", "")[:80],
                "node_id": node.get("id", "unknown"),
                "fg_color": foreground,
                "bg_color": background,
                "bg_source": background_source,
                "review_reason": issue,
            }
        )

    for child in node.get("children", []):
        extract_text_nodes(
            child, results, background, background_source, background_issue
        )
    return results


def relative_luminance(rgb: tuple[int, int, int]) -> float:
    """Calculate WCAG relative luminance for an RGB color."""
    converted = []
    for channel in rgb:
        value = channel / 255.0
        converted.append(
            value / 12.92
            if value <= 0.04045
            else ((value + 0.055) / 1.055) ** 2.4
        )
    red, green, blue = converted
    return 0.2126 * red + 0.7152 * green + 0.0722 * blue


def calculate_contrast_ratio(
    first_color: tuple[int, int, int], second_color: tuple[int, int, int]
) -> float:
    """Calculate the WCAG contrast ratio between two RGB colors."""
    first = relative_luminance(first_color)
    second = relative_luminance(second_color)
    return (max(first, second) + 0.05) / (min(first, second) + 0.05)


def build_report_lines(text_nodes: list[dict]) -> tuple[list[str], dict[str, int]]:
    """Create readable result lines and counts without duplicate entries."""
    lines = []
    counts = {"passed": 0, "failed": 0, "manual_review": 0}
    seen = set()
    for node in text_nodes:
        text = node["text"].strip() or "(empty text)"
        key = (text, node["fg_color"], node["bg_color"], node["review_reason"])
        if key in seen:
            continue
        seen.add(key)

        if node["review_reason"] or node["fg_color"] is None or node["bg_color"] is None:
            counts["manual_review"] += 1
            reason = node["review_reason"] or "color information is incomplete"
            lines.append(f"MANUAL REVIEW | {text} | node {node['node_id']} | reason: {reason}")
            continue

        ratio = calculate_contrast_ratio(node["fg_color"], node["bg_color"])
        status = "PASS" if ratio >= WCAG_AA_THRESHOLD else "FAIL"
        counts["passed" if status == "PASS" else "failed"] += 1
        lines.append(
            f"{status} | ratio {ratio:.2f} | {text} | node {node['node_id']} | "
            f"FG {node['fg_color']} | BG {node['bg_color']} ({node['bg_source']})"
        )
    return lines, counts


def write_report(
    text_nodes: list[dict], file_key: str, output_path: str | Path = "report.txt"
) -> bool:
    """Print and save a contrast report, returning whether saving succeeded."""
    lines, counts = build_report_lines(text_nodes)
    header = ["CONTRASTCHECK REPORT", f"File: {file_key}", "=" * 80]
    summary = (
        f"SUMMARY: {counts['passed']} passed, {counts['failed']} failed, "
        f"{counts['manual_review']} manual review"
    )
    display_lines = lines or ["No text nodes found."]
    print("\n" + "\n".join(header + display_lines + ["=" * 80, summary]) + "\n")
    try:
        Path(output_path).write_text(
            "\n".join(header + display_lines + ["=" * 80, summary]) + "\n",
            encoding="utf-8",
        )
    except OSError as error:
        print(f"Error: The report could not be saved ({error}).")
        return False
    print(f"Report saved to {output_path}")
    return True


def parse_file_key(value: str) -> str:
    """Accept either a Figma file key or a standard Figma design URL."""
    value = value.strip()
    if not value:
        raise ValueError("The Figma file key or URL cannot be empty.")
    if "://" not in value:
        return value
    parsed = urlparse(value)
    if parsed.netloc not in {"figma.com", "www.figma.com"}:
        raise ValueError("Please provide a figma.com file URL.")
    parts = [part for part in parsed.path.split("/") if part]
    if len(parts) < 2 or parts[0] not in {"file", "design"}:
        raise ValueError("The URL does not look like a Figma file or design URL.")
    return parts[1]


def parse_arguments() -> argparse.Namespace:
    """Parse command-line options for the Figma file and report location."""
    parser = argparse.ArgumentParser(
        description="Check text contrast in a Figma file using WCAG AA guidance."
    )
    parser.add_argument(
        "figma_file",
        nargs="?",
        default=os.environ.get("FIGMA_FILE_KEY", DEFAULT_FILE_KEY),
        help="Figma file URL or file key (defaults to FIGMA_FILE_KEY)",
    )
    parser.add_argument(
        "--output", default="report.txt", help="saved report path (default: report.txt)"
    )
    return parser.parse_args()


def main() -> int:
    """Run the complete ContrastCheck command-line workflow."""
    print("=" * 60)
    print("  CONTRASTCHECK - Figma Accessibility Checker")
    print("  HCI 584 - Heeral Chumber")
    print("=" * 60)
    arguments = parse_arguments()
    token = os.environ.get("FIGMA_TOKEN", "").strip()
    if not token:
        print("Error: FIGMA_TOKEN is missing.")
        print("Create a Figma token and set it as an environment variable before running.")
        return 1

    try:
        file_key = parse_file_key(arguments.figma_file)
    except ValueError as error:
        print(f"Error: {error}")
        return 1
    figma_data = fetch_figma_file(file_key, token)
    if figma_data is None:
        return 1
    document = figma_data.get("document")
    if not isinstance(document, dict):
        print("Error: The Figma response does not contain a readable document.")
        return 1

    print(f"\nFile name: {figma_data.get('name', 'Unknown')}")
    print(f"Last modified: {figma_data.get('lastModified', 'Unknown')}")
    text_nodes = []
    for page in document.get("children", []):
        print(f"Scanning page: {page.get('name', 'Unnamed page')}")
        extract_text_nodes(page, text_nodes)
    print(f"Found {len(text_nodes)} text node(s) across all pages.")
    return 0 if write_report(text_nodes, file_key, arguments.output) else 1


if __name__ == "__main__":
    raise SystemExit(main())
