import doctest
import io
import json
import os
import sys
import unittest
from contextlib import redirect_stderr, redirect_stdout

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "src"))
sys.path.insert(0, os.path.join(ROOT, "bench"))

import samename  # noqa: E402
import samename.index  # noqa: E402
import samename.match  # noqa: E402
from samename.cli import main as cli  # noqa: E402
from samename.parse import parse_name  # noqa: E402

PEOPLE_CSV = os.path.join(ROOT, "tests", "people.csv")   # read-only fixture; tests write nothing


class SameName(unittest.TestCase):
    def assertSame(self, a, b, **options):
        m = samename.compare(a, b, **options)
        self.assertTrue(m.is_match, f"{a!r} vs {b!r} scored {m.score:.2f}\n{m.explain()}")

    def test_ukrainian_to_latin(self):
        for latin in ("Shevchenko", "Ševčenko", "Szewczenko", "Schewtschenko", "Chevtchenko"):
            self.assertSame("Шевченко", latin)
        for latin in ("Zelenskyy", "Zelenskyi", "Zelensky", "Zelenskiy", "Zelenskij", "Selenskyj"):
            self.assertSame("Зеленський", latin)
        self.assertSame("Згурський", "Zghurskyi")
        self.assertSame("Грушевський", "Hrushevsky")

    def test_russian_to_latin(self):
        for latin in ("Khrushchev", "Chruschtschow", "Khrouchtchev", "Hruščëv", "Chruszczow"):
            self.assertSame("Хрущёв", latin)
        for latin in ("Tchaikovsky", "Tschaikowski", "Čajkovskij", "Czajkowski"):
            self.assertSame("Чайковский", latin)
        self.assertSame("Жуков", "Joukov")
        self.assertSame("Ельцин", "Yeltsin")
        self.assertSame("Солженицын", "Solschenizyn")

    def test_belarusian_to_latin(self):
        self.assertSame("Лукашэнка", "Lukashenka")
        self.assertSame("Іваноў", "Ivanou")
        self.assertSame("Яўген", "Yauhen")
        self.assertSame("Святлана Ціханоўская", "Sviatlana Tsikhanouskaya")

    def test_latin_to_latin(self):
        self.assertSame("Sergey", "Sergei")
        self.assertSame("Yuriy", "Iurii")
        self.assertSame("Tatiana", "Tatyana")
        self.assertSame("Kovalyov", "Kovaliov")
        self.assertSame("Khmelnytskyi", "Chmielnicki")       # Polish -cki

    def test_given_names_across_languages(self):
        self.assertSame("Володимир", "Владимир")
        self.assertSame("Володимир", "Уладзімір")
        self.assertSame("Микола", "Nikolai")
        self.assertSame("Олександр", "Alexander")
        self.assertSame("Сергій", "Siarhei")
        self.assertSame("Євген", "Eugene")
        self.assertSame("Evgeny", "Yauhen")
        self.assertSame("Олена", "Yelena")
        self.assertSame("Пётр", "Петро")

    def test_cyrillic_spelling_variants(self):
        self.assertSame("Хрущёв", "Хрущев")                  # ё written as е
        self.assertSame("Ковальов", "Ковалёв")
        self.assertSame("Мар'яна", "Мар’яна")                # apostrophe variants
        self.assertSame("Володи́мир", "Володимир")            # stress mark
        self.assertSame("Iвaн", "Іван")                      # Latin look-alike letters
        self.assertSame("ШЕВЧЕНКО", "шевченко")

    def test_surname_endings(self):
        self.assertSame("Ковальська", "Kovalskaya")
        self.assertSame("Білий", "Белый")
        self.assertSame("Толстой", "Tolstoi")
        self.assertSame("Іванов", "Ivanoff")

    def test_patronymics(self):
        self.assertSame("Іванович", "Ivanovitch")
        self.assertSame("Іванівна", "Ivanovna")
        self.assertSame("Микола Миколайович Петренко", "Nikolai Nikolaevich Petrenko")
        self.assertSame("Пётр Ильич Чайковский", "Petro Illich Tchaikovsky")
        self.assertSame("Іван Якович Франко", "Иван Яковлевич Франко")   # Yakiv -> Yakovych

    def test_name_order(self):
        self.assertSame("Тарас Григорович Шевченко", "Шевченко Тарас Григорович")
        self.assertSame("Тарас Шевченко", "SHEVCHENKO, Taras")
        self.assertSame("Zhadan Serhii Viktorovych", "Сергій Вікторович Жадан")
        self.assertTrue(samename.compare("Taras Shevchenko", "Shevchenko Taras").reordered)

    def test_missing_patronymic(self):
        self.assertSame("Тарас Григорович Шевченко", "Taras Shevchenko")
        self.assertSame("Володимир Олександрович Зеленський", "Vladimir Zelensky")
        m = samename.compare("Сергій Вікторович Жадан", "Serhiy Zhadan")
        self.assertEqual(m.unmatched_a, ["Вікторович"])
        self.assertEqual(m.unmatched_b, [])

    def test_initials(self):
        self.assertSame("Шевченко Т. Г.", "Taras Hryhorovych Shevchenko")
        self.assertSame("T.H. Shevchenko", "Тарас Григорович Шевченко")
        self.assertSame("Yu. Andrukhovych", "Юрій Андрухович")
        self.assertSame("I.I. Ivanov", "Иванов И. И.")
        self.assertEqual(parse_name("Шевченко Т. Г.")[1].kind, "initial")

    def test_titles(self):
        self.assertSame("пані Олена Петренко", "Dr. Olena Petrenko")
        self.assertSame("проф. Іван Франко", "Mr Ivan Franko")
        self.assertEqual([t.display for t in parse_name("Dr. Olena Petrenko")], ["Olena", "Petrenko"])

    def test_hyphenated_and_joined_parts(self):
        self.assertSame("Іван Нечуй-Левицький", "Nechuy-Levytsky Ivan")
        self.assertSame("Анна-Марія Коваль", "Annamaria Koval")

    def test_options(self):
        self.assertFalse(samename.is_match("Sasha Kovalenko", "Олександр Коваленко"))
        self.assertSame("Sasha Kovalenko", "Олександр Коваленко", diminutives=True)
        self.assertFalse(samename.is_match("Ivanov", "Ivanova"))
        self.assertSame("Ivanov", "Ivanova", gender_insensitive_surnames=True)
        self.assertSame("Ковальський", "Kovalska", gender_insensitive_surnames=True)
        self.assertFalse(samename.is_match("Микола", "Николай", cross_language=False))


