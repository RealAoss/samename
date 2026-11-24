"""Turn a single name token (Cyrillic or Latin script) into phonemes.

Both scripts are mapped onto one small shared inventory so that tokens written
in different scripts, and in different romanization systems, can be aligned:

* consonants  b p v f d t z s ž š č c(=ts) g h ɣ x k l m n r j w
* vowels      a e i y o u

``ɣ`` is the Cyrillic letter "г" when the language is unknown: it is "h" in
Ukrainian and Belarusian and "g" in Russian, and matches both.
``w`` is the Belarusian "ў". ``j`` is the glide written й / y / j / i.

Some Latin letters are ambiguous between romanization systems ("ch" is ч in
English, х in German and Polish, ш in French). Those phonemes carry
alternative readings in ``alt``; the distance function may use them at a
small extra cost.
"""

from __future__ import annotations

import unicodedata
from functools import lru_cache

__all__ = ["Ph", "clean_latin", "clean_cyrillic", "latin_phonemes", "cyrillic_phonemes",
           "phonemes", "detect_language"]


class Ph:
    """One phoneme. Immutable by convention."""

    __slots__ = ("t", "p", "src", "alt", "soft", "glide")

    def __init__(self, t, p, src, alt=(), soft=False, glide=False):
        self.t = t          # 'C' consonant | 'V' vowel
        self.p = p          # phoneme symbol
        self.src = src      # 'la' | 'cy'
        self.alt = alt      # other readings of an ambiguous Latin spelling
        self.soft = soft    # a "j" that only marks a soft consonant (Tatyana, Fyodor)
        self.glide = glide  # a Latin "i" before a vowel: may be that same soft "j"

    def __repr__(self):
        return self.p


# --------------------------------------------------------------------------
# Latin
# --------------------------------------------------------------------------

# Internal one-letter symbols: C = č, S = š, Z = ž, W = Belarusian ŭ.
_LATIN_PRE = {
    "č": "C", "š": "S", "ž": "Z", "ż": "Z", "ŝ": "SC", "ĉ": "C", "ć": "c", "ś": "s", "ź": "z",
    "ń": "n", "ł": "l", "ŭ": "W", "û": "yu", "â": "ya", "ë": "yo", "ï": "i", "ß": "ss",
    "đ": "d", "ø": "o", "æ": "e", "œ": "e", "ı": "i", "ș": "S", "ş": "S", "ț": "c",
}
_VOWEL_CHARS = "aeiouy"

_MULTI = (
    ("schtsch", ("š", "č")), ("shch", ("š", "č")), ("chtch", ("š", "č")), ("szcz", ("š", "č")),
    ("tsch", ("č",)), ("dsch", ("d", "ž")), ("dzh", ("d", "ž")), ("zgh", ("z", "h")),
    ("sch", ("š",)), ("tch", ("č",)),
    ("sh", ("š",)), ("zh", ("ž",)), ("kh", ("x",)), ("cz", ("č",)), ("sz", ("š",)),
    ("ts", ("c",)), ("tz", ("c",)), ("ck", ("k",)), ("ph", ("f",)), ("qu", ("k", "v")),
)
_CK_ENDINGS = frozenset("ck" + e for e in ("i", "y", "ij", "yj", "yi", "ii", "iy", "yy", "a", "aja", "aya", "aia"))
_SINGLE = {
    "b": "b", "p": "p", "v": "v", "w": "v", "f": "f", "d": "d", "t": "t", "z": "z", "s": "s",
    "g": "g", "k": "k", "q": "k", "l": "l", "m": "m", "n": "n", "r": "r",
    "C": "č", "S": "š", "Z": "ž", "W": "w",
}


def clean_latin(token: str) -> str:
    """Lower-case, fold diacritics into the internal alphabet, drop the rest."""
    s = "".join(_LATIN_PRE.get(c, c) for c in token.lower())
    s = unicodedata.normalize("NFD", s)
    return "".join(c for c in s if "a" <= c <= "z" or c in "CSZW")


