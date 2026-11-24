# Changelog

## 0.1.0

First release.

- `compare`, `score`, `is_match`: comparison of full East Slavic names
  (Ukrainian, Russian, Belarusian) across Cyrillic and Latin script, with an
  explainable result (`Match.explain()`, `Match.to_dict()`).
- Options: `cross_language` (on by default), `diminutives` and
  `gender_insensitive_surnames` (both opt-in).
- `NameIndex` and `dedupe` for searching and de-duplicating lists.
- `keys`: script-independent blocking keys.
- `samename` command line tool: `compare`, `key`, `search`, `dedupe`.
- Lexicon of about 370 given names and about 100 diminutives.
- Benchmark with a development set (`bench/run.py`) and a speed script
  (`bench/speed.py`), and a blind set (`bench/blind.py`) written without
  access to the matcher and run once: precision 0.996, recall 0.987.
