# Publications database

This repository stores publication metadata and formats it for CVs, reports, HTML, Unicode text, and LaTeX. Keep changes small and data-focused; there is no package/build system.

## Sources of truth

- `database.json`: publication records.
- `journals.json`: canonical journal names, abbreviations, and impact factors.
- `database.py`: validation, filtering, and formatting logic.
- `cv.py`, `latex.py`, `iap_list.py`, `report.py`, `report_min_year.py`, and `rscf.py`: command-line output helpers.

## Data conventions

- Preserve the existing JSON array/object style and UTF-8 text. Do not invent missing bibliographic data.
- Valid `Type` values are `Article`, `Proceeding`, `Abstract`, `BookArticle`, `Preprint`, and `Patent`.
- Valid `Language` values are `English`, `English*`, `Russian`, and `Russian*`.
- Write authors as `Surname, I. I.; Surname, I.` (semicolon-separated). Keep established transliterations and author ordering.
- Use a pandas-parseable `Date` such as `YYYY/M/D`; page ranges use an ASCII hyphen, e.g. `123-130`.
- An entry's `Journal` must exactly match a `Journal` key in `journals.json`. Add a journal record when introducing a new journal name.
- Optional fields should be omitted when unknown unless surrounding records deliberately use an empty string for that field.
- Preserve chronological record order. Formatting code also sorts records by `Date`.

## Working with the formatter

The code depends on pandas. `Database` supports `latex`, `html`, `unicode`, or plain formatting and templates including `$a`, `$t`, `$i`, `$DOI`, `$URL`, `$IF`, and `$pn`.

Common commands:

```sh
python latex.py English Article
python cv.py RussianEnglish
python report.py 2026
python report_min_year.py 2020
python rscf.py English
```

## Validation

After data or formatter changes, run:

```sh
jq empty database.json journals.json
python -m py_compile *.py
python -c "from database import Database; Database(languages='All', format='unicode')"
```

Also run the relevant output helper and inspect its text when changing formatting behavior. Treat warnings about invalid types/languages, unknown journals, or extra whitespace as data errors to fix rather than bypass.
