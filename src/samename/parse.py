"""Split a full name into tokens and work out what each token is.

Handled here, for Cyrillic and Latin script alike:

* "Given Patronymic Surname", "Surname Given Patronymic" and
  "SURNAME, Given" order (the part before a single comma is moved to the end);
* initials, spaced or glued:  "Шевченко Т. Г." · "T.H. Shevchenko" · "Yu. Andrukhovych";
* patronymics:  Іванович · Ивановна · Ivanovych · Ivanovitch · Ілліч · Ivanauna;
* hyphenated surnames (each half is its own token);
* titles (пан, пані, Dr, Prof ...), stress marks, apostrophe variants,
  Latin look-alike letters typed inside a Cyrillic word.
"""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass
from functools import lru_cache

from . import lexicon
from .phonemes import clean_cyrillic, clean_latin, detect_language, phonemes

__all__ = ["Token", "parse_name", "patronymic_of"]


@dataclass(frozen=True)
class Token:
    script: str            # 'cy' | 'la'
    text: str              # cleaned spelling
    display: str           # the text as the user wrote it
    kind: str = "name"     # 'name' | 'initial' | 'patronymic'
    lang: str | None = None   # 'uk' | 'ru' | 'be' | None, for Cyrillic tokens
    hyphen: bool = False   # joined to the previous token by a hyphen

    @property
    def seq(self) -> tuple:
        return phonemes(self.script, self.text, self.lang)


_INVISIBLE = re.compile("[­​-‏‪-‮⁦-⁩﻿́̀]")
_APOSTROPHES = "’ʼ`′ʹ‘"
_WORD = re.compile(r"[^\W\d_](?:[^\W\d_]|'(?=[^\W\d_]))*")
_CYRILLIC = re.compile("[Ѐ-ӿ]")
_LOOKALIKES = str.maketrans("aeopcxiyAEOPCXIBKMHT", "аеорсхіуАЕОРСХІВКМНТ")

_TITLES = {
    "la": {"mr", "mrs", "ms", "miss", "dr", "prof", "pan", "pani", "herr", "frau", "mme", "mlle"},
    "cy": {"пан", "пані", "пани", "панна", "др", "проф", "акад", "доц", "гр", "тов", "спадар",
           "спадарыня", "господин", "госпожа", "добродій", "добродійка"},
}
_LATIN_INITIALS = {"yu", "ya", "ye", "yo", "iu", "ia", "ie", "zh", "kh", "ch", "sh", "ts"}


def _words(name: str):
    """Yield ``(script, text, raw, hyphenated, dotted)`` for each word."""
    out = []
    for m in _WORD.finditer(name):
        raw = m.group()
        before = name[m.start() - 1] if m.start() else ""
        after = name[m.end()] if m.end() < len(name) else ""
        if _CYRILLIC.search(raw):
            if re.search("[A-Za-z]", raw):
                raw = raw.translate(_LOOKALIKES)
            script, text = "cy", clean_cyrillic(raw)
        else:
            script, text = "la", clean_latin(raw.replace("'", ""))
        if text.strip("'"):
            out.append((script, text, raw, before in "-‐‑–" and before != "" and bool(out), after == "."))
    return out


def patronymic_of(seq: tuple):
    """Return ``(gender, father ids)`` if ``seq`` is shaped like a patronymic.

    ``gender`` is 'm' (-ovych, -evich, -ich) or 'f' (-ivna, -ovna, -ichna);
    the ids are the lexicon names the father's name resolves to, possibly none.
    Returns None for anything else.
    """
    n = len(seq)
    if n < 4:
        return None
    p = [x.p for x in seq]
    if p[-1] == "a" and p[-2] == "n":
        if p[-3] in "vw" and seq[-4].t == "V" and n >= 6:
            # a father's name that itself ends in -iv / -ov absorbs the suffix (Yakiv -> Yakivna)
            return "f", lexicon.father_ids(seq[:-4]) or lexicon.father_ids(seq[:-2])
        if p[-3] == "č" and p[-4] in "iy":
            ids = lexicon.father_ids(seq[:-4])
            if not ids and n >= 7 and p[-5] == "n" and p[-6] in "iy":
                ids = lexicon.father_ids(seq[:-6])          # Illinichna, Kuzminichna
            return ("f", ids) if ids else None
        return None
    if p[-1] == "č" and p[-2] in "iy":
        if p[-3] == "v" and seq[-4].t == "V" and n >= 6:
            # Yakiv / Yakov -> Yakovych, not "Yakovovych"
            return "m", lexicon.father_ids(seq[:-4]) or lexicon.father_ids(seq[:-2])
        ids = lexicon.father_ids(seq[:-2], a_stems_only=True)   # Illich, Kuzmich, Lukich
        return ("m", ids) if ids else None
    return None


@lru_cache(maxsize=20_000)
def parse_name(name: str) -> tuple:
    """Parse a full name into a tuple of :class:`Token`."""
    if not isinstance(name, str):
        return ()
    name = unicodedata.normalize("NFC", name)
    name = _INVISIBLE.sub("", name)
    for ch in _APOSTROPHES:
        name = name.replace(ch, "'")
    if name.count(",") == 1:                      # "SURNAME, Given Patronymic"
        head, tail = name.split(",")
        if head.strip() and tail.strip():
            name = tail + " " + head
    words = _words(name)
    lang = detect_language(" ".join(w[1] for w in words if w[0] == "cy"))

    if len(words) > 1:
        kept = [w for w in words if w[1] not in _TITLES[w[0]]]
        words = kept or words

    tokens = []
    many = len(words) > 1
    for script, text, raw, hyphen, dotted in words:
        letters = text.replace("'", "")
        is_initial = many and (len(letters) == 1 or (dotted and script == "la" and letters in _LATIN_INITIALS)
                               or (dotted and script == "cy" and letters == "дж"))
        tokens.append(Token(script, text, raw, "initial" if is_initial else "name",
                            lang if script == "cy" else None, hyphen))
    return _mark_patronymics(tokens)


def _mark_patronymics(tokens: list) -> tuple:
    n = len(tokens)
    if n < 2:
        return tuple(tokens)
    compound = set()
    for i, t in enumerate(tokens):
        if t.hyphen:
            compound.update((i - 1, i))
    shaped = {}
    for i, t in enumerate(tokens):
        if t.kind == "name" and i not in compound:
            pat = patronymic_of(t.seq)
            if pat:
                shaped[i] = pat[0]
    chosen = {i for i, g in shaped.items() if g == "f"}       # -ivna / -ovna is never a surname
    male = [i for i, g in shaped.items() if g == "m"]
    if male and n >= 3 and not chosen:
        # -ovych may be a surname (Abramovich): the patronymic follows the given name
        pick = next((i for i in male if i > 0 and (i - 1) not in male), None)
        if pick is not None and pick == n - 1:
            before = [t for t in tokens[:pick] if t.kind == "name"]
            if len(before) >= 2 and all(lexicon.is_given_name(t.seq) for t in before):
                pick = None                                   # "Anna Maria Abramovich"
        if pick is not None:
            chosen.add(pick)
    if not chosen:
        return tuple(tokens)
    return tuple(
        Token(t.script, t.text, t.display, "patronymic", t.lang, t.hyphen) if i in chosen else t
        for i, t in enumerate(tokens)
    )
