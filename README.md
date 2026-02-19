
---
# <center> **_SQLite DB Comparator_**
---
**Beautiful, rich-text terminal based comparison tool for SQLite databases**

Quickly see schema differences, missing tables, row count mismatches and data changes between two `.db` / `.sqlite` files.

## ✨ Features

- Table existence comparison (tables only in DB1 / DB2)
- Schema difference detection (columns added/removed, type changes)
- Row count comparison
- Data difference detection (added / removed / changed rows)
- Normalization of values (handles whitespace, floating-point precision)
- Very readable **rich** terminal output with colors, panels, tables & trees
- File picker GUI when no command-line arguments are provided
- Detailed side-by-side row difference viewer (for mis-matched selected tables)

---

## Requirements

- Python 3.8+
- [rich](https://github.com/Textualize/rich) — for beautiful terminal output

```bash
pip install rich
```
---
## Installation

```bash
# Recommended: install directly from GitHub
pipx install git+https://github.com/YOUR-USERNAME/sqlite-db-comparator.git

# or clone & install locally
git clone https://github.com/YOUR-USERNAME/sqlite-db-comparator.git
cd sqlite-db-comparator
pip install -e .
```
---
## Usage

```bash
# Interactive mode (recommended for most users)
sqlite-db-compare

# or specify files directly
sqlite-db-compare database-v1.db database-v2.db

# or using python module style
python -m sqlite_comparator path/to/db1.db path/to/db2.db
```
---
## Example output

Identical databases:

```
┌──────────────────────────────────────┐
│     SQLite Database Comparison       │
│           Report                     │
└──────────────────────────────────────┘

Database 1:  prod-2025-12-15.db
Database 2:  prod-2025-12-16.db

               ✓ DATABASES ARE IDENTICAL
```

Databases with differences:

```
Only in DB1      users_old_archive
Only in DB2      audit_log_2025

Common tables with differences:
  • orders        (schema changed)
  • products      (12 rows added)
  • transactions  (price column type changed: REAL → TEXT)
  With additional clear details!

```
<!--
## Roadmap / Possible future improvements

- [ ] Export results to JSON / Markdown / HTML
- [ ] Primary key aware row matching (instead of full row hash)
- [ ] Ignore-list for tables / columns
- [ ] `--quiet` / `--only-summary` modes
- [ ] CI-friendly exit code & diff-like output -->

---

### Made with ❤️ and [rich](https://github.com/Textualize/rich)

```
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣠⣶⣾⡇⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢸⣿⣿⡟⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣸⣿⣿⣦⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣠⣾⣿⣿⣿⣿⠆⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣾⣿⣿⣿⣿⣿⠏⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢸⣿⣿⠿⠋⠛⠻⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣸⠉⠉⠀⠀⠀⢸⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⡰⠃⠀⠀⠀⠀⠀⢸⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢸⠃⠀⠀⠀⠀⠀⠀⢸⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢀⡇⠀⠀⠀⠀⠀⠀⠀⢸⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣸⠁⠀⠀⠀⠀⠀⠀⠀⣾⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣠⠔⠊⠁⠀⠀⠀⠀⠀⠀⠀⠀⠈⠑⢦⡀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢀⡴⠊⠁⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠙⢦⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⢀⡔⠉⠀⠀⠀⠀     ⣠⣴⣾⣿⡇⠀⠀⠀⠀⠀⠀⠀⠱⣄⠀⠀⠀⠀⠀⢀⣀⣀⣀⣀⣤⣤⣤⡀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⢠⠋⣠⣦⣟⣻⣦    ⣼⣿⣿⣿⣿⠃⠀⠀⠀⠀⠀⠀⠀⠀⠀⠈⢶⠒⠛⠉⠉⠀⠀⠀⠀⠀⣹⣿⣿⣿⣦⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⢸⠀⡏⠿⣎⣿⠏⠹   ⠟⠿⠟⠁⠀⠀⠀⠀⠀⢀⣴⣶⣶⣤⠀⠈⠃⠀⠀⠀⠀⠀⠀⠀⢰⣿⣿⣿⣿⣿⣷⡀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠈⡆⠛⠷⠟⢻⣷⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢰⣿⣿⣿⣿⣿⡇⠀⠀⠀⠀⠀⠀⠀⣀⡠⠜⠛⠛⢯⣙⠿⣿⣷⣄⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠹⡄⠀⠀⢸⣿⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢿⣿⣿⣿⣿⡿⠃⠀⠀⡀⠀⣠⠴⠊⠁⠀⠀⠀⠀⠀⠈⠓⢽⣿⣿⣷
⠀⠀⠀⠀⠀⠀⠀⠀⠀⢳⡀⠀⠘⢿⣿⣿⣿⣷⣆⠀⠀⠀⠀⠀⠀⠈⠻⢿⠿⠛⠡⣄⠀⢠⠟⠉⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠙⢿⣿
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠳⡀⠀⠀⠀⠀⠀⠸⣿⣤⣤⡀⠀⠀⠀⣤⣲⣖⠢⡀⠀⠀⠀⡜⠀⠀⠀⠀⠀⠀⠀⣀⣤⢄⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠙⣦⡀⠀⠀⠀⠀⠈⠉⠻⣿⣤⣤⣿⣶⠆⣩⠿⠅⠀⠀⡜⠁⠀⠀⠀⢀⡤⠖⠋⠀⣾⠈⣧⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢠⠏⠀⠑⠦⢀⠀⠀⠀⠀⠙⠻⣋⣩⣭⣶⣞⠋⠀⢀⡞⠀⠀⠀⣠⠖⠉⠀⠀⠀⠀⢻⡀⢸⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢠⠏⠀⠀⠀⠀⠀⠀⠀⠐⢲⡤⠀⠈⠉⠉⠁⣀⡠⠴⠋⠀⠀⡠⠎⠁⠀⢀⡠⠄⠀⠀⠸⡀⢸⠄⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⢠⠏⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠈⢙⡏⠉⠉⠉⠁⠀⠀⠀⣠⠞⠁⢀⣤⠞⣉⠄⠀⢀⡠⢔⡳⠋⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⢀⡎⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠈⠳⣄⠀⠀⠀⠀⠀⢰⠁⠀⠀⠛⠐⠋⣀⠤⣒⡭⠒⠋⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⡼⠀⠀⠀⠀⠀⠀⡀⠀⠀⠀⠀⠀⠀⠀⠀⠈⢦⠀⠀⠀⠀⠈⢦⡀⠀⢠⠴⠟⠚⠉⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⢰⠁⠀⠀⠀⠀⠀⢸⡇⠀⠀⠀⣾⣇⠀⠀⠀⠀⠈⢷⠀⠀⢀⡴⠋⠀⠀⠈⢇⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⡏⠀⠀⠀⠀⠀⠀⢸⡗⠀⠀⠀⠸⣿⠀⠀⠀⠀⠀⠀⢧⠀⢏⠀⠈⢳⡶⠟⠋⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⣸⠀⠀⠀⠀⠀⠀⠀⠀⠁⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠘⡄⠀⣳⠄⠀⡃⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⡏⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢧⡞⢁⡴⠋⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠻⣗⣒⠒⠛⠁⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠙⠓⠤⣄⡀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⣠⠤⠖⠛⣛⡻⢶⣄⠀⠀⠀⠀⣀⣀⡀⠀⠀⠀⠀⢀⡀⠀⠀⠀⠀⠀⠀⢠⣤⣤⣄⣀⣀⣈⣱⡆⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠉⠉⠉⠉⠉⠗⠚⠹⣤⡖⠊⠉⠻⠿⠋⠑⢦⣄⣴⠿⣽⣿⠒⠲⣤⣤⣀⣈⡷⠤⠤⠵⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
```
