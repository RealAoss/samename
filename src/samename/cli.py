"""Command line interface:  ``samename compare | key | search | dedupe``."""

from __future__ import annotations

import argparse
import csv
import json
import sys

from . import __version__
from .index import NameIndex, dedupe
from .match import DEFAULT_THRESHOLD, compare, keys


def _fail(message: str):
    """Report a usage error: message on stderr, exit code 2."""
    print(f"samename: {message}", file=sys.stderr)
    raise SystemExit(2)


def _read_names(path: str, column):
    """Read names from a text file (one per line) or a CSV / TSV column.

    A column given by name skips the header row; a column given by number
    (0-based) reads every row, so it suits files without a header.
    """
    try:
        with open(path, encoding="utf-8-sig", newline="") as fh:
            if column is None and not path.lower().endswith((".csv", ".tsv")):
                return [line.strip() for line in fh if line.strip()]
            dialect = "excel-tab" if path.lower().endswith(".tsv") else "excel"
            rows = [r for r in csv.reader(fh, dialect) if r]
    except OSError as exc:
        _fail(f"cannot read {path!r}: {exc.strerror or exc}")
    except UnicodeDecodeError:
        _fail(f"{path!r} is not UTF-8 text")
    if not rows:
        return []
    header = rows[0]
    width = max(len(r) for r in rows)
    if column is None:
        if width > 1:
            _fail(f"{path!r} has {width} columns; choose one with --column (header is {header})")
        col = 0
    elif column.isdigit():
        col = int(column)
        if col >= width:
            _fail(f"column {col} is out of range; {path!r} has {width} column(s), numbered from 0")
    elif column in header:
        col = header.index(column)
    else:
        _fail(f"column {column!r} not found; header is {header}")
    body = rows[1:] if (column is not None and not column.isdigit()) else rows
    return [r[col].strip() for r in body if len(r) > col and r[col].strip()]


def _add_options(parser, compare_options=True):
    parser.add_argument("--no-cross-language", action="store_true",
                        help="do not equate Ukrainian / Russian / Belarusian forms of a given name")
    parser.add_argument("--diminutives", action="store_true",
                        help="accept short forms for full names (Sasha = Oleksandr)")
    if compare_options:
        parser.add_argument("--gender-insensitive-surnames", action="store_true",
                            help="accept Ivanov / Ivanova as the same surname")


def _options(args, compare_options=True) -> dict:
    out = {"cross_language": not args.no_cross_language, "diminutives": args.diminutives}
    if compare_options:
        out["gender_insensitive_surnames"] = args.gender_insensitive_surnames
    return out


def main(argv=None) -> int:
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8")
        except (AttributeError, ValueError):
            pass

    p = argparse.ArgumentParser(
        prog="samename",
        description="Match East Slavic personal names across Cyrillic, Latin romanizations and languages.",
        epilog="Exit codes: 0 = match / hits found, 1 = no match / no hits, 2 = usage or file error.")
    p.add_argument("--version", action="version", version=f"samename {__version__}")
    sub = p.add_subparsers(dest="cmd", required=True)

    c = sub.add_parser("compare", help="compare two names")
    c.add_argument("a")
    c.add_argument("b")
    c.add_argument("--json", action="store_true")
    c.add_argument("-t", "--threshold", type=float, default=DEFAULT_THRESHOLD)
    _add_options(c)

    k = sub.add_parser("key", help="print the script-independent blocking keys of a name")
    k.add_argument("name")
    _add_options(k, compare_options=False)

    s = sub.add_parser("search", help="find a name in a file of names")
    s.add_argument("file")
    s.add_argument("query")
    s.add_argument("-c", "--column", help="CSV column name or 0-based number")
    s.add_argument("-n", "--limit", type=int, default=10)
    s.add_argument("-m", "--min-score", type=float, default=0.7)
    s.add_argument("--json", action="store_true")
    _add_options(s)

    d = sub.add_parser("dedupe", help="group names in a file that refer to the same person")
    d.add_argument("file")
    d.add_argument("-c", "--column", help="CSV column name or 0-based number")
    d.add_argument("-t", "--threshold", type=float, default=DEFAULT_THRESHOLD)
    d.add_argument("--json", action="store_true")
    _add_options(d)

    args = p.parse_args(argv)

    if args.cmd == "compare":
        m = compare(args.a, args.b, args.threshold, **_options(args))
        print(json.dumps(m.to_dict(), ensure_ascii=False, indent=2) if args.json else m.explain())
        return 0 if m.is_match else 1

    if args.cmd == "key":
        print(" ".join(keys(args.name, **_options(args, compare_options=False))))
        return 0

    names = _read_names(args.file, args.column)
    if args.cmd == "search":
        hits = NameIndex(names, **_options(args)).search(args.query, args.limit, args.min_score)
        if args.json:
            print(json.dumps([{"name": n, "score": round(sc, 4)} for n, sc in hits], ensure_ascii=False, indent=2))
        else:
            for n, sc in hits:
                print(f"{sc:.2f}  {n}")
        return 0 if hits else 1

    clusters = dedupe(names, args.threshold, **_options(args))
    if args.json:
        print(json.dumps([[names[i] for i in g] for g in clusters], ensure_ascii=False, indent=2))
    else:
        for n, g in enumerate(clusters, 1):
            print(f"# group {n}")
            for i in g:
                print(f"  {names[i]}")
        print(f"{len(clusters)} group(s) of likely duplicates among {len(names)} names", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
