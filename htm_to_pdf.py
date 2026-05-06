#!/usr/bin/env python3
"""
htm_to_pdf.py -- Interactive SingleFile .htm to PDF converter.

Usage:
    python htm_to_pdf.py               (launches menu, prompts for input file)
    python htm_to_pdf.py input.htm     (launches menu with file preloaded)
"""

import sys
import os
from pathlib import Path

# Menu helpers

def clear():
    os.system("cls" if os.name == "nt" else "clear")

def header(title="SingleFile HTM to PDF Converter"):
    print("=" * len(title))
    print(f"{title}")
    print("=" * len(title))

def ask_int(prompt, lo, hi):
    """
    Keep asking until the user enters an integer in [lo, hi].
    """
    while True:
        raw = input(prompt).strip()
        if raw.isdigit():
            val = int(raw)
            if lo <= val <= hi:
                return val
        print(f"Please enter a number between {lo} and {hi}.")

def ask_file(preloaded=None):
    clear()
    header("Step 1 of 5 -- Input File")
    if preloaded:
        print(f"Preloaded: {preloaded}\n")
        print("1 -> Use this file")
        print("2 -> Enter a different file")
        choice = ask_int("\nChoice: ", 1, 2)
        if choice == 1:
            return preloaded
    while True:
        path = input("\nPath to .htm / .html file: ").strip('').strip('"')
        p = Path(path).expanduser().resolve()
        if p.exists():
            return p
        print(f"File not found: {p}")

def ask_paper_size():
    clear()
    header("Step 2 of 5 -- Paper Size")
    sizes = ["A4", "A3", "A5", "Letter", "Legal", "Tabloid"]
    descriptions = {
        "A4":      "210 x 297 mm -- most common worldwide",
        "A3":      "297 x 420 mm -- large format",
        "A5":      "148 x 210 mm -- compact / booklet",
        "Letter":  "8.5 x 11 in  -- US standard",
        "Legal":   "8.5 x 14 in  -- US legal",
        "Tabloid": "11 x 17 in   -- US tabloid / ledger",
    }
    print()
    for i, s in enumerate(sizes, 1):
        marker = "(default)" if s == "A4" else ""
        print(f"{i} {s:<8} {descriptions[s]}{marker}")
    choice = ask_int("\nChoice: ", 1, len(sizes))
    return sizes[choice - 1]

def ask_orientation():
    clear()
    header("Step 3 of 5 -- Orientation")
    print()
    print("1 -> Portrait  -- taller than wide (default)")
    print("2 -> Landscape -- wider than tall")
    choice = ask_int("\nChoice: ", 1, 2)
    return choice == 2

def ask_backgrounds():
    clear()
    header("Step 4 of 5 -- Background Graphics")
    print()
    print("Include background colours, images, and gradients in the PDF?")
    print()
    print("1 -> Yes -- full fidelity, matches the original page  (default)")
    print("2 -> No  -- stripped backgrounds, ink-saving / print-friendly")
    choice = ask_int("\nChoice: ", 1, 2)
    return choice == 1

def ask_output(input_path):
    clear()
    header("Step 5 of 5 -- Output File")
    default_out = input_path.with_suffix(".pdf")
    print()
    print(f"Default output path: {default_out}")
    print()
    print("1 -> Use default")
    print("2 -> Enter a custom path")
    choice = ask_int("\nChoice: ", 1, 2)
    if choice == 1:
        return default_out
    while True:
        raw = input("\nOutput path (.pdf): ").strip('').strip('"')
        if raw:
            p = Path(raw).expanduser().resolve()
            if not p.suffix:
                p = p.with_suffix(".pdf")
            return p
        print("Path cannot be empty.")

def confirm_settings(input_path, output_path, paper, landscape, backgrounds):
    clear()
    header("Confirm Settings")
    print()
    print(f"  Input: {input_path}")
    print(f"  Output: {output_path}")
    print(f"  Paper: {paper}")
    print(f"  Layout: {"Landscape" if landscape else "Portrait"}")
    print(f"  Backgrounds: {"Included" if backgrounds else "Excluded"}")
    print()
    print("1 -> Confirm and convert")
    print("2 -> Start over")
    print("3 -> Quit")
    return ask_int("\nChoice: ", 1, 3)

# Core Conversion
def convert(input_path, output_path, paper, landscape, backgrounds):
    try:
        from playwright.sync_api import sync_playwright, TimeoutError as PWTimeout
    except ImportError:
        print("\nERROR: Playwright is not installed.")
        print("Run: pip install playwright && playwright install chromium")
        sys.exit(1)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    file_url = input_path.absolute().as_uri()

    clear()
    header("Converting...")
    print()
    print(f"  Input  : {input_path}")
    print(f"  Output : {output_path}")
    print()

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=[
                "--disable-web-security",
                "--allow-file-access-from-files",
                "--font-render-hinting=none"
            ],
        )
        page = browser.new_context(
            viewport={"width": 1920, "height": 1080}
        ).new_page()
        print("[1/3] Loading page ...", flush=True)
        try:
            page.goto(file_url, wait_until="networkidle", timeout=60000)
        except PWTimeout:
            print("(networkidle timed out -- falling back)", flush=True)
            page.goto(file_url, wait_until="domcontentloaded", timeout=30000)

        page.wait_for_timeout(500)

        page.evaluate(
            "(function(){"
            "  document.querySelectorAll('img').forEach(function(img){"
            "    if (!img.complete) img.loading = 'eager';"
            "  });"
            "})()"
        )

        print("[2/3] Generating PDF ...", flush=True)
        page.pdf(
            path=str(output_path),
            format=paper,
            landscape=landscape,
            margin={"top": "10mm", "right": "10mm", "bottom": "10mm", "left": "10mm"},
            print_background=backgrounds,
            scale=1.0,
        )
        browser.close()

    size_kb = output_path.stat().st_size / 1024
    print(f"[3/3] Conversion complete.")
    print(f"Saved => {output_path}")
    print(f"File size: {size_kb:.2f} KB")
    print()

# Main Loop
def main():
    preloaded = None
    if len(sys.argv) > 1:
        p = Path(sys.argv[1]).expanduser().resolve()
        if p.exists():
            preloaded = p
        else:
            print(f"Warning: file not found: {p}")

    while True:
        input_path = Path(ask_file(preloaded)).expanduser().resolve()
        paper = ask_paper_size()
        landscape = ask_orientation()
        backgrounds = ask_backgrounds()
        output_path = ask_output(input_path)

        action = confirm_settings(input_path, output_path, paper, landscape, backgrounds)

        if action == 1:
            convert(input_path, output_path, paper, landscape, backgrounds)
            sys.exit(0)
        elif action == 2:
            preloaded = input_path
            continue
        elif action == 3:
            print("\nBye!")
            sys.exit(0)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nCancelled.\n")
        sys.exit(0)
