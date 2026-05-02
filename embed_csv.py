"""
embed_csv.py — Leser Ledelsepod.csv og Ledelsepod_arkiv.csv og skriver
data-arrayene inn i Ledelsepod.html.

Kjør etter at CSV er oppdatert og vurdert:
  python embed_csv.py
"""

import csv
import json
import os
import re
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

BASE         = os.path.dirname(os.path.abspath(__file__))
CSV_PATH     = os.path.join(BASE, "Ledelsepod.csv")
ARCHIVE_PATH = os.path.join(BASE, "Ledelsepod_arkiv.csv")
HTML_PATH    = os.path.join(BASE, "Ledelsepod.html")


def csv_to_js_array(rows, var_name):
    lines = []
    for i, r in enumerate(rows):
        if len(r) < 11:
            r = r + [""] * (11 - len(r))
        try:
            lines.append(json.dumps(r, ensure_ascii=False))
        except (ValueError, TypeError) as e:
            print(f"FEIL: kunne ikke serialisere rad i {var_name}, rad {i+2}: {e}")
            sys.exit(1)
    return f"const {var_name} = [\n" + ",\n".join(lines) + "\n];"


def main():
    # Valider at hoved-CSV finnes og ikke er tom
    if not os.path.exists(CSV_PATH):
        print(f"FEIL: {CSV_PATH} finnes ikke")
        sys.exit(1)

    with open(CSV_PATH, encoding="utf-8", newline="") as f:
        all_rows = list(csv.reader(f))

    if len(all_rows) < 2:
        print("FEIL: CSV-filen mangler header eller inneholder ingen episoder")
        sys.exit(1)

    header, rows = all_rows[0], all_rows[1:]

    if len(header) < 11:
        print(f"FEIL: CSV-header har {len(header)} kolonner, forventet minst 11")
        sys.exit(1)

    # Bygg hoved-array
    new_data_array = csv_to_js_array(rows, "data")

    # Bygg arkiv-array — graceful hvis filen mangler eller er tom
    archive_rows = []
    if os.path.exists(ARCHIVE_PATH):
        with open(ARCHIVE_PATH, encoding="utf-8", newline="") as f:
            arch_all = list(csv.reader(f))
        if len(arch_all) >= 2:
            archive_rows = arch_all[1:]
    new_archive_array = csv_to_js_array(archive_rows, "archiveData")

    if not os.path.exists(HTML_PATH):
        print(f"FEIL: {HTML_PATH} finnes ikke")
        sys.exit(1)

    with open(HTML_PATH, encoding="utf-8") as f:
        html = f.read()

    new_html, n1 = re.subn(r"const data = \[.*?\];", new_data_array, html, flags=re.DOTALL)
    if n1 != 1:
        print(f"FEIL: forventet 1 treff på 'const data' i HTML, fikk {n1}")
        sys.exit(1)

    new_html, n2 = re.subn(r"const archiveData = \[.*?\];", new_archive_array, new_html, flags=re.DOTALL)
    if n2 != 1:
        print(f"FEIL: forventet 1 treff på 'const archiveData' i HTML, fikk {n2}")
        sys.exit(1)

    with open(HTML_PATH, "w", encoding="utf-8") as f:
        f.write(new_html)

    print(f"OK: {len(rows)} episoder + {len(archive_rows)} arkiverte skrevet inn i HTML")


if __name__ == "__main__":
    main()
