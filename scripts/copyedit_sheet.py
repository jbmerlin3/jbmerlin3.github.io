"""Copy-edit pass on scouting-reports.xlsx before a sync.

Usage: python3 scripts/copyedit_sheet.py sheet.xlsx [fixes.json]

Touches only the prose cells (Players.Summary, Grades.Sentences, Traits.Sentences).
Always applies the mechanical rules below; fixes.json adds one-off phrase fixes as
{"slug|column-or-row-name": [["old", "new"], ...]} or {"*": [["old", "new"], ...]}.
Prints every change so it can be listed back to Jonathan. Wording stays his.
"""
import json
import re
import sys

import openpyxl

# Misspellings seen in this sheet; safe to fix anywhere.
SPELLING = {
    "conisistently": "consistently",
    "stablizes": "stabilizes",
    "hault": "halt",
    "single handedly": "single-handedly",
    "gap-gap": "gap-to-gap",
}


def mechanical(text):
    t = text.strip()
    t = re.sub(r"\s{2,}", " ", t)
    # "heater.He" -> "heater. He" (but leave 88.2 and T90.0 alone)
    t = re.sub(r"([a-z])\.([A-Z])", r"\1. \2", t)
    t = re.sub(r"\b(\d+) MPH\b", r"\1 mph", t)
    for old, new in SPELLING.items():
        t = re.sub(rf"\b{re.escape(old)}\b", new, t)
    # every note ends as a sentence
    if t and t[-1] not in ".!?":
        t += "."
    return t


def main():
    path = sys.argv[1]
    fixes = json.load(open(sys.argv[2])) if len(sys.argv) > 2 else {}
    wb = openpyxl.load_workbook(path)
    changes = []
    for sheet, col, key in [("Players", "Summary", None), ("Grades", "Sentences", "Pitch / Tool"),
                            ("Traits", "Sentences", "Group")]:
        ws = wb[sheet]
        head = [c.value for c in ws[1]]
        ci = head.index(col)
        for row in ws.iter_rows(min_row=2):
            cell = row[ci]
            if not cell.value or not row[0].value:
                continue
            label = row[0].value + "|" + (str(row[head.index(key)].value) if key else col)
            new = str(cell.value)
            for old, rep in fixes.get(label, []) + fixes.get("*", []):
                new = new.replace(old, rep)
            new = mechanical(new)
            if new != cell.value:
                changes.append((label, cell.value, new))
                cell.value = new
    wb.save(path)
    for label, old, new in changes:
        print(f"{label}\n  - {old}\n  + {new}")
    print(f"{len(changes)} cells changed")


if __name__ == "__main__":
    main()
