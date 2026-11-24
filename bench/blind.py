"""Blind (held-out) set for East Slavic name matching. NEVER tune on this file.

This set was written without access to the engine: the author did not read
anything under src/ or tests/, did not read the README, and did not run the
library or the benchmark. Labels are what a knowledgeable human would call
"same name" / "different name", not what the matcher happens to return.

It must never be tuned on. If the matcher gets a pair here wrong, do not
adjust the matcher (or this file) to make the number go up: fix a label only
if it is factually wrong, and say so in the commit message.

Format is identical to bench/dataset.py:

GROUPS      every pair of spellings inside a group is the same name  (positives)
DISTINCT    pairs that look or sound alike but are different names   (negatives)

Pairs from two different groups are also used as negatives (bench/run.py
compares the first two spellings of each group with those of every other
group), so no two groups here are the same name.

Labelling conventions, all copied from bench/dataset.py:

* Ukrainian / Russian / Belarusian cognates of one name are the SAME name
  (Надія = Надежда = Надзея, Пилип = Филипп = Піліп, Чорний = Чёрный), as are
  all romanisations of them (national Ukrainian, BGN/PCGN, scientific,
  German, French, Polish, passport spellings).
* Masculine and feminine forms are DIFFERENT names, for given names
  (Руслан / Руслана), surnames (Вишневський / Вишневська) and patronymics
  (Сергійович / Сергіївна).
* Full names: word order, a missing patronymic and initials do not make a
  different name; a different given name, patronymic or surname does.
  A bare given name is different from a full name containing it.
* Diminutives and Western "translations" (Simon, Cyril, Elizabeth ...) are
  deliberately left out: nothing here depends on them.

Names and spellings were chosen not to overlap with bench/dataset.py.
"""