class DifferentName(unittest.TestCase):
    def assertDifferent(self, a, b):
        m = samename.compare(a, b)
        self.assertFalse(m.is_match, f"{a!r} vs {b!r} scored {m.score:.2f}\n{m.explain()}")

    def test_similar_given_names(self):
        self.assertDifferent("Oleksandr", "Oleksii")
        self.assertDifferent("Александр", "Алексей")
        self.assertDifferent("Марія", "Марина")
        self.assertDifferent("Юрій", "Юлія")
        self.assertDifferent("Ігор", "Єгор")
        self.assertDifferent("Natalia", "Nadia")
        self.assertDifferent("Marta", "Marfa")
        self.assertDifferent("Vladyslav", "Volodymyr")

    def test_masculine_and_feminine_given_names(self):
        self.assertDifferent("Олександр", "Олександра")
        self.assertDifferent("Ivan", "Ivanna")
        self.assertDifferent("Yevhen", "Yevhenia")
        self.assertDifferent("Viktor", "Viktoria")

    def test_surname_gender(self):
        self.assertDifferent("Ivanov", "Ivanova")
        self.assertDifferent("Ковальський", "Ковальська")
        self.assertDifferent("Tolstoy", "Tolstaya")
        self.assertIn("masculine and feminine", samename.compare("Ivanov", "Ivanova").explain())

    def test_neighbouring_surnames(self):
        self.assertDifferent("Shevchenko", "Shevchuk")
        self.assertDifferent("Koval", "Kovalenko")
        self.assertDifferent("Kovalchuk", "Kovalchyk")
        self.assertDifferent("Морозов", "Мороз")
        self.assertDifferent("Petrenko", "Petrov")

    def test_patronymics(self):
        self.assertDifferent("Петрович", "Павлович")
        self.assertDifferent("Іванович", "Іванівна")
        self.assertDifferent("Ivan Petrovych Shevchenko", "Ivan Mykolaiovych Shevchenko")

    def test_one_different_part_is_a_different_person(self):
        self.assertDifferent("Taras Shevchenko", "Taras Kovalenko")
        self.assertDifferent("Oleksandr Kovalenko", "Oleksii Kovalenko")
        self.assertDifferent("Dmytro Kuleba", "Dmytro Kulyk")
        self.assertDifferent("Олександр Іванов", "Олександра Іванова")
        self.assertDifferent("T. Shevchenko", "O. Shevchenko")

    def test_swapped_roles(self):
        self.assertDifferent("Petro Ivanov", "Ivan Petrov")
        self.assertDifferent("Олег Ігорович Ткаченко", "Ігор Олегович Ткаченко")

    def test_single_part_is_weak_evidence(self):
        self.assertDifferent("Taras", "Taras Shevchenko")
        self.assertDifferent("Шевченко", "Шевченко Тарас Григорович")