class _Out(list):
    """Phoneme list that collapses doubled consonants and doubled vowels."""

    def __init__(self, src):
        super().__init__()
        self.src = src

    def cons(self, p, alt=(), soft=False):
        if self and self[-1].t == "C" and self[-1].p == p:
            return
        self.append(Ph("C", p, self.src, alt=alt, soft=soft))

    def vowel(self, p, glide=False):
        if self and self[-1].t == "V" and self[-1].p == p and p != "e":
            return
        self.append(Ph("V", p, self.src, glide=glide))

    def after_vowel(self):
        return bool(self) and self[-1].t == "V"

    def after_hard(self):
        """True after a consonant other than the glide."""
        return bool(self) and self[-1].t == "C" and self[-1].p != "j"


@lru_cache(maxsize=50_000)
def latin_phonemes(s: str) -> tuple:
    """Phonemes of a cleaned Latin token (see :func:`clean_latin`)."""
    n = len(s)
    out = _Out("la")
    i = 0
    while i < n:
        c = s[i]
        nxt = s[i + 1] if i + 1 < n else ""
        nxt2 = s[i + 2] if i + 2 < n else ""
        rest = s[i:]

        if c in "aou":
            two = s[i:i + 2]
            tail = s[i + 2:]
            # Belarusian -оў / -аў written "ou" / "au" (Ivanou, Bykau, -ouski, -auna)
            if two in ("ou", "au") and (tail == "" or tail.startswith(("sk", "na", "ic", "iC"))):
                out.vowel(c)
                out.cons("w")
                i += 2
            elif two in ("ou", "oo"):
                out.vowel("u")       # French "ou", ad-hoc English "oo"
                i += 2
            else:
                out.vowel(c)
                i += 1
            continue
        if c == "e":
            if nxt == "u" and (nxt2 == "" or s[i + 2:].startswith(("sk", "na"))):
                out.vowel("e")       # Belarusian -еў
                out.cons("w")
                i += 2
            else:
                out.vowel("e")
                i += 1
            continue
        if c == "i":
            if nxt and nxt in _VOWEL_CHARS:
                if out.after_hard():
                    out.vowel("i", glide=True)       # Maria, Tatiana, Siergiej
                else:
                    out.cons("j")                    # Iurii, Zoia, Mariia
            elif out.after_vowel():
                out.cons("j")                        # Sergei, Mikhail, Dmitrii
            else:
                out.vowel("i")
            i += 1
            continue
        if c == "y":
            if nxt and nxt in _VOWEL_CHARS:
                if out.after_hard() and nxt in "iy" and nxt2 == "":
                    out.vowel("y")                   # Bilyi, Zelenskyy
                else:
                    out.cons("j", soft=out.after_hard())   # Yuri, Tatyana, Mariya
            elif out.after_vowel():
                out.cons("j")                        # Sergey, Yuriy
            else:
                out.vowel("y")                       # Volodymyr, Dmitry
            i += 1
            continue

        if n >= 6 and rest in _CK_ENDINGS:
            out.cons("c")            # Polish / Czech / scientific -cki, -cka, -ckij
            i += 1                   # (Chmielnicki, Potocka, Trockij); the k follows
            continue
        for graph, phs in _MULTI:
            if rest.startswith(graph):
                for p in phs:
                    out.cons(p)
                i += len(graph)
                break
        else:
            if c == "c":
                if nxt == "h":
                    out.cons("č", alt=("x", "š"))    # English / German, Polish / French
                    i += 2
                    continue
                if nxt and nxt in "eiy":
                    out.cons("c", alt=("s",))
                else:
                    out.cons("k", alt=("c",))
            elif c == "t" and nxt == "h":
                out.cons("t", alt=("f",))            # Theodor = Fedir
                i += 2
                continue
            elif c == "g":
                if nxt == "h":
                    out.cons("ɣ")
                    i += 2
                    continue
                out.cons("g")
                if nxt == "u" and nxt2 and nxt2 in "ei":
                    i += 1                           # French "gu": Sergueï, Guennadi
            elif c == "h":
                if not (i == n - 1 and n > 3 and s[i - 1] == "a"):   # Hannah, Sarah
                    out.cons("h")
            elif c == "j":
                out.cons("j", alt=("ž",), soft=out.after_hard())
            elif c == "x":
                out.cons("k")
                out.cons("s")
            elif c in _SINGLE:
                out.cons(_SINGLE[c])
            i += 1
    return tuple(out)


