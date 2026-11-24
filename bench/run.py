"""Benchmark samename against the approaches people usually reach for.

    python bench/run.py            # summary tables for the sets
    python bench/run.py --errors   # also list every pair samename gets wrong

Baselines (each is given its *best possible* threshold on this data, which
flatters them; samename is measured at its fixed default threshold):

* levenshtein     normalised edit distance on the lower-cased strings
* translit+lev    naive letter-by-letter romanization of Cyrillic, then
                  normalised edit distance
* translit+skel   same romanization, vowels removed, exact match of the rest
"""

from __future__ import annotations

import importlib
import os
import sys
import time
import unicodedata

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
sys.path.insert(0, os.path.dirname(__file__))

import samename  # noqa: E402

_CYRILLIC = {
    "а": "a", "б": "b", "в": "v", "г": "g", "ґ": "g", "д": "d", "е": "e", "є": "ye", "ё": "yo",
    "ж": "zh", "з": "z", "и": "i", "і": "i", "ї": "yi", "й": "y", "к": "k", "л": "l", "м": "m",
    "н": "n", "о": "o", "п": "p", "р": "r", "с": "s", "т": "t", "у": "u", "ў": "u", "ф": "f",
    "х": "kh", "ц": "ts", "ч": "ch", "ш": "sh", "щ": "shch", "ъ": "", "ы": "y", "ь": "", "э": "e",
    "ю": "yu", "я": "ya", "'": "", "’": "",
}


def translit(s: str) -> str:
    s = "".join(_CYRILLIC.get(c, c) for c in s.lower())
    s = unicodedata.normalize("NFD", s)
    return "".join(c for c in s if ("a" <= c <= "z") or c == " ")


def lev(a: str, b: str) -> float:
    if not a and not b:
        return 1.0
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        cur = [i]
        for j, cb in enumerate(b, 1):
            cur.append(min(prev[j] + 1, cur[-1] + 1, prev[j - 1] + (ca != cb)))
        prev = cur
    return 1.0 - prev[-1] / max(len(a), len(b))


def skel(s: str) -> str:
    return "".join(c for c in translit(s) if c not in "aeiouyjw ")


METHODS = {
    "levenshtein": lambda a, b: lev(a.lower(), b.lower()),
    "translit+lev": lambda a, b: lev(translit(a), translit(b)),
    "translit+skel": lambda a, b: 1.0 if skel(a) == skel(b) else 0.0,
    "samename": samename.score,
}


def build_pairs(GROUPS, DISTINCT):
    pos, neg = [], [tuple(p) for p in DISTINCT]
    for g in GROUPS:
        for i in range(len(g)):
            for j in range(i + 1, len(g)):
                pos.append((g[i], g[j]))
    # first two spellings of each group against the first two of every other group
    for x in range(len(GROUPS)):
        for y in range(x + 1, len(GROUPS)):
            neg.append((GROUPS[x][0], GROUPS[y][0]))
            neg.append((GROUPS[x][1], GROUPS[y][1]))
    return pos, neg


def prf(pos_scores, neg_scores, t):
    tp = sum(s >= t for s in pos_scores)
    fp = sum(s >= t for s in neg_scores)
    fn = len(pos_scores) - tp
    p = tp / (tp + fp) if tp + fp else 0.0
    r = tp / (tp + fn) if tp + fn else 0.0
    f = 2 * p * r / (p + r) if p + r else 0.0
    return p, r, f


def main():
    only = [a for a in sys.argv[1:] if not a.startswith("-")]     # e.g. "dataset" or "blind"
    for title, name in (
        ("development set (bench/dataset.py): tuned on", "dataset"),
        ("blind set (bench/blind.py): run once, never tuned on", "blind"),
    ):
        if only and name not in only:
            continue
        if not os.path.isfile(os.path.join(os.path.dirname(os.path.abspath(__file__)), name + ".py")):
            print(f"== bench/{name}.py not found: skipping the {name} set ==")
            continue
        mod = importlib.import_module(name)
        print(f"== {title} ==")
        report(mod.GROUPS, mod.DISTINCT)
        print()


def report(GROUPS, DISTINCT):
    pos, neg = build_pairs(GROUPS, DISTINCT)
    print(f"{len(pos)} same-name pairs, {len(neg)} different-name pairs "
          f"({len(DISTINCT)} of them deliberately confusable)\n")
    print(f"{'method':<15}{'threshold':>10}{'precision':>11}{'recall':>9}{'F1':>8}")
    for name, fn in METHODS.items():
        t0 = time.perf_counter()
        ps = [fn(a, b) for a, b in pos]
        ns = [fn(a, b) for a, b in neg]
        dt = time.perf_counter() - t0
        if name == "samename":
            t = samename.DEFAULT_THRESHOLD
            note = f"   fixed default; {len(pos) + len(neg)} pairs in {dt * 1000:.0f} ms"
        else:
            t = max((x / 100 for x in range(5, 101)), key=lambda t: prf(ps, ns, t)[2])
            note = "   best threshold for this data"
        p, r, f = prf(ps, ns, t)
        print(f"{name:<15}{t:>10.2f}{p:>11.3f}{r:>9.3f}{f:>8.3f}{note}")
        if name == "samename" and "--errors" in sys.argv:
            print("\nmissed (same name, scored below threshold):")
            for (a, b), s in zip(pos, ps):
                if s < t:
                    print(f"  {s:.2f}  {a}  |  {b}")
            print("\nfalse alarms (different names, scored above threshold):")
            for (a, b), s in zip(neg, ns):
                if s >= t:
                    print(f"  {s:.2f}  {a}  |  {b}")


if __name__ == "__main__":
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8")
        except (AttributeError, ValueError):
            pass
    main()
