"""
embed_csv.py — Leser Ledelsepod.csv og skriver data-arrayen inn i Ledelsepod.html.

Kjør etter at CSV er oppdatert og vurdert:
  python embed_csv.py
"""

import csv
import json
import os
import re
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

BASE      = os.path.dirname(os.path.abspath(__file__))
CSV_PATH  = os.path.join(BASE, "Ledelsepod.csv")
HTML_PATH = os.path.join(BASE, "Ledelsepod.html")


def main():
    with open(CSV_PATH, encoding="utf-8", newline="") as f:
        rows = list(csv.reader(f))[1:]  # hopp over header

    lines = []
    for r in rows:
        if len(r) < 11:
            r += [""] * (11 - len(r))
        lines.append(json.dumps(r, ensure_ascii=False))

    new_array = "const data = [\n" + ",\n".join(lines) + "\n];"

    with open(HTML_PATH, encoding="utf-8") as f:
        html = f.read()

    new_html, n = re.subn(r"const data = \[.*?\];", new_array, html, flags=re.DOTALL)
    if n != 1:
        print(f"FEIL: forventet 1 treff i HTML, fikk {n}")
        sys.exit(1)

    with open(HTML_PATH, "w", encoding="utf-8") as f:
        f.write(new_html)

    print(f"OK: {len(rows)} episoder skrevet inn i HTML")


if __name__ == "__main__":
    main()