# --------------------------------------------------------------------------
# Cyrillic
# --------------------------------------------------------------------------

_CY_CONS = {
    "б": "b", "п": "p", "в": "v", "ф": "f", "д": "d", "т": "t", "з": "z", "с": "s",
    "ж": "ž", "ш": "š", "ч": "č", "ц": "c", "ґ": "g", "х": "x", "к": "k", "л": "l",
    "м": "m", "н": "n", "р": "r", "ў": "w",
}
_CY_IOTATED = {"я": "a", "ю": "u", "є": "e", "ё": "o"}
_CY_PLAIN = {"а": "a", "о": "o", "у": "u", "э": "e", "ы": "y", "і": "i"}
_SIGNS = "ьъ'"
_CY_LETTERS = set(_CY_CONS) | set(_CY_IOTATED) | set(_CY_PLAIN) | set("гщеиїй" + _SIGNS)
_APOSTROPHES = "’ʼ`′ʹ‘"


def clean_cyrillic(token: str) -> str:
    """Lower-case, unify apostrophes, drop stress marks and anything unknown."""
    s = unicodedata.normalize("NFC", token.lower())
    s = "".join("'" if c in _APOSTROPHES else c for c in s)
    return "".join(c for c in s if c in _CY_LETTERS)


def detect_language(text: str):
    """Guess 'uk', 'ru', 'be' or None from the letters of a Cyrillic string."""
    s = text.lower()
    if "ў" in s:
        return "be"
    if any(c in s for c in "їєґ"):
        return "uk"
    ru_like = any(c in s for c in "ыэёъ")
    if "і" in s:
        return "be" if (ru_like and "и" not in s) else "uk"
    if ru_like:
        return "ru"
    return None


@lru_cache(maxsize=50_000)
def cyrillic_phonemes(s: str, lang=None) -> tuple:
    """Phonemes of a cleaned Cyrillic token. ``lang`` is 'uk', 'ru', 'be' or None."""
    n = len(s)
    out = _Out("cy")
    sign = False   # previous letter was a soft / hard sign or an apostrophe
    i = 0
    while i < n:
        c = s[i]
        nxt = s[i + 1] if i + 1 < n else ""
        if c in _SIGNS:
            sign = True
            i += 1
            continue
        open_pos = sign or not out or out.after_vowel()
        if c == "г":
            out.cons("h" if lang in ("uk", "be") else "g" if lang == "ru" else "ɣ")
        elif c == "щ":
            out.cons("š")
            out.cons("č")
        elif c == "т" and nxt == "с":
            out.cons("c")
            i += 1
        elif c in _CY_CONS:
            out.cons(_CY_CONS[c])
        elif c == "й":
            out.cons("j", soft=out.after_hard())
        elif c in _CY_IOTATED:
            out.cons("j", soft=out.after_hard())
            out.vowel(_CY_IOTATED[c])
        elif c == "ї":
            out.cons("j", soft=out.after_hard())
            out.vowel("i")
        elif c == "е":
            if lang != "uk" and open_pos:
                out.cons("j", soft=out.after_hard())
            out.vowel("e")
        elif c == "и":
            if sign:
                out.cons("j", soft=out.after_hard())     # Ильин
            out.vowel("y" if lang == "uk" else "i")
        elif c in _CY_PLAIN:
            if sign and c in "оі":
                out.cons("j", soft=out.after_hard())     # Ковальов
            out.vowel(_CY_PLAIN[c])
        sign = False
        i += 1
    return tuple(out)


def phonemes(script: str, text: str, lang=None) -> tuple:
    if script == "cy":
        return cyrillic_phonemes(text, lang)
    return latin_phonemes(text)