class EdgeCases(unittest.TestCase):
    def test_empty(self):
        self.assertEqual(samename.score("", ""), 0.0)
        self.assertEqual(samename.score("", "Іван"), 0.0)
        self.assertFalse(samename.is_match("   ", "Ivan"))
        self.assertEqual(samename.keys(""), ())
        self.assertEqual(parse_name(""), ())

    def test_digits_and_punctuation(self):
        self.assertEqual(samename.score("12345", "12345"), 0.0)
        self.assertEqual(samename.score("123 456", "Ivan"), 0.0)
        self.assertEqual(samename.score("!!! ... ---", "???"), 0.0)
        self.assertEqual(samename.keys("... 42"), ())
        self.assertTrue(samename.is_match("Ivanov Ivan 1980", "Иван Иванов"))   # digits are ignored
        self.assertTrue(samename.is_match("Ivan\tPetrov\n", "Ivan  Petrov"))

    def test_not_a_string(self):
        self.assertEqual(samename.score(None, "Ivan"), 0.0)
        self.assertEqual(parse_name(42), ())

    def test_unsupported_scripts_score_zero(self):
        for other in ("محمد", "李小龙", "Ιβάν"):
            self.assertEqual(samename.score(other, "Ivan"), 0.0)

    def test_very_long_input(self):
        self.assertEqual(samename.score(" ".join(["Іван"] * 40), " ".join(["Ivan"] * 40)), 1.0)
        s = samename.score("Іван" * 500, "Ivan")
        self.assertTrue(0.0 <= s < 0.5)
        self.assertEqual(len(samename.keys("Шевченко" * 200)), 1)

    def test_single_letters(self):
        self.assertEqual(samename.score("І", "І"), 1.0)
        self.assertEqual(samename.score("a", "b"), 0.0)


