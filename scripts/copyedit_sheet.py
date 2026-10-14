"""Copy-edit pass on scouting-reports.xlsx before a sync.

Usage: python3 scripts/copyedit_sheet.py sheet.xlsx [fixes.json]

Touches the prose cells (Players.Summary, Grades.Sentences, Traits.Sentences) and the form adjective cells.
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


# One wording per form adjective, so every report reads the same way.
TAGS = {
    "cut ride": "Cut ride", "some strikes": "Some strikes", "wide setup": "Wide setup",
    "h3/4": "High 3/4 slot", "3/4": "3/4 slot", "l3/4": "Low 3/4 slot", "low 3/4 arm slot": "Low 3/4 slot",
    "avg strength": "Average strength", "avg balance": "Average balance",
    "projectability good": "Good projectability", "projectability some": "Some projectability",
    "projectability very": "Plus projectability",
    "athleticism excellent": "Excellent athleticism", "athleticism average": "Average athleticism",
    "body language average": "Average body language", "body language good": "Good body language",
    "body language excellent": "Excellent body language",
    "personality fine": "Fine personality", "personality great kid": "Great kid",
}


def tidy_tags(text):
    out = []
    for tag in (x.strip() for x in str(text).split(";")):
        if not tag:
            continue
        tag = TAGS.get(tag.lower(), tag)
        # sentence case: capitalize the first word only, keep abbreviations like FB or 3/4
        words = tag.split(" ")
        tag = " ".join([words[0]] + [w if w.isupper() or any(ch.isdigit() for ch in w) else w.lower()
                                     for w in words[1:]])
        out.append(tag[0].upper() + tag[1:])
    return "; ".join(out)


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
    for sheet in ("Grades", "Traits"):
        ws = wb[sheet]
        head = [c.value for c in ws[1]]
        ci = head.index("Form adjectives")
        for row in ws.iter_rows(min_row=2):
            cell = row[ci]
            if cell.value and row[0].value:
                new = tidy_tags(cell.value)
                if new != cell.value:
                    changes.append((f"{row[0].value}|{row[1].value} tags", cell.value, new))
                    cell.value = new
    wb.save(path)
    for label, old, new in changes:
        print(f"{label}\n  - {old}\n  + {new}")
    print(f"{len(changes)} cells changed")


if __name__ == "__main__":
    main()
