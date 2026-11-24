"""Rough speed measurement on synthetic data (nothing is read from or written to disk).

    python bench/speed.py

Builds 4,000 distinct Ukrainian-script full names from the lexicon and a list
of generated surnames, then plants 1,000 duplicates written in a plain Latin
romanization (some without the patronymic, some surname-first), and times
``compare``, ``NameIndex.search`` and ``dedupe`` on the resulting 5,000 names.
"""

from __future__ import annotations

import os
import random
import sys
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
sys.path.insert(0, os.path.dirname(__file__))

import samename  # noqa: E402
from samename import lexicon  # noqa: E402
from run import translit  # noqa: E402

_STEMS = ("Коваль Шевч Бонд Мельн Ткач Крав Петр Іван Савч Гнат Лис Мороз Руд Пав Марч Остап Гриц Дмитр "
          "Назар Тарас Юрч Кузьм Луц Захар Федор Панч Онищ Яким Прокоп Степан Тимош Харч Стець Дзюб "
          "Гонч Бойч Кліщ Литвин Поліщ Яцен Зінч Вакул Нестер Олійн Сидор Васил Клим Дем Герас Корн").split()
_SUFFIXES = ("енко", "ук", "чук", "ишин", "як", "ко", "ович", "инець", "ів", "ак")
_FATHERS = ("Іванович", "Петрович", "Миколайович", "Олександрович", "Васильович", "Сергійович",
            "Андрійович", "Михайлович", "Степанович", "Богданович", "Юрійович", "Ігорович")


def _given_names() -> list:
    out = []
    for line in lexicon._DATA.splitlines():
        if line.startswith("m "):
            fields = line[2:].split("|")
            if len(fields) > 1 and fields[1].split() and fields[1].split()[0] != "-":
                out.append(fields[1].split()[0])
    return out


def build(n_people: int = 4000, n_duplicates: int = 1000, seed: int = 0):
    rnd = random.Random(seed)
    given = _given_names()
    # no "сч" / "цч" clusters: their plain romanization ("sch", "tsch") is read as
    # ш / ч, a real limitation (see README) that does not belong in a speed test
    surnames = [s + x for s in _STEMS for x in _SUFFIXES if not (x == "чук" and s[-1] in "сцчш")]
    people = set()
    while len(people) < n_people:
        parts = [rnd.choice(given), rnd.choice(_FATHERS), rnd.choice(surnames)]
        people.add(tuple(parts))
    people = sorted(people)
    rnd.shuffle(people)
    names = [" ".join(p) for p in people]
    planted = []                                  # (index of original, index of duplicate)
    for src in rnd.sample(range(n_people), n_duplicates):
        g, f, s = (translit(x).capitalize() for x in people[src])
        style = rnd.randrange(3)
        dup = f"{g} {f} {s}" if style == 0 else f"{g} {s}" if style == 1 else f"{s} {g} {f}"
        planted.append((src, len(names)))
        names.append(dup)
    return names, planted


def main():
    names, planted = build()
    rnd = random.Random(1)
    print(f"{len(names)} names, {len(planted)} planted cross-script duplicates")

    pairs = [(rnd.choice(names), rnd.choice(names)) for _ in range(20000)]
    t0 = time.perf_counter()
    for a, b in pairs:
        samename.compare(a, b)
    dt = time.perf_counter() - t0
    print(f"compare        {dt / len(pairs) * 1000:.3f} ms per pair  ({len(pairs)} random pairs, caches warming up)")
    t0 = time.perf_counter()
    for a, b in pairs:
        samename.compare(a, b)
    dt = time.perf_counter() - t0
    print(f"compare again  {dt / len(pairs) * 1000:.3f} ms per pair  (same pairs, name parts now cached)")

    t0 = time.perf_counter()
    index = samename.NameIndex(names)
    print(f"build index    {(time.perf_counter() - t0) * 1000:.0f} ms")
    queries = [names[dup] for _, dup in planted[:300]]
    t0 = time.perf_counter()
    found = 0
    for (src, _), q in zip(planted, queries):
        found += any(name == names[src] for name, _ in index.search(q))
    dt = time.perf_counter() - t0
    print(f"search         {dt / len(queries) * 1000:.2f} ms per query  "
          f"({found}/{len(queries)} originals returned for their Latin duplicate)")
    t0 = time.perf_counter()
    for q in queries[:20]:
        index.search(q, exhaustive=True)
    dt = time.perf_counter() - t0
    print(f"search (exhaustive)  {dt / 20 * 1000:.0f} ms per query")

    t0 = time.perf_counter()
    clusters = samename.dedupe(names)
    dt = time.perf_counter() - t0
    where = {}
    for n, g in enumerate(clusters):
        for i in g:
            where[i] = n
    hit = sum(1 for a, b in planted if a in where and where[a] == where.get(b))
    print(f"dedupe         {dt:.2f} s for {len(names)} names  "
          f"({hit}/{len(planted)} planted duplicates grouped with their original; {len(clusters)} groups)")


if __name__ == "__main__":
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8")
        except (AttributeError, ValueError):
            pass
    main()