class Api(unittest.TestCase):
    def test_score_range_and_symmetry(self):
        pairs = [("Тарас Шевченко", "Shevchenko Taras"), ("Олена Петренко", "Petrenko O."),
                 ("Ivan Franko", "Franko Ivan Yakovych"), ("x", "Іван"), ("", "Іван"),
                 ("Oleksandr Kovalenko", "Oleksii Kovalenko")]
        for a, b in pairs:
            s1, s2 = samename.score(a, b), samename.score(b, a)
            self.assertTrue(0.0 <= s1 <= 1.0)
            self.assertAlmostEqual(s1, s2, places=6)

    def test_identity(self):
        for name in ("Тарас Григорович Шевченко", "Sviatlana Tsikhanouskaya", "Пётр Ильич Чайковский", "Іваноў"):
            self.assertAlmostEqual(samename.score(name, name), 1.0)

    def test_explain(self):
        text = samename.compare("SHEVCHENKO, Taras H.", "Тарас Григорович Шевченко").explain()
        lines = text.splitlines()
        self.assertTrue(lines[0].startswith("score 0.9"))
        self.assertIn("(strong)", lines[0])
        self.assertIn("Taras  ~  Тарас", text)
        self.assertIn("SHEVCHENKO  ~  Шевченко", text)
        text = samename.compare("Тарас Григорович Шевченко", "Shevchenko Taras").explain()
        self.assertIn("only in first:  Григорович", text)
        self.assertIn("different order", text)
        self.assertEqual(samename.compare("", "").explain(), "score 0.00  (no)")

    def test_to_dict(self):
        m = samename.compare("Сергій Вікторович Жадан", "Zhadan Serhij")
        d = m.to_dict()
        self.assertEqual(set(d), {"score", "is_match", "level", "pairs", "unmatched_a", "unmatched_b",
                                  "reordered", "notes"})
        self.assertEqual(d["unmatched_a"], ["Вікторович"])
        self.assertEqual(d["pairs"][0], {"a": "Жадан", "b": "Zhadan", "score": 1.0})
        self.assertTrue(d["is_match"] and d["reordered"])
        self.assertEqual(json.loads(json.dumps(d, ensure_ascii=False)), d)
        self.assertEqual(bool(m), m.is_match)
        self.assertEqual(samename.compare("Ivanov", "Ivanova").to_dict()["notes"],
                         ["Ivanov / Ivanova: masculine and feminine form of one surname"])

    def test_levels_and_threshold(self):
        self.assertEqual(samename.compare("Ivan Franko", "Іван Франко").level, "strong")
        self.assertEqual(samename.compare("Ivan", "Olha").level, "no")
        self.assertTrue(samename.is_match("Hanna", "Анна"))
        self.assertFalse(samename.is_match("Hanna", "Анна", threshold=0.95))
        self.assertTrue(samename.is_match("Oleksandr", "Oleksii", threshold=0.5))
        self.assertEqual(samename.DEFAULT_THRESHOLD, 0.85)

    def test_keys_are_script_independent(self):
        self.assertEqual(samename.keys("Шевченко"), ("JVJNK",))
        self.assertEqual(samename.keys("Szewczenko"), ("JVJNK",))
        self.assertIn("JVJNK", samename.keys("Shevchenko"))
        self.assertEqual(samename.keys("Володимир"), ("VLDMR", "=VOLODYMYR"))
        self.assertEqual(samename.keys("Vladimir"), samename.keys("Володимир"))
        self.assertIn("=VOLODYMYR", samename.keys("Уладзімір"))
        self.assertEqual(samename.keys("Vladimir", cross_language=False), ("VLDMR",))
        self.assertEqual(samename.keys("Гнатчук"), samename.keys("Gnatchuk"))
        self.assertTrue(set(samename.keys("Яўген")) & set(samename.keys("Yauhen")))

    def test_keys_of_full_names(self):
        k = samename.keys("Тарас Григорович Шевченко")
        self.assertEqual(k, ("TRS", "=TARAS", "KRKRVJ", "=HRYHORII~", "JVJNK"))
        self.assertEqual(samename.keys("Шевченко Т. Г."), ("JVJNK",))          # initials give no key
        self.assertIn("=OLEKSANDR", samename.keys("Sasha", diminutives=True))
        self.assertNotIn("=OLEKSANDR", samename.keys("Sasha"))

    def test_parse(self):
        toks = parse_name("Taras Hryhorovych Shevchenko")
        self.assertEqual([t.kind for t in toks], ["name", "patronymic", "name"])
        toks = parse_name("ШЕВЧЕНКО, Тарас")
        self.assertEqual([t.display for t in toks], ["Тарас", "ШЕВЧЕНКО"])
        self.assertEqual([t.script for t in parse_name("Іван Franko")], ["cy", "la"])
        self.assertEqual([t.kind for t in parse_name("Roman Abramovich")], ["name", "name"])

    def test_docstring_examples(self):
        for module in (samename, samename.match, samename.index):
            failed, attempted = doctest.testmod(module)
            self.assertEqual(failed, 0)
            self.assertGreater(attempted, 0)


class Readme(unittest.TestCase):
    def test_python_examples_print_what_the_readme_says(self):
        with open(os.path.join(ROOT, "README.md"), encoding="utf-8") as fh:
            text = "\n".join("" if line.startswith("```") else line for line in fh.read().splitlines())
        test = doctest.DocTestParser().get_doctest(text, {}, "README.md", "README.md", 0)
        self.assertGreater(len(test.examples), 20)
        report = []
        runner = doctest.DocTestRunner(verbose=False)
        runner.run(test, out=report.append)
        self.assertEqual(runner.failures, 0, "".join(report))


