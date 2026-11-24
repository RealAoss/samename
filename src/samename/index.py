"""Search and de-duplicate lists of names without comparing every pair."""

from __future__ import annotations

from .match import DEFAULT_THRESHOLD, compare, token_keys

__all__ = ["NameIndex", "dedupe"]


class NameIndex:
    """An in-memory index of names that can be searched in any script.

    The keyword options are those of :func:`samename.compare` and apply to
    every search.

    >>> idx = NameIndex(["Тарас Шевченко", "Olena Kovalenko", "Сергей Иванов"])
    >>> [name for name, _ in idx.search("Serhii Ivanov")]
    ['Сергей Иванов']
    """

    def __init__(self, names=(), *, cross_language: bool = True, diminutives: bool = False,
                 gender_insensitive_surnames: bool = False):
        self._options = {
            "cross_language": bool(cross_language),
            "diminutives": bool(diminutives),
            "gender_insensitive_surnames": bool(gender_insensitive_surnames),
        }
        self._key_options = {"cross_language": bool(cross_language), "diminutives": bool(diminutives)}
        self._names: list = []
        self._ids: list = []
        self._parts: list = []      # number of name parts of each stored name
        self._buckets: dict = {}    # blocking key -> positions
        for name in names:
            self.add(name)

    def __len__(self) -> int:
        return len(self._names)

    def add(self, name: str, id=None) -> None:
        """Add a name. ``id`` is returned by :meth:`search_ids` (default: position)."""
        pos = len(self._names)
        groups = token_keys(name, **self._key_options)
        self._names.append(name)
        self._ids.append(pos if id is None else id)
        self._parts.append(len(groups))
        for k in {k for g in groups for k in g}:
            self._buckets.setdefault(k, []).append(pos)

    def _candidates(self, name: str, after: int = -1) -> list:
        """Stored names sharing a key for two name parts (one, for 1-part names)."""
        groups = token_keys(name, **self._key_options)
        hits: dict = {}
        for g in groups:
            seen = set()
            for k in g:
                seen.update(self._buckets.get(k, ()))
            for pos in seen:
                if pos > after:
                    hits[pos] = hits.get(pos, 0) + 1
        n = len(groups)
        parts = self._parts
        return sorted(pos for pos, c in hits.items() if c >= min(2, n, parts[pos]))

    def _score(self, a: str, b: str) -> float:
        return compare(a, b, **self._options).score

    def _search(self, query, limit, min_score, exhaustive):
        cands = range(len(self._names)) if exhaustive else self._candidates(query)
        hits = []
        for pos in cands:
            s = self._score(query, self._names[pos])
            if s >= min_score:
                hits.append((s, pos))
        hits.sort(key=lambda h: (-h[0], h[1]))
        return hits[:limit] if limit else hits

    def search(self, query: str, limit: int = 10, min_score: float = 0.7, exhaustive: bool = False) -> list:
        """Return ``[(name, score), ...]`` best first.

        Candidates are found through blocking keys, which is fast but can miss
        a rare spelling; pass ``exhaustive=True`` to score every stored name.
        """
        return [(self._names[p], s) for s, p in self._search(query, limit, min_score, exhaustive)]

    def search_ids(self, query: str, limit: int = 10, min_score: float = 0.7, exhaustive: bool = False) -> list:
        """Like :meth:`search` but returns ``[(id, score), ...]``."""
        return [(self._ids[p], s) for s, p in self._search(query, limit, min_score, exhaustive)]


def dedupe(names, threshold: float = DEFAULT_THRESHOLD, **options) -> list:
    """Group names that refer to the same person.

    Returns a list of clusters, each a list of indexes into ``names``; only
    clusters with two or more members are returned. Matching is transitive
    (single linkage), so review large clusters before merging records.
    ``options`` are those of :func:`samename.compare`.
    """
    names = list(names)
    index = NameIndex(names, **options)
    parent = list(range(len(names)))

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    for i, name in enumerate(names):
        for j in index._candidates(name, after=i):
            ri, rj = find(i), find(j)
            if ri != rj and index._score(name, names[j]) >= threshold:
                parent[max(ri, rj)] = min(ri, rj)
    groups: dict = {}
    for pos in range(len(names)):
        groups.setdefault(find(pos), []).append(pos)
    return [g for g in groups.values() if len(g) > 1]
