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
    # Valider at CSV-filen finnes og ikke er tom
    if not os.path.exists(CSV_PATH):
        print(f"FEIL: {CSV_PATH} finnes ikke")
        sys.exit(1)

    with open(CSV_PATH, encoding="utf-8", newline="") as f:
        all_rows = list(csv.reader(f))

    if len(all_rows) < 2:
        print("FEIL: CSV-filen mangler header eller inneholder ingen episoder")
        sys.exit(1)

    header, rows = all_rows[0], all_rows[1:]

    # Valider at headeren har forventet antall kolonner
    if len(header) < 11:
        print(f"FEIL: CSV-header har {len(header)} kolonner, forventet minst 11")
        sys.exit(1)

    lines = []
    for i, r in enumerate(rows, start=2):  # start=2 siden rad 1 er header
        if len(r) < 11:
            r += [""] * (11 - len(r))
        try:
            lines.append(json.dumps(r, ensure_ascii=False))
        except (ValueError, TypeError) as e:
            print(f"FEIL: kunne ikke serialisere rad {i}: {e}")
            sys.exit(1)

    new_array = "const data = [\n" + ",\n".join(lines) + "\n];"

    if not os.path.exists(HTML_PATH):
        print(f"FEIL: {HTML_PATH} finnes ikke")
        sys.exit(1)

    with open(HTML_PATH, encoding="utf-8") as f:
        html = f.read()

    new_html, n = re.subn(r"const data = \[.*?\];", new_array, html, flags=re.DOTALL)
    if n != 1:
        print(f"FEIL: forventet 1 treff på 'const data' i HTML, fikk {n}")
        sys.exit(1)

    with open(HTML_PATH, "w", encoding="utf-8") as f:
        f.write(new_html)

    print(f"OK: {len(rows)} episoder skrevet inn i HTML")


if __name__ == "__main__":
    main()
