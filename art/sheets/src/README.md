Unit sprite sheets, named `<faction>_<unit>_t<tier>.png` (e.g. `mutant_leaper_t1.png`).
Magenta-background sheets are cut and normalized; already-cleaned transparent sheets are kept as they are.
Then run, from the repo root:

    python3 tools/sheets.py && python3 tools/embed_sheets.py

See "Unit sprite sheets" in the main README for the sheet format.
