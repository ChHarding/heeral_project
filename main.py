# main.py
# ContrastCheck - Figma Accessibility Checker
# Heeral Chumber - HCI 584

import os
import requests

# ── 1. CONFIG ──────────────────────────────────────────────────
FIGMA_TOKEN = os.environ.get("FIGMA_TOKEN", "")
FILE_KEY = os.environ.get("FIGMA_FILE_KEY", "Rznp5ERB6Jr2p4Xneg8r7g")

# ── 2. FETCH FIGMA FILE ────────────────────────────────────────
def fetch_figma_file(file_key, token):
    """Fetch the full Figma file JSON via the REST API."""
    url = f"https://api.figma.com/v1/files/{file_key}"
    headers = {"X-Figma-Token": token}
    print(f"\nConnecting to Figma API...")
    response = requests.get(url, headers=headers, timeout=30)
    if response.status_code != 200:
        print(f"Error: {response.status_code} - {response.text}")
        return None
    print("Connected successfully!")
    return response.json()

# ── 3. EXTRACT COLORS ──────────────────────────────────────────
def extract_text_nodes(node, results=None, depth=0):
    """Recursively walk the Figma node tree and find text nodes."""
    if results is None:
        results = []
    if node.get("type") == "TEXT":
        text_content = node.get("characters", "")
        fills = node.get("fills", [])
        fg_color = None
        if fills and fills[0].get("type") == "SOLID":
            c = fills[0]["color"]
            fg_color = (
                int(c["r"] * 255),
                int(c["g"] * 255),
                int(c["b"] * 255)
            )
        # get background from parent frame (stored separately)
        results.append({
            "text":     text_content[:40],  # truncate long text
            "fg_color": fg_color,
            "node_id":  node.get("id")
        })

    for child in node.get("children", []):
        extract_text_nodes(child, results, depth + 1)

    return results

def extract_bg_colors(node, bg_map=None):
    """Walk tree and record background fill for each FRAME/RECTANGLE."""
    if bg_map is None:
        bg_map = {}
    if node.get("type") in ("FRAME", "RECTANGLE", "COMPONENT"):
        fills = node.get("fills", [])
        if fills and fills[0].get("type") == "SOLID":
            c = fills[0]["color"]
            bg_map[node.get("id")] = (
                int(c["r"] * 255),
                int(c["g"] * 255),
                int(c["b"] * 255)
            )
    for child in node.get("children", []):
        extract_bg_colors(child, bg_map)
    return bg_map

# ── 4. CONTRAST MATH (WCAG) ────────────────────────────────────
def relative_luminance(rgb):
    """Calculate relative luminance of an RGB color (WCAG formula)."""
    result = []
    for channel in rgb:
        c = channel / 255.0
        if c <= 0.04045:
            result.append(c / 12.92)
        else:
            result.append(((c + 0.055) / 1.055) ** 2.4)
    r, g, b = result
    return 0.2126 * r + 0.7152 * g + 0.0722 * b

def contrast_ratio(rgb1, rgb2):
    """Calculate contrast ratio between two RGB colors."""
    l1 = relative_luminance(rgb1)
    l2 = relative_luminance(rgb2)
    lighter = max(l1, l2)
    darker  = min(l1, l2)
    return (lighter + 0.05) / (darker + 0.05)

# ── 5. REPORT ──────────────────────────────────────────────────
def print_report(text_nodes, bg_color=(255, 255, 255)):
    """Print a contrast check report for all text nodes."""
    print("\n" + "=" * 60)
    print("  CONTRASTCHECK REPORT")
    print("  File: " + FILE_KEY)
    print("=" * 60)

    if not text_nodes:
        print("No text nodes found in this file.")
        return

    passed = 0
    failed = 0
    seen = set()  # track duplicates

    # save results to a file too
    report_lines = []

    for node in text_nodes:
        fg = node["fg_color"]
        text = node["text"].strip() if node["text"].strip() else "(empty text)"

        if fg is None:
            continue

        # skip duplicates
        key = (text[:40], fg)
        if key in seen:
            continue
        seen.add(key)

        ratio = contrast_ratio(fg, bg_color)
        status = "PASS" if ratio >= 4.5 else "FAIL"

        if ratio >= 4.5:
            passed += 1
        else:
            failed += 1

        line = f"{status} | ratio {ratio:.2f} | {text[:40]} | FG {fg}"
        print(line)
        report_lines.append(line)

    # print summary
    print("\n" + "=" * 60)
    print(f"  SUMMARY: {passed} passed, {failed} failed")
    print("=" * 60 + "\n")

    # save to file
    with open("report.txt", "w") as f:
        f.write("CONTRASTCHECK REPORT\n")
        f.write("=" * 60 + "\n")
        for line in report_lines:
            f.write(line + "\n")
        f.write("=" * 60 + "\n")
        f.write(f"SUMMARY: {passed} passed, {failed} failed\n")
    print("Report saved to report.txt")

# ── 6. MAIN ────────────────────────────────────────────────────
def main():
    print("=" * 60)
    print("  CONTRASTCHECK - Figma Accessibility Checker")
    print("  HCI 584 - Heeral Chumber")
    print("=" * 60)

    if not FIGMA_TOKEN:
        print("Missing FIGMA_TOKEN environment variable.")
        print("Set it before running the program so the token is not stored in source code.")
        return

    # fetch file
    figma_data = fetch_figma_file(FILE_KEY, FIGMA_TOKEN)
    if not figma_data:
        print("Could not fetch Figma file. Check your token and file key.")
        return

    print(f"\nFile name : {figma_data['name']}")
    print(f"Last modified: {figma_data['lastModified']}")

    # walk the document tree
    document = figma_data["document"]
    text_nodes = []
    for page in document.get("children", []):
        print(f"\nScanning page: {page['name']}")
        extract_text_nodes(page, text_nodes)

    print(f"Found {len(text_nodes)} text node(s) across all pages.")

    # run contrast check against white background (default for v1)
    print_report(text_nodes, bg_color=(255, 255, 255))

if __name__ == "__main__":
    main()
