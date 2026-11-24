"""Compare two full names and explain the result."""

from __future__ import annotations

from dataclasses import dataclass, field
from functools import lru_cache

from . import lexicon
from .distance import INF, similarity, skeletons, sub_cost
from .parse import Token, parse_name, patronymic_of

__all__ = ["Match", "compare", "score", "is_match", "token_similarity", "keys", "token_keys",
           "DEFAULT_THRESHOLD"]

DEFAULT_THRESHOLD = 0.85
_DISTINCT_CAP = 0.75       # two spellings known to be different names
_SAME_FLOOR = 0.92         # two forms of one known name (Volodymyr / Vladimir)
_SHORT_FLOOR = 0.90        # a diminutive and its full name (Sasha / Oleksandr)
_WEAK_PAIR = 0.82          # below this, a paired name part counts against the match
_INITIAL_SIM = 0.9
_INITIAL_WEIGHT = 0.4
_REORDER_FACTOR = 0.97
_EXTRA_PENALTY = 0.2       # a name part present on one side only
_EXTRA_PENALTY_THIN = 0.5  # ... when only one part matched at all
_EXTRA_PATRONYMIC = 0.1    # an omitted patronymic says very little
_JOIN_MIN = 0.9
_JOIN_GAIN = 0.08
_GENDER_STEM_MIN = 0.9

_GENDER_NOTE = "masculine and feminine form of one surname"
_GENDER_IGNORED = "surname gender ignored"


@dataclass
class Match:
    """Result of :func:`compare`."""

    score: float
    pairs: list = field(default_factory=list)        # (part of a, part of b, similarity)
    unmatched_a: list = field(default_factory=list)
    unmatched_b: list = field(default_factory=list)
    reordered: bool = False
    threshold: float = DEFAULT_THRESHOLD
    notes: list = field(default_factory=list)

    @property
    def is_match(self) -> bool:
        return self.score >= self.threshold

    @property
    def level(self) -> str:
        s = self.score
        if s >= 0.93:
            return "strong"
        if s >= 0.85:
            return "probable"
        if s >= 0.70:
            return "possible"
        return "no"

    def __bool__(self) -> bool:
        return self.is_match

    def to_dict(self) -> dict:
        return {
            "score": round(self.score, 4),
            "is_match": self.is_match,
            "level": self.level,
            "pairs": [{"a": a, "b": b, "score": round(s, 4)} for a, b, s in self.pairs],
            "unmatched_a": list(self.unmatched_a),
            "unmatched_b": list(self.unmatched_b),
            "reordered": self.reordered,
            "notes": list(self.notes),
        }

    def explain(self) -> str:
        lines = [f"score {self.score:.2f}  ({self.level})"]
        for a, b, s in self.pairs:
            lines.append(f"  {a}  ~  {b}   {s:.2f}")
        if self.unmatched_a:
            lines.append("  only in first:  " + ", ".join(self.unmatched_a))
        if self.unmatched_b:
            lines.append("  only in second: " + ", ".join(self.unmatched_b))
        if self.reordered:
            lines.append("  (name parts appear in a different order)")
        for note in self.notes:
            lines.append(f"  ({note})")
        return "\n".join(lines)


# --------------------------------------------------------------------------
# one name part against another
# --------------------------------------------------------------------------

def _gender_pair(a: tuple, b: tuple):
    """If ``a`` / ``b`` are the two gender forms of one surname, return the
    similarity of their stems; otherwise None.

    Ivanov / Ivanova · Shevchyshyn / Shevchyshyna · Kovalskyi / Kovalska ·
    Tolstoy / Tolstaya · Bilyi / Bila
    """
    for m, f in ((a, b), (b, a)):
        if len(f) < 4 or len(m) < 3 or f[-1].p != "a":
            continue
        # -ov / -ova, -ev / -eva, -in / -ina, -yn / -yna
        if f[-2].p in "vn" and f[-3].t == "V" and m[-1].p in "vnfw":
            s = similarity(m, f[:-1])
            if s >= _GENDER_STEM_MIN:
                return s
        # adjectival: -yi, -ii, -oi, -y  against  -a, -aya
        fs = f[:-3] if (len(f) >= 6 and f[-2].p == "j" and f[-3].p == "a") else f[:-1]
        if m[-1].p == "j" and len(m) >= 5 and m[-2].p in "iyo":
            ms = m[:-2]
        elif m[-1].p in "iy":
            ms = m[:-1]
        else:
            continue
        if len(ms) >= 3 and len(fs) >= 3 and ms[-1].t == "C" and fs[-1].t == "C":
            s = similarity(ms, fs)
            if s >= _GENDER_STEM_MIN:
                return s
    return None


