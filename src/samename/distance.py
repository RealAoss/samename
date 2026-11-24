"""Weighted phonetic edit distance between two phoneme sequences.

Unlike an abjad, Cyrillic writes its vowels, so vowels carry real information
here: only the vowel changes that romanization and the Ukrainian / Russian /
Belarusian sound correspondences actually produce are cheap.

* i / y (и, і, ы) are nearly free; a / o (akanye), e / i (Сергій / Сергей),
  e / o (ё written as е) are cheap; a / i or u / y are not confusable at all.
* g / h (the letter г), h / kh, v / f / w, s / z, ts / s, sh / s and the like
  are cheap between scripts, because romanization systems disagree on them.
  Between two Cyrillic spellings only the cross-language pairs are allowed.
* The glide "j" is cheap wherever romanizations drop it (Yevhen / Evhen,
  Lyudmila / Ludmila, Yuriy / Yuri) and expensive elsewhere.
* A final "a" is never dropped cheaply: it is what separates Ivanov from
  Ivanova and Oleksandr from Oleksandra.
"""

from __future__ import annotations

from itertools import islice, product

INF = 99.0
_ALT = 0.08       # using a secondary reading of an ambiguous Latin spelling
_FINAL_A = 2.5    # dropping the vowel that marks a feminine form
_FINAL_V = 1.0

_CONS_PAIRS = {
    ("g", "h"): 0.15, ("g", "ɣ"): 0.0, ("h", "ɣ"): 0.0, ("h", "x"): 0.15, ("ɣ", "x"): 0.5,
    ("k", "x"): 0.4, ("v", "f"): 0.25, ("v", "w"): 0.05, ("f", "w"): 0.3,
    ("s", "z"): 0.35, ("s", "c"): 0.3, ("z", "c"): 0.4, ("c", "č"): 0.35, ("c", "t"): 0.4,
    ("s", "š"): 0.4, ("z", "ž"): 0.4, ("š", "ž"): 0.3, ("š", "č"): 0.35,
    ("d", "t"): 0.6, ("b", "p"): 0.6, ("g", "k"): 0.6, ("m", "n"): 0.7,
}
# what differs between the Ukrainian, Russian and Belarusian spelling of one name
_CROSS_LANGUAGE = {("g", "h"), ("g", "ɣ"), ("h", "ɣ"), ("v", "w"), ("c", "t")}
_VOWEL_PAIRS = {
    ("i", "y"): 0.05, ("a", "o"): 0.35, ("e", "i"): 0.35, ("e", "y"): 0.35,
    ("e", "o"): 0.3, ("o", "i"): 0.5, ("a", "e"): 0.6, ("o", "u"): 0.6,
}

CONS, CONS_CY, VOWELS = {}, {}, {}
for (_a, _b), _c in _CONS_PAIRS.items():
    CONS[(_a, _b)] = CONS[(_b, _a)] = _c
    if (_a, _b) in _CROSS_LANGUAGE:
        CONS_CY[(_a, _b)] = CONS_CY[(_b, _a)] = _c
for (_a, _b), _c in _VOWEL_PAIRS.items():
    VOWELS[(_a, _b)] = VOWELS[(_b, _a)] = _c


def weight(x) -> float:
    """Context-free weight of a phoneme, used to normalise the distance."""
    if x.t == "V":
        return 0.7
    if x.p == "j":
        return 0.2
    return 0.5 if x.p == "w" else 1.0


def sub_cost(x, y) -> float:
    if x.t == "V" and y.t == "V":
        if x.p == y.p:
            return 0.0
        return VOWELS.get((x.p, y.p), INF)
    if x.t == "C" and y.t == "C":
        if x.p == y.p:
            return 0.0
        table = CONS_CY if (x.src == "cy" and y.src == "cy") else CONS
        best = table.get((x.p, y.p), INF)
        if x.alt or y.alt:
            for i, a in enumerate((x.p,) + x.alt):
                for j, b in enumerate((y.p,) + y.alt):
                    if i == 0 and j == 0:
                        continue
                    c = 0.0 if a == b else table.get((a, b), INF)
                    c += _ALT * ((i > 0) + (j > 0))
                    if c < best:
                        best = c
        return best
    c, v = (x, y) if x.t == "C" else (y, x)
    if c.p == "j" and v.p in "iy":
        return 0.0 if v.glide else 0.1
    if v.p == "u":
        if c.p == "w":
            return 0.05
        if c.p == "v":
            return 0.3
    return INF