class IndexAndDedupe(unittest.TestCase):
    NAMES = [
        "Тарас Григорович Шевченко", "Olena Kovalenko", "Сергей Иванов", "Леся Українка", "Dmytro Kuleba",
        "Taras Shevchenko", "Олена Коваленко", "Serhii Ivanov", "Oleksii Kovalenko", "Шевченко Т. Г.",
        "Сергей Иванова",
    ]

    def test_search(self):
        idx = samename.NameIndex(self.NAMES)
        self.assertEqual(len(idx), len(self.NAMES))
        hits = idx.search("Sergey Ivanov")
        self.assertEqual({n for n, _ in hits}, {"Сергей Иванов", "Serhii Ivanov"})
        self.assertEqual(hits[0], ("Сергей Иванов", 1.0))
        self.assertTrue(all(hits[i][1] >= hits[i + 1][1] for i in range(len(hits) - 1)))
        self.assertEqual(idx.search("Lesya Ukrainka")[0][0], "Леся Українка")
        self.assertEqual(idx.search("Zzzz Qqqq"), [])
        self.assertEqual(idx.search(""), [])

    def test_search_limit_min_score_exhaustive(self):
        idx = samename.NameIndex(self.NAMES)
        self.assertEqual(len(idx.search("Шевченко Тарас", limit=1)), 1)
        self.assertEqual({n for n, _ in idx.search("Шевченко Тарас")},
                         {"Тарас Григорович Шевченко", "Taras Shevchenko", "Шевченко Т. Г."})
        self.assertEqual(idx.search("Olena Kovalenko", min_score=0.99),
                         [("Olena Kovalenko", 1.0), ("Олена Коваленко", 1.0)])
        self.assertEqual(idx.search("Sergey Ivanov", exhaustive=True), idx.search("Sergey Ivanov"))

    def test_search_ids(self):
        idx = samename.NameIndex()
        idx.add("Юрій Андрухович", id="author-0042")
        idx.add("Сергій Жадан")
        self.assertEqual(idx.search_ids("Yuri Andrukhovych")[0][0], "author-0042")
        self.assertEqual(idx.search_ids("Serhiy Zhadan")[0][0], 1)             # default id: position

    def test_index_options(self):
        names = ["Олександр Коваленко", "Петро Іванов"]
        self.assertEqual(samename.NameIndex(names).search("Sasha Kovalenko", min_score=0.85), [])
        self.assertEqual(samename.NameIndex(names, diminutives=True).search("Sasha Kovalenko")[0][0], names[0])
        idx = samename.NameIndex(names, gender_insensitive_surnames=True)
        self.assertEqual(idx.search("Petro Ivanova")[0][0], names[1])

    def test_dedupe(self):
        clusters = [sorted(self.NAMES[i] for i in g) for g in samename.dedupe(self.NAMES)]
        self.assertIn(sorted(["Тарас Григорович Шевченко", "Taras Shevchenko", "Шевченко Т. Г."]), clusters)
        self.assertIn(sorted(["Olena Kovalenko", "Олена Коваленко"]), clusters)
        self.assertIn(sorted(["Сергей Иванов", "Serhii Ivanov"]), clusters)
        self.assertEqual(len(clusters), 3)

    def test_dedupe_edge_cases(self):
        self.assertEqual(samename.dedupe([]), [])
        self.assertEqual(samename.dedupe(["Ivan Franko"]), [])
        self.assertEqual(samename.dedupe(["", "", "Ivan Franko", "123"]), [])
        self.assertEqual(samename.dedupe(["Ivanov", "Ivanova"]), [])
        self.assertEqual(samename.dedupe(["Ivanov", "Ivanova"], gender_insensitive_surnames=True), [[0, 1]])
        self.assertEqual(samename.dedupe(iter(["Іван Франко", "x", "Ivan Franko"])), [[0, 2]])