def _initial_match(initial: Token, other: Token, opts) -> bool:
    a = initial.seq
    if not a:
        return False
    x = a[0]
    firsts = list(other.seq[:1])
    if other.kind != "initial" and opts[0]:
        firsts.extend(lexicon.first_phonemes(lexicon.name_ids(other.seq, opts[1])))
    for y in firsts:
        if x.t != y.t:
            c, v = (x, y) if x.t == "C" else (y, x)
            if c.p == "j" or sub_cost(x, y) < INF:
                return True                    # Є. / E. · Ю. / I. · У. / V.
        elif x.t == "V" or sub_cost(x, y) <= 0.2:
            return True
    return False


@lru_cache(maxsize=200_000)
def _token_result(a: Token, b: Token, opts: tuple):
    """Return ``(similarity, note)`` for two name parts; ``opts`` is
    ``(cross_language, diminutives, gender_insensitive_surnames)``."""
    cross_language, diminutives, gender_insensitive = opts
    if a.kind == "initial" or b.kind == "initial":
        if a.kind == b.kind:
            ok = _initial_match(a, b, opts) or _initial_match(b, a, opts)
            return (1.0 if ok else 0.0), None
        ini, full = (a, b) if a.kind == "initial" else (b, a)
        return (_INITIAL_SIM if _initial_match(ini, full, opts) else 0.0), None

    sa, sb = a.seq, b.seq
    best = similarity(sa, sb)

    pa, pb = patronymic_of(sa), patronymic_of(sb)
    if pa and pb and (a.kind == "patronymic" or b.kind == "patronymic"):
        if pa[0] != pb[0]:
            return min(best, _DISTINCT_CAP), None          # brother and sister
        if pa[1] and pb[1]:
            if pa[1].isdisjoint(pb[1]):
                return min(best, _DISTINCT_CAP), None
            if cross_language:
                best = max(best, _SAME_FLOOR)              # Mykolaiovych / Nikolaevich
        return best, None

    ia, ib = lexicon.name_ids(sa), lexicon.name_ids(sb)
    if ia and ib:
        if not ia.isdisjoint(ib):
            if cross_language:
                best = max(best, _SAME_FLOOR)
        elif diminutives and not lexicon.name_ids(sa, True).isdisjoint(lexicon.name_ids(sb, True)):
            best = max(best, _SHORT_FLOOR)
        else:
            best = min(best, _DISTINCT_CAP)                # known to be different names
        return best, None
    if not ia and not ib:
        stems = _gender_pair(sa, sb)
        if stems is not None:
            if gender_insensitive:
                return max(best, stems), _GENDER_IGNORED
            return min(best, _DISTINCT_CAP), _GENDER_NOTE
    return best, None


def token_similarity(a: Token, b: Token, opts: tuple = (True, False, False)) -> float:
    """Similarity in [0, 1] between two name parts, in any two scripts."""
    return _token_result(a, b, opts)[0]


# --------------------------------------------------------------------------
# full names
# --------------------------------------------------------------------------

def _weight(tok: Token) -> float:
    return _INITIAL_WEIGHT if tok.kind == "initial" else 1.0


def _join(a: Token, b: Token) -> Token:
    return Token(a.script, a.text + b.text, a.display + " " + b.display, "name", a.lang, a.hyphen)


def _merge_split_parts(A: list, B: list, opts) -> list:
    """If one part of A is written as two adjacent parts in B, join them
    (Anna-Maria / Annamaria, Bila Tserkva / Bilatserkva)."""
    B = list(B)
    for t in A:
        if t.kind != "name":
            continue
        j = 0
        while j < len(B) - 1:
            u, v = B[j], B[j + 1]
            if u.kind == "name" and v.kind == "name" and u.script == v.script:
                merged = _join(u, v)
                s = token_similarity(t, merged, opts)
                if s >= _JOIN_MIN and s > max(token_similarity(t, u, opts),
                                              token_similarity(t, v, opts)) + _JOIN_GAIN:
                    B[j:j + 2] = [merged]
                    continue
            j += 1
    return B