def _del_costs(seq) -> list:
    """Cost of leaving each phoneme of ``seq`` without a partner."""
    n = len(seq)
    out = []
    for i, x in enumerate(seq):
        prev = seq[i - 1] if i else None
        nxt = seq[i + 1] if i + 1 < n else None
        last = nxt is None
        if x.t == "C":
            if x.p == "j":
                if prev is None:
                    c = 0.05 if (nxt and nxt.p == "e") else 0.1 if (nxt and nxt.p in "iy") else 0.7
                elif prev.t == "C":                      # marks a soft consonant
                    c = 0.8 if (nxt and nxt.p == "a") else 0.1
                elif last:
                    c = 0.05 if prev.p in "iy" else 0.25
                elif nxt.t == "V":
                    c = 0.1 if prev.p in "iy" else 0.15
                else:
                    c = 0.4
            elif x.p == "č" and prev is not None and prev.p == "š":
                c = 0.2                                  # щ simplified to sh
            elif x.p == "z" and prev is not None and prev.p == "d" and nxt is not None and nxt.t == "V":
                c = 0.5                                  # Belarusian дз for д
            elif x.p == "w":
                c = 0.5
            else:
                c = 1.0
        else:
            if last and n >= 3:
                if x.p == "a":
                    aja = n >= 4 and prev.p == "j" and seq[i - 2].p == "a"
                    c = 0.2 if aja else _FINAL_A         # -ska / -skaya are one form
                elif x.p == "e" and x.src == "la" and n >= 4 and prev.t == "C" and prev.p != "j":
                    c = 0.15                             # silent French -e (Alexandre)
                else:
                    c = _FINAL_V
            elif x.glide:
                c = 0.8 if (nxt and nxt.p == "a") else 0.15
            elif x.p in "iy" and nxt is not None and nxt.p == "j" and i + 2 < n and seq[i + 2].t == "V":
                c = 0.1                                  # Mariya / Marya, Nataliya / Natalya
            elif x.p in "iy" and prev is not None and prev.p == "j" and prev.t == "C" and i > 1:
                c = 0.15                                 # Zaika / Заїка
            elif prev is None:
                c = 0.9
            else:
                c = 0.7
        out.append(c)
    return out


_IOTATED = 0.25


def _is_iotated(first, second) -> bool:
    """Soft consonant + a / o, which other spellings write as plain "e":
    Belarusian Сяргей / Sergey, Пятро / Petro; Russian Фёдор / Fedor."""
    return second.t == "V" and second.p in "ao" and (first.soft or first.glide)


def distance(a, b):
    """Return ``(distance, weight_a, weight_b)`` for two non-empty sequences."""
    n, m = len(a), len(b)
    da, db = _del_costs(a), _del_costs(b)
    D = [[0.0] * (m + 1) for _ in range(n + 1)]
    for i in range(1, n + 1):
        D[i][0] = D[i - 1][0] + da[i - 1]
    for j in range(1, m + 1):
        D[0][j] = D[0][j - 1] + db[j - 1]
    for i in range(1, n + 1):
        x = a[i - 1]
        row, up = D[i], D[i - 1]
        for j in range(1, m + 1):
            y = b[j - 1]
            best = up[j] + da[i - 1]
            c = row[j - 1] + db[j - 1]
            if c < best:
                best = c
            s = sub_cost(x, y)
            if s < INF:
                c = up[j - 1] + s
                if c < best:
                    best = c
            if i >= 2 and y.p == "e" and _is_iotated(a[i - 2], x):
                c = D[i - 2][j - 1] + _IOTATED
                if c < best:
                    best = c
            if j >= 2 and x.p == "e" and _is_iotated(b[j - 2], y):
                c = up[j - 2] + _IOTATED
                if c < best:
                    best = c
            row[j] = best
    return D[n][m], sum(weight(x) for x in a), sum(weight(x) for x in b)


def similarity(a, b) -> float:
    """Similarity in [0, 1] between two phoneme sequences."""
    if not a or not b:
        return 1.0 if (not a and not b) else 0.0
    d, wa, wb = distance(a, b)
    w = max(wa, wb)
    if w <= 0:
        return 1.0 if d == 0 else 0.0
    return max(0.0, 1.0 - d / w)


_KEY = {
    "b": "B", "p": "P", "v": "V", "f": "V", "w": "V", "d": "D", "t": "T",
    "z": "S", "s": "S", "c": "S", "ž": "J", "š": "J", "č": "J",
    "g": "K", "h": "K", "ɣ": "K", "x": "K", "k": "K",
    "l": "L", "m": "M", "n": "N", "r": "R", "j": "",
}


def skeletons(seq) -> tuple:
    """Coarse consonant skeletons of a sequence, used as blocking keys.

    Usually one; an ambiguous Latin spelling ("ch", "c") yields up to four.
    """
    options = []
    after_stop = []       # option positions whose consonant directly follows a t / d
    n = len(seq)
    for i, x in enumerate(seq):
        if x.t != "C":
            # a Latin "u" between a vowel and a consonant may be the Belarusian ў
            # (Yauhen = Яўген, Paulau = Паўлаў), which other spellings write as v
            if x.p == "u" and x.src == "la" and 0 < i < n - 1 and seq[i - 1].t == "V" and seq[i + 1].t == "C":
                options.append(["", "V"])
            continue
        if x.p == "z" and i and seq[i - 1].p == "d":
            continue                                     # дз / д
        ks = [_KEY[x.p]]
        for alt in x.alt:
            k = _KEY[alt]
            if k not in ks:
                ks.append(k)
        if x.p == "c" and i + 1 < n and seq[i + 1].p in "iej":
            ks.append("T")                               # Belarusian ц for т (Ціхан / Тихон)
        after_stop.append(len(options) if (i and seq[i - 1].t == "C" and seq[i - 1].p in "td") else -1)
        options.append(ks)
    affricate = {pos for pos in after_stop if pos >= 0}
    out = []
    for combo in islice(product(*options), 4):
        key = []
        for pos, k in enumerate(combo):
            if k == "J" and pos in affricate and key and key[-1] in "TD":
                key.pop()            # тч / дж / "tch" / "dzh": one affricate (Гнатчук = Gnatchuk)
            if k and (not key or key[-1] != k):
                key.append(k)
        key = "".join(key) or "0"
        if key not in out:
            out.append(key)
    return tuple(out)