GROUPS = [
    # --- given names: scripts, romanization systems, languages -----------------
    ["Костянтин", "Константин", "Канстанцін", "Kostiantyn", "Konstantin", "Kostyantyn", "Kanstantsin",
     "Constantin"],
    ["Геннадій", "Геннадий", "Генадзь", "Hennadii", "Gennady", "Hennadiy", "Gennadiy", "Gennadi",
     "Gennadij", "Henadz", "Guennadi"],
    ["Любов", "Любовь", "Любоў", "Liubov", "Lyubov", "Ljubow", "Lioubov", "Ljubov'", "Liubou"],
    ["Надія", "Надежда", "Надзея", "Nadiia", "Nadezhda", "Nadiya", "Nadeschda", "Nadejda", "Nadežda",
     "Nadzeya", "Nadija"],
    ["Всеволод", "Усевалад", "Vsevolod", "Wsewolod", "Usevalad", "Vsévolod"],
    ["Семен", "Семён", "Сямён", "Semen", "Semyon", "Semion", "Semjon", "Siamion"],
    ["Артем", "Артём", "Арцём", "Artem", "Artyom", "Artiom", "Artjom", "Artsiom"],
    ["Зінаїда", "Зинаида", "Зінаіда", "Zinaida", "Zinayida", "Sinaida", "Zinaïda"],
    ["Раїса", "Раиса", "Раіса", "Raisa", "Rayisa", "Raissa", "Raïssa"],
    ["Анастасія", "Анастасия", "Настасся", "Anastasiia", "Anastasia", "Anastasiya", "Anastasija",
     "Anastassija", "Nastassia"],
    ["Кирило", "Кирилл", "Кірыл", "Kyrylo", "Kirill", "Kiryl", "Kyrill"],
    ["Лариса", "Ларыса", "Larysa", "Larisa", "Larissa", "Laryssa"],
    ["Анатолій", "Анатолий", "Анатоль", "Anatolii", "Anatoly", "Anatoliy", "Anatoli", "Anatolij", "Anatol"],
    ["Ксенія", "Ксения", "Kseniia", "Ksenia", "Kseniya", "Xenia", "Ksenija"],
    ["Борис", "Барыс", "Borys", "Boris", "Barys"],
    ["Тимофій", "Тимофей", "Цімафей", "Tymofii", "Timofey", "Tymofiy", "Timofei", "Timofej", "Tsimafei"],
    ["Галина", "Галіна", "Halyna", "Galina", "Halina", "Galyna"],
    ["Георгій", "Георгий", "Heorhii", "Georgy", "Heorhiy", "Georgiy", "Georgi", "Georgij", "Gueorgui",
     "Heorhi"],
    ["Вадим", "Вадзім", "Vadym", "Vadim", "Wadim", "Vadzim"],
    ["Пилип", "Филипп", "Піліп", "Pylyp", "Filipp", "Pilip", "Philipp"],
    ["Матвій", "Матвей", "Мацвей", "Matvii", "Matvey", "Matviy", "Matvei", "Matwej", "Matsvei"],
    ["Яків", "Яков", "Якаў", "Yakiv", "Yakov", "Iakov", "Jakow", "Jakov", "Jakiw", "Yakau"],
    ["Жанна", "Zhanna", "Žanna", "Schanna", "Janna", "Żanna"],
    ["Христина", "Кристина", "Крысціна", "Khrystyna", "Kristina", "Chrystyna", "Krystsina", "Christina",
     "Krystyna"],
    ["Гліб", "Глеб", "Hlib", "Gleb", "Hleb", "Glib"],
    ["Едуард", "Эдуард", "Eduard", "Edouard", "Édouard"],
    ["Маргарита", "Маргарыта", "Marharyta", "Margarita", "Margaryta"],
    ["Зоя", "Zoia", "Zoya", "Zoja", "Soja"],
    ["Єлизавета", "Елизавета", "Елізавета", "Yelyzaveta", "Elizaveta", "Yelizaveta", "Ielyzaveta",
     "Jelisaweta"],
    ["Дем'ян", "Демьян", "Дзям'ян", "Demian", "Demyan", "Dem'yan", "Demjan", "Dem'jan", "Dziamian"],
    ["Кузьма", "Kuzma", "Kuz'ma", "Kusma", "Kouzma"],
    # --- surnames ---------------------------------------------------------------
    ["Достоевский", "Достоєвський", "Dostoevsky", "Dostoyevsky", "Dostojewski", "Dostoïevski",
     "Dostoevskij", "Dostoievskyi"],
    ["Пушкин", "Пушкін", "Pushkin", "Puschkin", "Pouchkine", "Puškin", "Puszkin"],
    ["Чехов", "Чэхаў", "Chekhov", "Tschechow", "Tchekhov", "Čechov", "Czechow", "Chekhau"],
    ["Шостакович", "Shostakovich", "Schostakowitsch", "Chostakovitch", "Šostakovič", "Szostakowicz",
     "Shostakovych"],
    ["Щедрин", "Щедрін", "Shchedrin", "Schtschedrin", "Chtchedrine", "Ščedrin", "Szczedrin"],
    ["Грищенко", "Hryshchenko", "Grishchenko", "Gryshchenko", "Hryschtschenko", "Hryščenko"],
    ["Ющенко", "Yushchenko", "Juschtschenko", "Iouchtchenko", "Juščenko", "Juszczenko", "Iushchenko"],
    ["Соловйов", "Соловьёв", "Соловьев", "Soloviov", "Solovyov", "Solovyev", "Soloviev", "Solovev",
     "Solowjow", "Solov'ëv"],
    ["Гоголь", "Гогаль", "Hohol", "Gogol", "Gogol'", "Hohol'"],
    ["Тимошенко", "Цімашэнка", "Tymoshenko", "Timoshenko", "Tymoschenko", "Tymochenko", "Timochenko",
     "Tymošenko", "Tymoszenko", "Tsimashenka"],
    ["Яценюк", "Yatseniuk", "Yatsenyuk", "Jazenjuk", "Iatseniouk", "Jaceniuk", "Iatseniuk", "Jacenjuk"],
    ["Порошенко", "Парашэнка", "Poroshenko", "Poroschenko", "Porochenko", "Porošenko", "Poroszenko",
     "Parashenka"],
    ["Алексиевич", "Алексіевіч", "Алексієвич", "Alexievich", "Aleksievich", "Alexijewitsch", "Aleksijevič",
     "Aleksiyevich", "Alexievitch"],
    ["Мусоргский", "Мусоргський", "Mussorgsky", "Musorgsky", "Mussorgski", "Moussorgski", "Musorgskij",
     "Musorgskiy"],
    ["Рахманинов", "Рахманінов", "Rachmaninoff", "Rakhmaninov", "Rachmaninow", "Rachmaninov", "Rahmaninov"],
    ["Терешкова", "Церашкова", "Tereshkova", "Tereschkowa", "Terechkova", "Tereškova", "Tierieszkowa",
     "Tserashkova"],
    ["Вишневська", "Вишневская", "Vyshnevska", "Vishnevskaya", "Wischnewskaja", "Vichnevskaïa",
     "Višnevskaja", "Vishnevskaia"],
    ["Вишневський", "Вишневский", "Vyshnevskyi", "Vishnevsky", "Vyshnevsky", "Vishnevskiy", "Wischnewski",
     "Višnevskij"],
    ["Чорний", "Чёрный", "Черный", "Chornyi", "Chyorny", "Cherny", "Chornyy", "Chernyi", "Čërnyj"],
    ["Кличко", "Klychko", "Klitschko", "Klitchko", "Kličko", "Klyčko", "Klichko", "Kliczko"],
    ["Нуреев", "Нурєєв", "Nureyev", "Nureev", "Nurejew", "Noureev"],
    ["Караткевіч", "Короткевич", "Karatkevich", "Korotkevich", "Karatkievič", "Korotkewitsch",
     "Karatkewitsch"],
    ["Пугачёва", "Пугачева", "Пугачова", "Pugacheva", "Pugachova", "Pugachyova", "Pugatschowa",
     "Pougatcheva", "Pugačëva"],
    ["Мечников", "Mechnikov", "Metschnikow", "Metchnikoff", "Mečnikov", "Miecznikow", "Mechnykov"],
    ["Хвильовий", "Khvylovyi", "Khvylovy", "Khvylovyy", "Chwylowyj"],
    ["Захарченко", "Zakharchenko", "Sachartschenko", "Zakhartchenko", "Zaharčenko", "Zacharczenko"],
    ["Ґонґадзе", "Гонгадзе", "Gongadze", "Gongadse", "Gongadzé"],
    ["Лук'яненко", "Лукьяненко", "Lukianenko", "Lukyanenko", "Luk'yanenko", "Lukjanenko", "Loukianenko"],
    # --- patronymics --------------------------------------------------------------
    ["Сергійович", "Сергеевич", "Сяргеевіч", "Serhiiovych", "Sergeyevich", "Sergeevich", "Serhiyovych",
     "Sergejewitsch", "Sergueïevitch", "Sergeevič", "Siarheyevich"],
    ["Миколаївна", "Николаевна", "Мікалаеўна", "Mykolaivna", "Nikolaevna", "Nikolayevna", "Mykolayivna",
     "Nikolajewna", "Nikolaïevna", "Mikalaeuna"],
    ["Володимирович", "Владимирович", "Уладзіміравіч", "Volodymyrovych", "Vladimirovich",
     "Wladimirowitsch", "Vladimirovič", "Uladzimiravich"],
    ["Петрівна", "Петровна", "Пятроўна", "Petrivna", "Petrovna", "Petrowna", "Piatrouna"],
    ["Ілліч", "Ильич", "Ільіч", "Illich", "Ilyich", "Ilich", "Iljitsch", "Il'ič", "Ilitch"],
    ["Юріївна", "Юрьевна", "Yuriivna", "Yuryevna", "Yurievna", "Yuriyivna", "Jurjewna", "Jur'evna",
     "Iourievna"],
    ["Васильович", "Васильевич", "Васільевіч", "Vasylovych", "Vasilyevich", "Vasilievich",
     "Wassiljewitsch", "Vasil'evič", "Vasilevich"],
    # --- full names -----------------------------------------------------------------
    ["Михаил Афанасьевич Булгаков", "Mikhail Bulgakov", "Михаил Булгаков", "Булгаков М. А.",
     "Mikhail Afanasyevich Bulgakov", "Michail Bulgakow", "Mikhaïl Boulgakov", "Bulgakov, Mikhail",
     "Михайло Булгаков", "M. A. Bulgakov"],
    ["Ліна Василівна Костенко", "Lina Kostenko", "Лина Васильевна Костенко", "Kostenko Lina Vasylivna",
     "Lina Vasylivna Kostenko", "Л. В. Костенко", "KOSTENKO, Lina"],
    ["Василь Семенович Стус", "Vasyl Stus", "Василий Семёнович Стус", "Stus Vasyl Semenovych",
     "Wassyl Stus", "V. S. Stus", "Vasyl Semenovych Stus"],
    ["Валерій Федорович Залужний", "Valerii Zaluzhnyi", "Valeriy Zaluzhny", "Валерий Фёдорович Залужный",
     "Zaluzhnyi Valerii Fedorovych", "Walerij Saluschnyj", "Valeri Zaloujny", "V. Zaluzhnyi"],
    ["Марыя Аляксандраўна Калеснікава", "Maria Kalesnikava", "Мария Александровна Колесникова",
     "Maria Kolesnikova", "Maryia Kalesnikava", "Maryja Kalesnikawa", "Марія Колесникова"],
    ["Алесь Віктаравіч Бяляцкі", "Ales Bialiatski", "Алесь Викторович Беляцкий", "Ales Byalyatski",
     "Bialiatski Ales", "Ales Bjaljazki", "Алесь Бяляцкі"],
    ["Марина Ивановна Цветаева", "Marina Tsvetaeva", "Марина Іванівна Цвєтаєва",
     "Marina Ivanovna Tsvetayeva", "Tsvetaeva, Marina", "Marina Zwetajewa", "Marina Tsvetaïeva",
     "М. И. Цветаева"],
    ["Богдан Сильвестрович Ступка", "Bohdan Stupka", "Bogdan Stupka", "Богдан Ступка",
     "Stupka Bohdan Sylvestrovych", "B. S. Stupka", "Bohdan Sylvestrovych Stupka"],
    ["Руслана Степанівна Лижичко", "Ruslana Lyzhychko", "Руслана Степановна Лыжичко", "Ruslana Lyzhichko",
     "Lyzhychko Ruslana", "Ruslana Lyschytschko"],
    ["В'ячеслав Максимович Чорновіл", "Viacheslav Chornovil", "Вячеслав Максимович Черновол",
     "Vyacheslav Chornovil", "Chornovil Viacheslav Maksymovych", "Wjatscheslaw Tschornowil",
     "V. M. Chornovil", "Vyacheslav Chernovol"],
    ["Васіль Уладзіміравіч Быкаў", "Vasil Bykau", "Василь Владимирович Быков", "Vasil Bykov",
     "Vasil Uladzimiravich Bykau", "Wassil Bykau", "Васіль Быкаў"],
    ["Казимир Северинович Малевич", "Kazimir Malevich", "Казимир Малевич", "Kazymyr Malevych",
     "Kasimir Malewitsch", "Kazimir Severinovich Malevich", "Малевич К. С.", "Kazimir Malevitch",
     "Kazimierz Malewicz"],
    ["Соломія Амвросіївна Крушельницька", "Solomiia Krushelnytska", "Solomiya Krushelnytska",
     "Соломия Амвросиевна Крушельницкая", "Solomija Kruschelnyzka", "Salomea Kruszelnicka",
     "Krushelnytska, Solomiia"],
    ["Михайло Іванович Туган-Барановський", "Mykhailo Tuhan-Baranovskyi",
     "Михаил Иванович Туган-Барановский", "Mikhail Tugan-Baranovsky", "Tuhan-Baranovskyi Mykhailo",
     "M. I. Tugan-Baranovsky", "Michail Tugan-Baranowski"],
]