def _assign(S, wa, wb, monotonic: bool):
    """Best one-to-one assignment of rows to columns; returns (total, pairs)."""
    n, m = len(S), len(S[0]) if S else 0
    if monotonic:
        D = [[0.0] * (m + 1) for _ in range(n + 1)]
        for i in range(1, n + 1):
            for j in range(1, m + 1):
                D[i][j] = max(D[i - 1][j], D[i][j - 1],
                              D[i - 1][j - 1] + S[i - 1][j - 1] * min(wa[i - 1], wb[j - 1]))
        pairs = []
        i, j = n, m
        while i > 0 and j > 0:
            if D[i][j] == D[i - 1][j]:
                i -= 1
            elif D[i][j] == D[i][j - 1]:
                j -= 1
            else:
                pairs.append((i - 1, j - 1))
                i -= 1
                j -= 1
        return D[n][m], pairs[::-1]
    if m > 12:  # absurdly long name: greedy is good enough
        cells = sorted(((S[i][j] * min(wa[i], wb[j]), i, j) for i in range(n) for j in range(m)),
                       key=lambda c: (-c[0], c[1], c[2]))
        used_i, used_j, pairs, total = set(), set(), [], 0.0
        for v, i, j in cells:
            if i not in used_i and j not in used_j and v > 0:
                used_i.add(i)
                used_j.add(j)
                pairs.append((i, j))
                total += v
        return total, sorted(pairs)

    @lru_cache(maxsize=None)
    def best(i: int, mask: int):
        if i == n:
            return 0.0, ()
        top, top_pairs = best(i + 1, mask)  # leave row i unmatched
        for j in range(m):
            if not mask & (1 << j):
                v = S[i][j] * min(wa[i], wb[j])
                if v <= 0:
                    continue
                sub, sub_pairs = best(i + 1, mask | (1 << j))
                if v + sub > top + 1e-12:
                    top, top_pairs = v + sub, ((i, j),) + sub_pairs
        return top, top_pairs

    total, pairs = best(0, 0)
    return total, list(pairs)


def compare(a: str, b: str, threshold: float = DEFAULT_THRESHOLD, *, cross_language: bool = True,
            diminutives: bool = False, gender_insensitive_surnames: bool = False) -> Match:
    """Compare two full names written in Cyrillic or Latin script.

    cross_language
        treat the Ukrainian, Russian and Belarusian forms of a given name
        (Volodymyr / Vladimir / Uladzimir) as the same name. Default True.
    diminutives
        also accept a short form for its full name (Sasha / Oleksandr).
    gender_insensitive_surnames
        accept Ivanov / Ivanova and Kovalskyi / Kovalska as the same surname
        (useful for linking family members; by default they do not match,
        because they are different people).

    >>> compare("Володимир Зеленський", "Vladimir Zelensky").is_match
    True
    """
    opts = (bool(cross_language), bool(diminutives), bool(gender_insensitive_surnames))
    A, B = list(parse_name(a)), list(parse_name(b))
    if not A or not B:
        return Match(0.0, threshold=threshold)
    B = _merge_split_parts(A, B, opts)
    A = _merge_split_parts(B, A, opts)
    if len(A) > len(B):  # keep the assignment search on the shorter side
        res = _compare_tokens(B, A, threshold, opts)
        res.pairs = [(y, x, s) for x, y, s in res.pairs]
        res.unmatched_a, res.unmatched_b = res.unmatched_b, res.unmatched_a
        return res
    return _compare_tokens(A, B, threshold, opts)


def _extra_factor(left: list, strong: int) -> float:
    if left and all(t.kind == "patronymic" for t in left):
        return _EXTRA_PATRONYMIC
    if left and all(t.kind != "name" for t in left):
        return _EXTRA_PENALTY
    return _EXTRA_PENALTY if strong >= 2 else _EXTRA_PENALTY_THIN


