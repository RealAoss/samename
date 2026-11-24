# Contributing

Thank you for helping. No setup is needed beyond Python 3.10+; the project has
no dependencies.

```bash
python -m unittest discover -s tests     # must pass
python bench/run.py --errors             # shows every pair the matcher gets wrong
python bench/speed.py                    # speed on synthetic data
```

## Add names to the lexicon (most useful)

Open `src/samename/lexicon.py` and add a line:

```
m|f Canonical [Latin ...] | Ukrainian ... | Russian ... | Belarusian ...
d   Diminutive [Latin ...] | Cyrillic ...  | Canonical name(s) it is short for
```

- `m` / `f` is the gender; the first word is the canonical Latin form, which
  must be unique: `m Serhii Serge | Сергій | Сергей | Сяргей`.
- Use `-` for a language that has no form of its own.
- Plain romanizations of the Cyrillic forms (Serhiy, Sergey, Sergej,
  Siarhei ...) need not be listed; they are recognised phonetically. List
  only Latin forms that are *not* a romanization (Alexander, Eugene, Andrew).
- Two names that are different names get **separate lines**, even if they
  sound close, and so do the masculine and feminine form of one name. That is
  how the matcher learns they differ.
- A `d` line names the full name(s) a diminutive is short for, by their
  canonical form: `d Sasha Sascha | Саша | Oleksandr Oleksandra`.

Regional, older and less common given names are under-represented, and so
are Western equivalents (Leo for Лев). Every line helps.

## Report a wrong result

Open an issue with the two names, what you expected, and the output of:

```bash
samename compare "name one" "name two"
```

## Change the matcher

- Add the failing pairs to `bench/dataset.py` first, then fix.
- Prefer a general rule (a phoneme, a cost, a parsing rule) over a special
  case for one name. A pair that only a special case would fix is better left
  wrong and listed under Limitations in the README.
- **Never tune against `bench/blind.py`.** That file is written by someone who
  has not seen the matcher, so that its numbers stay honest. If a change is
  motivated by a pair in it, move the pair to `dataset.py` and note it in the
  changelog.
- Every Python example in the README is executed by the test suite; if you
  change behaviour, update the README output to what the code really prints.
- Tests must not write to disk; file-based tests read `tests/people.csv`.
- Keep the library dependency-free.

## Real-world data

Labelled pairs from a real system (even a few hundred, even anonymised to
given names only) would improve this project more than anything else. If you
cannot share data, sharing the precision / recall you measured is still
valuable.