DISTINCT = [
    # different given names that look alike
    ("Heorhii", "Hryhorii"), ("Георгий", "Григорий"), ("Hennadii", "Heorhii"), ("Геннадий", "Герман"),
    ("Halyna", "Hanna"), ("Галина", "Ганна"), ("Зінаїда", "Зіновій"), ("Raisa", "Larysa"),
    ("Kseniia", "Yevheniia"), ("Ксения", "Евгения"), ("Borys", "Boryslav"), ("Tymofii", "Tymur"),
    ("Vadym", "Vladyslav"), ("Вадим", "Владимир"), ("Yakiv", "Yakym"), ("Яків", "Яким"),
    ("Zhanna", "Yana"), ("Жанна", "Снежана"), ("Khrystyna", "Kateryna"), ("Kristina", "Karina"),
    ("Eduard", "Edgar"), ("Marharyta", "Marianna"), ("Zoia", "Zoriana"), ("Єлизавета", "Єлисей"),
    ("Демьян", "Даниил"), ("Artem", "Artur"), ("Anatolii", "Antonii"), ("Liubov", "Liubomyr"),
    ("Любовь", "Любава"), ("Vsevolod", "Volodymyr"), ("Всеволод", "Всеслав"), ("Мирослав", "Мстислав"),
    ("Oles", "Oleh"), ("Alla", "Ella"), ("Inha", "Inna"), ("Mykyta", "Mykola"), ("Никита", "Николай"),
    ("Ostap", "Osyp"), ("Lukian", "Luka"), ("Elina", "Alina"), ("Fedir", "Fedot"), ("Kyrylo", "Kornii"),
    ("Matvei", "Maksim"), ("Семён", "Семёнов"), ("Кузьма", "Кузьмин"),
    # masculine and feminine forms of one name
    ("Anastasiia", "Anastasii"), ("Ruslan", "Ruslana"), ("Pavlo", "Pavlyna"), ("Myroslav", "Myroslava"),
    ("Владислав", "Владислава"),
    # surnames: gender forms and near neighbours
    ("Пушкин", "Пущин"), ("Pushkin", "Pushkina"), ("Достоевский", "Достоевская"),
    ("Dostoevsky", "Dunaevsky"), ("Chekhov", "Chekhova"), ("Шостакович", "Шестаков"),
    ("Shchedrin", "Shchedrina"), ("Грищенко", "Гриценко"), ("Hryshchenko", "Hrytsenko"),
    ("Hryshchenko", "Hryshko"), ("Yushchenko", "Yashchenko"), ("Ющенко", "Юрченко"),
    ("Soloviov", "Solovei"), ("Соловьёв", "Соловьёва"), ("Гоголь", "Гоголев"),
    ("Tymoshenko", "Tymoshchuk"), ("Тимошенко", "Тимченко"), ("Yatseniuk", "Yatsenko"),
    ("Poroshenko", "Doroshenko"), ("Алексиевич", "Алексеев"), ("Rachmaninoff", "Rakhmanov"),
    ("Рахманинов", "Рахманинова"), ("Tereshkova", "Tereshkov"), ("Tereshkova", "Tereshchenko"),
    ("Vyshnevskyi", "Vyshnevetskyi"), ("Вишневский", "Вишневецкий"), ("Vyshnevskyi", "Vyshnevska"),
    ("Chornyi", "Chorna"), ("Чёрный", "Чернов"), ("Chornyi", "Chornenko"), ("Кличко", "Клочко"),
    ("Korotkevich", "Korotkov"), ("Пугачёва", "Пугачёв"), ("Mechnikov", "Melnikov"),
    ("Мечников", "Меншиков"), ("Zakharchenko", "Zakharenko"), ("Захарченко", "Захарчук"),
    ("Лук'яненко", "Лукашенко"), ("Lukyanenko", "Lukyanov"), ("Булгаков", "Булганин"),
    ("Костенко", "Косенко"), ("Kostenko", "Kostiuk"), ("Ступка", "Ступак"), ("Быков", "Бычков"),
    ("Bykov", "Bykovsky"), ("Tuhan-Baranovskyi", "Baranovskyi"), ("Tsvetaeva", "Tsvetkova"),
    ("Malevich", "Makarevich"), ("Колесникова", "Колесник"),
    # patronymics
    ("Сергійович", "Сергіївна"), ("Sergeevich", "Sergeevna"), ("Сергеевич", "Семёнович"),
    ("Миколаївна", "Михайлівна"), ("Mykolaivna", "Mykytivna"), ("Volodymyrovych", "Vsevolodovych"),
    ("Владимирович", "Владиславович"), ("Петрівна", "Петрович"), ("Petrivna", "Pavlivna"),
    ("Petrovna", "Petrova"), ("Ilyich", "Ilyinichna"), ("Ильич", "Ильин"), ("Юрьевна", "Юльевна"),
    ("Yuriivna", "Yuliivna"), ("Васильович", "Василівна"), ("Васильевич", "Васильев"),
    ("Vasilyevich", "Vitalyevich"), ("Григорьевич", "Георгиевич"),
    # full names: one different part is a different person
    ("Mikhail Bulgakov", "Sergei Bulgakov"),
    ("Михаил Афанасьевич Булгаков", "Михаил Александрович Булгаков"),
    ("M. A. Bulgakov", "S. N. Bulgakov"), ("Ліна Костенко", "Ніна Костенко"),
    ("Lina Kostenko", "Lina Kosenko"), ("Lina", "Lina Kostenko"), ("Vasyl Stus", "Dmytro Stus"),
    ("Василь Семенович Стус", "Василь Степанович Стус"),
    ("Vasyl Semenovych Stus", "Semen Vasylovych Stus"), ("Valerii Zaluzhnyi", "Vitalii Zaluzhnyi"),
    ("Валерій Залужний", "Валерія Залужна"), ("Maria Kalesnikava", "Maryna Kalesnikava"),
    ("Мария Колесникова", "Мария Колесниченко"), ("Ales Bialiatski", "Aleh Bialiatski"),
    ("Marina Tsvetaeva", "Anastasia Tsvetaeva"),
    ("Марина Ивановна Цветаева", "Марина Игоревна Цветаева"), ("Bohdan Stupka", "Ostap Stupka"),
    ("Богдан Ступка", "Богдана Ступка"), ("Ruslana Lyzhychko", "Ruslan Lyzhychko"),
    ("Viacheslav Chornovil", "Taras Chornovil"), ("В'ячеслав Чорновіл", "В'ячеслав Чорний"),
    ("Vasil Bykov", "Rolan Bykov"), ("Васіль Быкаў", "Васіль Быкоўскі"),
    ("Казимир Малевич", "Казимир Маркевич"), ("Solomiia Krushelnytska", "Sofiia Krushelnytska"),
    ("Mykhailo Tuhan-Baranovskyi", "Mykhailo Baranovskyi"),
]