def _compare_tokens(A, B, threshold, opts) -> Match:
    R = [[_token_result(x, y, opts) for y in B] for x in A]
    S = [[r[0] for r in row] for row in R]
    wa, wb = [_weight(t) for t in A], [_weight(t) for t in B]
    mono_total, mono_pairs = _assign(S, wa, wb, True)
    free_total, free_pairs = _assign(S, wa, wb, False)
    reordered = free_total > mono_total + 1e-9
    pairs = free_pairs if reordered else mono_pairs

    num = den = 0.0
    used_a, used_b = set(), set()
    strong = 0
    out_pairs, notes = [], []
    for i, j in pairs:
        w = min(wa[i], wb[j])
        s = S[i][j]
        if s < _WEAK_PAIR and len(pairs) > 1:
            s *= 0.25  # one clearly different part outweighs several equal ones
        num += w * s
        den += w
        used_a.add(i)
        used_b.add(j)
        if S[i][j] >= _WEAK_PAIR and A[i].kind != "initial" and B[j].kind != "initial":
            strong += 1
        out_pairs.append((A[i].display, B[j].display, S[i][j]))
        if R[i][j][1]:
            notes.append(f"{A[i].display} / {B[j].display}: {R[i][j][1]}")
    left_a = [i for i in range(len(A)) if i not in used_a]
    left_b = [j for j in range(len(B)) if j not in used_b]
    wa_left = sum(wa[i] for i in left_a)
    wb_left = sum(wb[j] for j in left_b)
    conflict = min(wa_left, wb_left)          # both sides have something the other lacks
    extra = abs(wa_left - wb_left)            # one side simply has more parts
    longer = [A[i] for i in left_a] if wa_left >= wb_left else [B[j] for j in left_b]
    den += conflict + extra * _extra_factor(longer, strong)
    value = num / den if den else 0.0
    if reordered:
        value *= _REORDER_FACTOR
    return Match(
        score=max(0.0, min(1.0, value)),
        pairs=out_pairs,
        unmatched_a=[A[i].display for i in left_a],
        unmatched_b=[B[j].display for j in left_b],
        reordered=reordered,
        threshold=threshold,
        notes=notes,
    )


def score(a: str, b: str, **options) -> float:
    """Similarity in [0, 1] between two full names."""
    return compare(a, b, **options).score


def is_match(a: str, b: str, threshold: float = DEFAULT_THRESHOLD, **options) -> bool:
    """True if two names plausibly refer to the same person."""
    return compare(a, b, threshold, **options).score >= threshold


# --------------------------------------------------------------------------
# blocking keys
# --------------------------------------------------------------------------

def keys(name: str, *, cross_language: bool = True, diminutives: bool = False) -> tuple:
    """Script-independent blocking keys, one or more per name part.

    Two spellings of the same name share at least one key in nearly all cases,
    so the keys can be stored in a database column or used to bucket records
    before the (more expensive) pairwise :func:`compare`. A part the lexicon
    knows also gets the key of its name (``=VOLODYMYR``), which is what links
    the Ukrainian, Russian and Belarusian forms. An ambiguous Latin spelling
    ("ch" is ч in English but х in German and Polish) yields extra keys.

    >>> keys("Шевченко") == keys("Szewczenko") == ("JVJNK",)
    True
    >>> keys("Shevchenko")
    ('JVJNK', 'JVKNK')
    >>> keys("Володимир") == keys("Vladimir") == ("VLDMR", "=VOLODYMYR")
    True
    """
    out = []
    for group in token_keys(name, cross_language=cross_language, diminutives=diminutives):
        for k in group:
            if k not in out:
                out.append(k)
    return tuple(out)


def token_keys(name: str, *, cross_language: bool = True, diminutives: bool = False) -> tuple:
    """Like :func:`keys`, but grouped: one tuple of keys per name part."""
    out = []
    for tok in parse_name(name):
        if tok.kind == "initial":
            continue
        seq = tok.seq
        group = list(skeletons(seq))
        if cross_language or diminutives:
            pat = patronymic_of(seq) if tok.kind == "patronymic" else None
            if pat:
                extra = ["=" + lexicon.canonical(e).upper() + "~" for e in sorted(pat[1])]
            else:
                ids = lexicon.name_ids(seq, diminutives)
                extra = ["=" + lexicon.canonical(e).upper() for e in sorted(ids)]
            group.extend(extra)
        if group:
            out.append(tuple(group))
    return tuple(out)
