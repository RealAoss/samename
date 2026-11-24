# samename

**Match East Slavic personal names across scripts, romanizations and languages.**
`Володимир Зеленський` = `Vladimir Zelensky` = `Wolodymyr Selenskyj` = `Уладзімір Зяленскі`,
but `Oleksandr` ≠ `Oleksii` and `Ivanov` ≠ `Ivanova`.

Ukrainian, Russian and Belarusian names, written in Cyrillic or in any of the
common Latin romanizations. Pure Python, zero dependencies, works offline.

```python
>>> import samename
>>> samename.is_match("Володимир Олександрович Зеленський", "Dr. Vladimir Zelensky")
True
>>> samename.is_match("Oleksandr Kovalenko", "Oleksii Kovalenko")
False
>>> print(samename.compare("SHEVCHENKO, Taras H.", "Тарас Григорович Шевченко").explain())
score 0.98  (strong)
  Taras  ~  Тарас   1.00
  H  ~  Григорович   0.90
  SHEVCHENKO  ~  Шевченко   1.00
```

## Why this exists

One East Slavic name has many legitimate spellings. The same person is
`Сергій` in a Ukrainian passport, `Сергей` in an older Russian-language
document and `Сяргей` in a Belarusian one; in Latin script he is Serhii,
Serhiy, Sergey, Sergei, Sergej, Sergueï or Siarhei, depending on the country,
the decade and the romanization standard the clerk happened to use. German,
French and Polish conventions add Schewtschenko, Chevtchenko and Szewczenko
for one and the same `Шевченко`.

Software that compares names as plain strings gets this wrong in both
directions:

- **Refugee registration, family tracing and humanitarian aid** fail to link
  records of one person taken by different agencies in different scripts.
- **Hospitals, universities and HR systems** create duplicate records, or
  cannot join a Cyrillic record to its passport-spelling twin.
- **Banks and sanctions screening** flag innocent people whose name merely
  resembles a listed one, because generic fuzzy matching cannot tell
  *Oleksandr* from *Oleksii* or *Ivanov* from *Ivanova*.
- **Archives, genealogy and libraries** hold the same author under five
  romanizations.