class Cli(unittest.TestCase):
    def run_cli(self, *args):
        out, err = io.StringIO(), io.StringIO()
        with redirect_stdout(out), redirect_stderr(err):
            try:
                code = cli(list(args))
            except SystemExit as exc:
                code = exc.code
        return code, out.getvalue(), err.getvalue()

    def test_compare(self):
        code, out, _ = self.run_cli("compare", "Володимир Зеленський", "Vladimir Zelensky")
        self.assertEqual(code, 0)
        self.assertIn("Володимир  ~  Vladimir", out)
        code, out, _ = self.run_cli("compare", "Oleksandr Kovalenko", "Oleksii Kovalenko")
        self.assertEqual(code, 1)
        self.assertTrue(out.startswith("score 0."))

    def test_compare_json_and_options(self):
        code, out, _ = self.run_cli("compare", "Ivanov", "Ivanova", "--json")
        self.assertEqual(code, 1)
        self.assertFalse(json.loads(out)["is_match"])
        code, out, _ = self.run_cli("compare", "Ivanov", "Ivanova", "--json", "--gender-insensitive-surnames")
        self.assertEqual(code, 0)
        self.assertTrue(json.loads(out)["is_match"])
        self.assertEqual(self.run_cli("compare", "Sasha", "Олександр")[0], 1)
        self.assertEqual(self.run_cli("compare", "Sasha", "Олександр", "--diminutives")[0], 0)
        self.assertEqual(self.run_cli("compare", "Микола", "Николай")[0], 0)
        self.assertEqual(self.run_cli("compare", "Микола", "Николай", "--no-cross-language")[0], 1)
        self.assertEqual(self.run_cli("compare", "Hanna", "Анна", "-t", "0.95")[0], 1)

    def test_key(self):
        self.assertEqual(self.run_cli("key", "Шевченко")[1].strip(), "JVJNK")
        self.assertEqual(self.run_cli("key", "Володимир")[1].strip(), "VLDMR =VOLODYMYR")
        self.assertEqual(self.run_cli("key", "Vladimir", "--no-cross-language")[1].strip(), "VLDMR")
        self.assertEqual(self.run_cli("key", "")[1].strip(), "")

    def test_search(self):
        code, out, _ = self.run_cli("search", PEOPLE_CSV, "Шевченко Тарас", "-c", "full_name")
        self.assertEqual(code, 0)
        self.assertEqual([line.split("  ", 1)[1] for line in out.splitlines()],
                         ["Taras Shevchenko", "Тарас Григорович Шевченко"])
        code, out, _ = self.run_cli("search", PEOPLE_CSV, "Sergey Ivanov", "-c", "1", "--json", "-n", "1")
        self.assertEqual(json.loads(out), [{"name": "Сергей Иванов", "score": 1.0}])
        code, out, _ = self.run_cli("search", PEOPLE_CSV, "Zzzz Qqqq", "-c", "full_name")
        self.assertEqual((code, out), (1, ""))

    def test_dedupe(self):
        code, out, err = self.run_cli("dedupe", PEOPLE_CSV, "-c", "full_name", "--json")
        self.assertEqual(code, 0)
        self.assertEqual(json.loads(out), [
            ["Тарас Григорович Шевченко", "Taras Shevchenko"],
            ["Olena Kovalenko", "Kovalenko, Olena"],
            ["Сергей Иванов", "Serhii Ivanov"],
        ])
        code, out, err = self.run_cli("dedupe", PEOPLE_CSV, "--column", "full_name")
        self.assertIn("# group 1\n  Тарас Григорович Шевченко\n  Taras Shevchenko\n", out)
        self.assertIn("3 group(s) of likely duplicates among 8 names", err)

    def test_errors(self):
        code, out, err = self.run_cli("dedupe", os.path.join(ROOT, "tests", "no-such-file.csv"))
        self.assertEqual((code, out), (2, ""))
        self.assertIn("cannot read", err)
        code, _, err = self.run_cli("search", PEOPLE_CSV, "Olena", "-c", "nope")
        self.assertEqual(code, 2)
        self.assertIn("column 'nope' not found", err)
        code, _, err = self.run_cli("search", PEOPLE_CSV, "Olena")          # CSV with several columns
        self.assertEqual(code, 2)
        self.assertIn("--column", err)
        self.assertEqual(self.run_cli("search", PEOPLE_CSV, "Olena", "-c", "9")[0], 2)
        self.assertEqual(self.run_cli()[0], 2)
        self.assertEqual(self.run_cli("compare", "only-one")[0], 2)

    def test_version(self):
        code, out, _ = self.run_cli("--version")
        self.assertEqual(code, 0)
        self.assertEqual(out.strip(), f"samename {samename.__version__}")


class Benchmark(unittest.TestCase):
    """Regression guard: quality on the development set must not drop."""

    def test_development_set(self):
        import dataset
        from run import build_pairs, prf

        pos, neg = build_pairs(dataset.GROUPS, dataset.DISTINCT)
        p, r, f = prf([samename.score(a, b) for a, b in pos], [samename.score(a, b) for a, b in neg],
                      samename.DEFAULT_THRESHOLD)
        self.assertGreaterEqual(p, 0.99)
        self.assertGreaterEqual(r, 0.98)

    def test_blocking_keeps_every_matching_pair(self):
        import dataset
        from run import build_pairs

        pos, _ = build_pairs(dataset.GROUPS, dataset.DISTINCT)
        lost = [(a, b) for a, b in pos
                if samename.is_match(a, b) and not samename.NameIndex([a]).search(b, min_score=0.85)]
        self.assertLessEqual(len(lost), len(pos) // 100, lost[:5])


if __name__ == "__main__":
    unittest.main()