`samename` is a small library you can read in an afternoon and drop into any
pipeline. It is a sibling of [ismatch](https://github.com/RealAoss/ismatch),
which does the same job for Arabic names.

## What it understands

| Phenomenon | Example |
|---|---|
| Romanization systems (English, German, French, Polish, scientific) | `Шевченко` ↔ Shevchenko / Ševčenko / Szewczenko / Schewtschenko / Chevtchenko |
| The letters щ, ж, х, ц, ч in every convention | `Хрущёв` ↔ Khrushchev / Chruschtschow / Khrouchtchev / Hruščëv |
| г as *h* or *g* | `Григорій` ↔ Hryhorii / Grigory · `Згурський` ↔ Zghurskyi |
| One given name in three languages | `Володимир` ↔ `Владимир` ↔ `Уладзімір` · `Микола` ↔ Nikolai |
| Western forms listed in the lexicon | `Олександр` ↔ Alexander · `Євген` ↔ Eugene · `Андрій` ↔ Andrew |
| Belarusian spelling (akanye, ў, дз, ц) | `Іваноў` ↔ Ivanou · `Яўген` ↔ Yauhen · `Ціханоўская` ↔ Tikhanovskaya |
| Surname endings | `Зеленський` ↔ Zelensky / Zelenskyy / Zelenskij · `Ковальська` ↔ Kovalskaya |
| ё written as е, soft signs, apostrophes, stress marks | `Хрущёв` ↔ `Хрущев` · `Мар'яна` ↔ `Мар’яна` |
| Patronymics across languages | `Миколайович` ↔ Nikolaevich · `Іванівна` ↔ Ivanovna · `Іван Якович Франко` ↔ `Иван Яковлевич Франко` |
| Name order, omitted patronymic | "SHEVCHENKO, Taras" ↔ `Тарас Григорович Шевченко` |
| Initials, spaced or glued | `Шевченко Т. Г.` ↔ Taras Shevchenko · "Yu. Andrukhovych" ↔ `Юрій Андрухович` |
| Titles | `пані Олена Петренко` ↔ Dr. Olena Petrenko |
| Hyphenated and joined parts | `Нечуй-Левицький` ↔ Nechui-Levytskyi · `Анна-Марія` ↔ Annamaria |
| Latin look-alike letters typed into a Cyrillic word | `Iвaн` (Latin I, a) ↔ `Іван` |
| Diminutives *(opt-in)* | Sasha ↔ `Олександр` with `diminutives=True` |

And, just as important, what it refuses to merge:

| Different names | Why they are hard |
|---|---|
| `Олександр` Oleksandr ≠ `Олексій` Oleksii | shared first half |
| `Марія` Mariia ≠ `Марина` Maryna | one consonant apart |
| `Ігор` Ihor ≠ `Єгор` Yehor | one letter apart |
| `Олександр` ≠ `Олександра` · Ivan ≠ Ivanna | masculine / feminine given name |
| Ivanov ≠ Ivanova · `Ковальський` ≠ `Ковальська` | masculine / feminine surname: two people (opt out with `gender_insensitive_surnames=True`) |
| Shevchenko ≠ Shevchuk · Koval ≠ Kovalenko | same root, different surname |
| `Петрович` ≠ `Павлович` · `Іванович` ≠ `Іванівна` | different father; brother and sister |
| Petro Ivanov ≠ Ivan Petrov | same roots, swapped roles |
| Ivan **Petrovych** Shevchenko ≠ Ivan **Mykolaiovych** Shevchenko | one different part = another person |

## How it works

1. **Parse** the name: strip titles and stress marks, unify apostrophes, move
   a "SURNAME, Given" head to the end, recognise initials and patronymics.
2. **Phonemise** every part into a small script-independent alphabet. Cyrillic
   letters and Latin digraphs (`shch`, `sch`, `tsch`, `cz`, `kh`, `zh` ...)
   map onto the same consonants and vowels; an ambiguous Latin spelling such
   as `ch` keeps its alternative readings.
3. **Align** two parts with a weighted edit distance whose costs model how
   these names really vary: `i`/`y` is nearly free, `g`/`h` and `v`/`w` are
   cheap, a dropped glide is cheap where romanizations drop it, and a missing
   final `a` is expensive because it marks a feminine form.
4. **Consult a lexicon** of about 370 given names (plus about 100
   diminutives). It links the Ukrainian, Russian and Belarusian forms of one
   name, and knows that some similar spellings are different names.
5. **Assign** the parts of one full name to the parts of the other, tolerate
   reordering and an omitted patronymic, and punish a clearly different part.

No machine learning, no model download: the result is deterministic and every
score can be explained (`Match.explain()`).

## Accuracy

`python bench/run.py` compares `samename` with the approaches people usually
reach for. Each baseline gets the **best possible threshold for that data**;
`samename` uses its fixed default (0.85).

| Set | Pairs | Method | Precision | Recall | F1 |
|---|---|---|---|---|---|
| **Blind** (run once, never tuned on) | 8,575 | Levenshtein | 0.794 | 0.507 | 0.618 |
| | | Transliterate + Levenshtein | 0.880 | 0.931 | 0.905 |
| | | Transliterate + consonant skeleton | 0.969 | 0.382 | 0.548 |
| | | **samename** | **0.996** | **0.987** | **0.992** |
| Development (tuned on) | 5,449 | Levenshtein | 0.751 | 0.482 | 0.587 |
| | | Transliterate + Levenshtein | 0.853 | 0.915 | 0.883 |
| | | Transliterate + consonant skeleton | 0.943 | 0.495 | 0.649 |
| | | **samename** | 0.999 | 1.000 | 1.000 |

The blind set (`bench/blind.py`, 78 name groups and 143 deliberately
confusable pairs) was written by someone who had not seen the matcher's code,
tests or documentation. It was run once and the matcher was not changed
afterwards, so its 27 misses and 8 false alarms are all still there
(`python bench/run.py --errors` prints them). Examples: the patronymics
`Миколаївна` / `Николаевна` and `Володимирович` / `Уладзіміравіч` are missed,
the Polish form `Kazimierz Malewicz` is not linked to `Казимир Малевич`, and
`Кличко` / `Клочко`, `Костенко` / `Косенко` and `Zhanna` / `Yana` are wrongly
merged.

Read these numbers with care:

- Only the **blind** row is an honest estimate, and even that set was written
  for this project rather than collected from real records.

- The development set was **written by the project authors, who also tuned
  the matcher on it**. Its numbers are a regression benchmark, not an
  evaluation, and they are optimistic: expect clearly lower figures on any
  data the matcher has not seen.
- It is not real-world data. It is full of deliberately confusable pairs, but
  real records are messier (typos, OCR errors, missing parts, mixed scripts).
- One development pair is still wrong and is left wrong on purpose rather
  than special-cased: Savchenko / Shevchenko scores 0.86.
- If you have labelled name pairs from a real system and can share them (or
  just the aggregate results), please open an issue. That is the most
  valuable contribution this project can receive.

Speed on a laptop, single thread, CPython 3.14 (`python bench/speed.py`,
synthetic data: 4,000 distinct full names built from the lexicon plus 1,000
planted Latin-script duplicates): about 0.35 ms per comparison of two unseen
three-part names (about 0.05 ms once the name parts are cached); building the
index of 5,000 names takes about 0.1 s; a search in it takes about 2 ms;
de-duplicating all 5,000 names takes about 4.5 s and groups all 1,000 planted
duplicates with their original. An exhaustive search (no blocking) takes
about 0.6 s.

## Install

```bash
pip install git+https://github.com/RealAoss/samename
```

or clone the repository and run `pip install .`. Python 3.10+.

## Usage

### Compare two names

```python
>>> import samename
>>> m = samename.compare("Сергій Вікторович Жадан", "Zhadan Serhij")
>>> round(m.score, 2)          # 0.0 - 1.0
0.92
>>> m.is_match                 # score >= threshold (default 0.85)
True
>>> m.level                    # 'strong' | 'probable' | 'possible' | 'no'
'probable'
>>> m.pairs                    # (part_a, part_b, similarity)
[('Жадан', 'Zhadan', 1.0), ('Сергій', 'Serhij', 1.0)]
>>> m.unmatched_a, m.reordered
(['Вікторович'], True)
>>> m.to_dict()                # JSON-ready
{'score': 0.9238, 'is_match': True, 'level': 'probable', 'pairs': [{'a': 'Жадан', 'b': 'Zhadan', 'score': 1.0}, {'a': 'Сергій', 'b': 'Serhij', 'score': 1.0}], 'unmatched_a': ['Вікторович'], 'unmatched_b': [], 'reordered': True, 'notes': []}

>>> samename.score("Hanna Kovalska", "Ганна Ковальська")                    # just the number
1.0
>>> samename.is_match("Hanna", "Анна"), samename.is_match("Hanna", "Анна", threshold=0.95)
(True, False)
```

Choosing a threshold: `0.85` balances both error types. For anything that
blocks a person (sanctions, fraud), keep a human in the loop and treat
`possible` (0.70-0.85) as "needs review", never as a decision.

### Options

```python
>>> samename.is_match("Sasha Kovalenko", "Олександр Коваленко")
False
>>> samename.is_match("Sasha Kovalenko", "Олександр Коваленко", diminutives=True)
True

>>> print(samename.compare("Ivanov", "Ivanova").explain())
score 0.57  (no)
  Ivanov  ~  Ivanova   0.57
  (Ivanov / Ivanova: masculine and feminine form of one surname)
>>> samename.is_match("Ivanov", "Ivanova", gender_insensitive_surnames=True)   # linking a family
True

>>> samename.score("Микола", "Николай")                                   # one name, two languages
0.92
>>> round(samename.score("Микола", "Николай", cross_language=False), 2)   # spelling only
0.58
```

### Search a list

```python
>>> idx = samename.NameIndex(["Тарас Шевченко", "Olena Kovalenko", "Сергей Иванов"])
>>> idx.add("Юрій Андрухович", id="author-0042")
>>> idx.search("Shevchenko, Taras")
[('Тарас Шевченко', 1.0)]
>>> [(name, round(score, 2)) for name, score in idx.search("Serhii Ivanov")]
[('Сергей Иванов', 0.96)]
>>> [(id, round(score, 2)) for id, score in idx.search_ids("Yuri Andrukhovych")]
[('author-0042', 0.99)]
```

`NameIndex` takes the same options as `compare`. Candidates are found through
blocking keys (two name parts must share a key); pass `exhaustive=True` to
`search` to score every stored name instead.

### Find duplicates

```python
>>> names = ["Тарас Шевченко", "Olena Kovalenko", "Taras Shevchenko", "Олена Коваленко", "Oleksii Kovalenko"]
>>> samename.dedupe(names)     # indexes into names
[[0, 2], [1, 3]]
```

Grouping is transitive (single linkage): review large groups before merging
records.

### Blocking keys for databases

```python
>>> samename.keys("Шевченко")
('JVJNK',)
>>> samename.keys("Szewczenko")
('JVJNK',)
>>> samename.keys("Shevchenko")      # "ch" is ambiguous in Latin script: two keys
('JVJNK', 'JVKNK')
>>> samename.keys("Володимир")
('VLDMR', '=VOLODYMYR')
>>> samename.keys("Уладзімір")
('LDMR', '=VOLODYMYR')
```

Store the keys in an indexed column to fetch candidates with plain SQL, then
score the candidates with `compare`. Keys starting with `=` come from the
lexicon and link the forms of one given name across languages.

### Command line

```console
$ samename compare "Володимир Зеленський" "Vladimir Zelensky"
score 0.95  (strong)
  Володимир  ~  Vladimir   0.92
  Зеленський  ~  Zelensky   0.99
$ samename compare "Oleksandr Kovalenko" "Oleksii Kovalenko"
score 0.56  (no)
  Oleksandr  ~  Oleksii   0.52
  Kovalenko  ~  Kovalenko   1.00
$ samename key "Тарас Шевченко"
TRS =TARAS JVJNK
$ samename search tests/people.csv "Шевченко Тарас" --column full_name
0.97  Taras Shevchenko
0.92  Тарас Григорович Шевченко
$ samename dedupe tests/people.csv --column full_name
# group 1
  Тарас Григорович Шевченко
  Taras Shevchenko
# group 2
  Olena Kovalenko
  Kovalenko, Olena
# group 3
  Сергей Иванов
  Serhii Ivanov
3 group(s) of likely duplicates among 8 names
```

`compare` and `search` exit with 0 for a match / at least one hit and 1
otherwise; usage and file errors exit with 2. Add `--json` to `compare`,
`search` or `dedupe` for machine-readable output, and `--diminutives`,
`--gender-insensitive-surnames` or `--no-cross-language` for the options
above. Input files are UTF-8: a text file with one name per line, or a CSV /
TSV file with `--column` (a header name, or a 0-based number for files
without a header row). Without installing, run `python -m samename ...` with
`src` on `PYTHONPATH`.

## Limitations

Be aware of these before relying on a score:

- **A name is not an identity.** Two people can share a full name. Combine
  the score with date of birth, place, document number or other evidence.
- **Only East Slavic names, only Cyrillic and Latin script.** Text in any
  other script (Arabic, Greek, Chinese, Georgian ...) is ignored and scores
  0. Names from other cultures written in Latin or Cyrillic are compared
  phonetically with no special knowledge.
- **Short and single-part names** carry little information; `Taras` alone
  never "matches" `Taras Shevchenko`. A patronymic standing alone is treated
  like any other word.
- **Extra parts are forgiven when two parts agree**: `Olena Petrenko`
  matches `Olena Kovalenko-Petrenko` (0.91) and `Ivan Franko` matches
  `Ivan Franko Jr` (0.91). Initials are weak evidence too:
  `T. H. Shevchenko` matches every T. H. Shevchenko, whatever the names
  behind the initials.
- **Given names outside the lexicon** are matched by spelling alone. Western
  equivalents that are not listed do not match: Leo / `Лев`, Jeanne /
  `Жанна`, Nick / `Микола`. Diminutives (Sasha, Katya) match only with
  `diminutives=True`, and only the listed ones.
- **Surnames are matched by rules only.** Close surnames can collide:
  Savchenko / Shevchenko scores 0.86 and is wrongly accepted.
- **Latin digraphs are ambiguous.** `sch` is read as ш / щ (German,
  simplified Ukrainian), so a surname with a real с + ч cluster does not
  match its plain romanization (`Тарасчук` / Taraschuk scores 0.81).
- **The lexicon takes sides** where usage is disputed: `Ганна` and `Анна`
  are one name, `Марта` and `Марфа` are two, `Ліна` and `Лена` are two.
- **Typos are not modelled.** The costs describe romanization and language
  differences, not keyboard slips or OCR errors.
- **Known misses from the blind set** (see Accuracy): cross-language
  patronymics standing alone, Polish cognate forms of given names, and
  surnames that differ by one inner letter (`Кличко` / `Клочко`).

## Contributing

The easiest high-impact contribution is a line in
[`src/samename/lexicon.py`](src/samename/lexicon.py): a given name with its
Ukrainian, Russian and Belarusian forms. See [CONTRIBUTING.md](CONTRIBUTING.md).

```bash
python -m unittest discover -s tests     # tests
python bench/run.py --errors             # benchmark and every wrong pair
python bench/speed.py                    # speed on synthetic data
```

## License

MIT
