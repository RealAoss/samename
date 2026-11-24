"""A curated lexicon of East Slavic given names.

Rules alone cannot know that Володимир, Владимир and Уладзімір are one name,
or that Марія and Марина are two. The lexicon gives the matcher both:

1. the Ukrainian, Russian and Belarusian forms of each given name, plus the
   Latin forms that are not a plain romanization (Alexander, Eugene, Serge);
2. the knowledge that two similar spellings are **different names**: every
   line is its own name, and masculine and feminine forms get separate lines.

Format, one name per line::

    m|f Canonical [Latin ...] | Ukrainian ... | Russian ... | Belarusian ...
    d   Diminutive [Latin ...] | Cyrillic ...  | Canonical name(s) it is short for

``-`` marks a language with no form of its own. Plain romanizations of the
Cyrillic forms (Serhii, Sergey, Sergej, Siarhei ...) need not be listed: they
are recognised phonetically.

Contributions are very welcome: a line here is the easiest way to improve
matching quality.
"""

from __future__ import annotations

from functools import lru_cache

from .distance import similarity, skeletons
from .phonemes import clean_cyrillic, clean_latin, cyrillic_phonemes, latin_phonemes

_DATA = """
# --- masculine given names ---------------------------------------------------
m Oleksandr Alexander Alexandre Aleksander Olexandr Alexandr | Олександр | Александр | Аляксандр
m Oleksii Alexey Alexei Alexej Olexii | Олексій Олекса | Алексей | Аляксей
m Volodymyr Vladimir Wladimir | Володимир | Владимир | Уладзімір Уладзімер
m Mykola Nicholas Nicolas Nikolaus | Микола | Николай | Мікалай Мікола
m Dmytro Dimitri Dimitry | Дмитро | Дмитрий Димитрий | Дзмітрый Зміцер
m Serhii Serge | Сергій | Сергей | Сяргей
m Andrii Andrew | Андрій | Андрей | Андрэй
m Mykhailo Michael Michail | Михайло | Михаил | Міхаіл Міхал
m Pavlo Paul Pawel | Павло | Павел | Павел Павал
m Petro Peter Piotr | Петро | Пётр Петр | Пётр Пятро
m Yevhen Eugene Eugen | Євген Євгеній | Евгений | Яўген Яўгеній
m Ivan | Іван | Иван | Іван
m Yurii Yuri Yury Juri | Юрій | Юрий | Юрый Юры
m Vasyl Vasily Wassili | Василь | Василий | Васіль
m Viktor Victor | Віктор | Виктор | Віктар
m Anatolii Anatoly Anatole | Анатолій | Анатолий | Анатоль Анатолій
m Oleh Oleg | Олег | Олег | Алег
m Ihor Igor | Ігор | Игорь | Ігар
m Vitalii Vitaly | Віталій | Виталий | Віталь Віталій
m Valerii Valery | Валерій | Валерий | Валерый Валер
m Valentyn Valentin | Валентин | Валентин | Валянцін
m Hryhorii Gregory Gregor | Григорій | Григорий | Рыгор Грыгорый
m Borys Boris | Борис | Борис | Барыс
m Leonid | Леонід | Леонид | Леанід
m Stepan | Степан | Степан | Сцяпан
m Maksym Maxim Maxime | Максим | Максим | Максім
m Artem Artyom | Артем | Артём Артем | Арцём
m Denys Denis Dennis | Денис | Денис | Дзяніс
m Roman | Роман | Роман | Раман
m Bohdan Bogdan | Богдан | Богдан | Багдан
m Taras | Тарас | Тарас | Тарас
m Ruslan | Руслан | Руслан | Руслан
m Vadym Vadim | Вадим | Вадим | Вадзім
m Yaroslav | Ярослав | Ярослав | Яраслаў
m Stanislav | Станіслав | Станислав | Станіслаў
m Viacheslav Vyacheslav | В'ячеслав | Вячеслав | Вячаслаў
m Sviatoslav Svyatoslav | Святослав | Святослав | Святаслаў
m Rostyslav | Ростислав | Ростислав | Расціслаў
m Vladyslav Vladislav | Владислав | Владислав | Уладзіслаў
m Myroslav | Мирослав | Мирослав | Міраслаў
m Kostiantyn Konstantin Constantin Constantine | Костянтин | Константин | Канстанцін Кастусь
m Heorhii Georgy Georg | Георгій | Георгий | Георгій Георгі
m Yehor Egor | Єгор | Егор | Ягор
m Illia Ilya | Ілля | Илья | Ілья Ілля
m Kyrylo Kirill Cyril | Кирило | Кирилл | Кірыл Кірыла
m Danylo Daniel Daniil | Данило | Даниил Данила Данил | Даніла Даніл Данііл
m Nazar | Назар | Назар | Назар
m Ostap | Остап | Остап | Астап
m Marko Mark Marc | Марко | Марк | Марк
m Matvii Matvey | Матвій | Матвей | Мацвей
m Tymofii Timofey | Тимофій | Тимофей | Цімафей
m Tymur Timur | Тимур | Тимур | Цімур
m Davyd David | Давид | Давид | Давыд
m Zakhar | Захар | Захар | Захар
m Semen Semyon | Семен | Семён Семен | Сямён
m Fedir Fyodor Theodor Feodor | Федір Теодор | Фёдор Федор | Фёдар Хведар
m Hlib Gleb | Гліб | Глеб | Глеб
m Lev | Лев | Лев | Леў
m Arsen | Арсен | Арсен | Арсен
m Arsenii Arseny | Арсеній | Арсений | Арсеній Арсень
m Anton | Антон Антін | Антон | Антон
m Artur Arthur | Артур | Артур | Артур
m Eduard Edward | Едуард Едвард | Эдуард Эдвард | Эдуард Эдвард
m Hennadii Gennady | Геннадій | Геннадий | Генадзь Генадзій
m Yakiv Yakov Jakob | Яків | Яков | Якаў Якуб
m Yosyp Joseph Josef | Йосип | Иосиф Осип | Язэп Іосіф
m Trokhym Trofim | Трохим | Трофим | Трафім
m Yukhym Yefim | Юхим | Ефим | Яўхім
m Lavrentii Lavrenty | Лаврентій | Лаврентий | Лаўрэнцій Лаўрэн
m Makar | Макар | Макар | Макар
m Mykyta Nikita | Микита | Никита | Мікіта
m Nestor | Нестор | Нестор | Нестар
m Orest | Орест | Орест | Арэст
m Panas Opanas Afanasy | Панас Опанас Афанасій | Афанасий | Апанас Панас
m Pylyp Philip Filipp | Пилип | Филипп | Піліп
m Rodion | Родіон | Родион | Радзівон Радыён
m Sava | Сава | Савва | Сава
m Tykhon | Тихон | Тихон | Ціхан
m Khoma Foma | Хома | Фома | Хама
m Yulian Julian | Юліан | Юлиан | Юльян
m Yulii Yuly | Юлій | Юлий | Юлій
m Yan Jan | Ян | Ян | Ян
m Adam | Адам | Адам | Адам
m Albert | Альберт | Альберт | Альберт
m Arkadii Arkady | Аркадій | Аркадий | Аркадзь Аркадзій
m Veniamin Benjamin | Веніамін | Вениамин | Веніямін
m Vikentii | Вікентій | Викентий | Вікенцій
m Vsevolod | Всеволод | Всеволод | Усевалад
m Herman German Hermann | Герман | Герман | Герман
m Demian Demyan Damian | Дем'ян Даміан | Демьян Дамиан | Дзям'ян
m Yelysei Elisey | Єлисей | Елисей | Елісей
m Zynovii Zinovy | Зиновій | Зиновий | Зіновій
m Ilarion | Іларіон | Илларион | Іларыён
m Klym Klim | Клим | Клим | Клім
m Kuzma | Кузьма | Кузьма | Кузьма
m Lukian Lukyan | Лук'ян | Лукьян | Лук'ян
m Luka | Лука | Лука | Лука
m Markiian | Маркіян | Маркиан | -
m Nazarii | Назарій | Назарий | -
m Oles Ales | Олесь | Олесь | Алесь
m Omelian Yemelyan | Омелян | Емельян | Амяльян
m Prokhor | Прохор | Прохор | Прохар
m Platon | Платон | Платон | Платон
m Robert | Роберт | Роберт | Роберт
m Savelii Savely | Савелій | Савелий | Савелій
m Samuil Samuel | Самуїл Самійло | Самуил | Самуіл
m Sevastian Sebastian | Севастян | Севастьян | -
m Svyryd Spiridon | Свирид | Спиридон | Спірыдон
m Solomon | Соломон | Соломон | Саламон
m Spartak | Спартак | Спартак | Спартак
m Stefan Stephan | Стефан | Стефан | Стэфан
m Terentii Terenty | Терентій | Терентий | Цярэнцій
m Ustym Ustin | Устим | Устин | Усцін
m Feliks Felix | Фелікс | Феликс | Фелікс
m Kharyton | Харитон | Харитон | Харытон
m Khrystyian Christian Kristian | Християн | Кристиан | Крысціян
m Emil | Еміль | Эмиль | Эміль
m Erik Eric | Ерік | Эрик | Эрык
m Ernest | Ернест | Эрнест | Эрнэст
m Yarema Yeremey | Ярема | Еремей | Ярэма
m Yaromyr | Яромир | Яромир | -
m Liubomyr Lubomyr | Любомир | Любомир | Любамір
m Bronislav | Броніслав | Бронислав | Браніслаў
m Vlas | Влас | Влас | Улас
m Hordii Gordey | Гордій | Гордей | Гардзей
m Hnat Ignat Ignaty | Гнат Ігнат Ігнатій | Игнат Игнатий | Ігнат Ігнацій
m Zenon | Зенон | Зенон | Зянон
m Kindrat Kondrat | Кіндрат | Кондрат Кондратий | Кандрат
m Kornii Korney | Корній Корнелій | Корней Корнелий | Карней
m Leontii Leonty | Леонтій | Леонтий | Лявонцій Лявон
m Myron | Мирон | Мирон | Мірон
m Naum | Наум | Наум | Навум
m Nykyfor Nikifor | Никифор | Никифор | Нічыпар
m Panteleimon | Пантелеймон | Пантелеймон | Панцеляймон
m Prokip Prokop Prokopy | Прокіп | Прокопий Прокоп | Пракоп
m Rafail Raphael Rafael | Рафаїл | Рафаил | Рафаіл
m Rinat Renat | Рінат Ренат | Ринат Ренат | Рынат
m Rustam Rustem | Рустам | Рустам | Рустам
m Yakym Akim | Яким | Аким Иоаким | Акім Якім
m Abram Abraham Avraam | Абрам Аврам | Абрам Авраам | Абрам
m Aron Aaron | Арон | Арон Аарон | Арон
m Isak Isaac Isaak | Ісак Ісаак | Исаак | Ісак
m Marian | Мар'ян | Марьян | Мар'ян
m Vitold | Вітольд | Витольд | Вітальд
m Henrikh Heinrich Henryk | Генріх | Генрих | Генрых
m Kazymyr Casimir | Казимир | Казимир | Казімір
m Karl Carl | Карл Карло | Карл | Карл
m Leonard | Леонард | Леонард | Леанард
m Marat | Марат | Марат | Марат
m Martyn Martin | Мартин | Мартин Мартын | Марцін
m Mstyslav | Мстислав | Мстислав | Мсціслаў
m Oskar Oscar | Оскар | Оскар | Оскар
m Radym | Радим | Радим | Радзім
m Rudolf Rudolph | Рудольф | Рудольф | Рудольф
m Serafym | Серафим | Серафим | Серафім
m Sydir Sidor Isidor | Сидір | Сидор Исидор | Сідар
m Tadei Tadeusz Thaddeus | Тадей | Фаддей | Тадэвуш Фадзей
m Feodosii Feodosy | Феодосій Тодось | Феодосий | Феадосій
m Yevstakhii Evstafy | Євстахій | Евстафий | Яўстафій
m Ildar | Ільдар | Ильдар | Ільдар
m Damir | Дамір | Дамир | Дамір
m Ramil | Раміль | Рамиль | Раміль
m Eldar | Ельдар | Эльдар | Эльдар
m Ali | Алі | Али | Алі
m Akhmed Ahmed Akhmet | Ахмед | Ахмед Ахмет | Ахмед
m Mahomed Magomed Muhammad Mohammed | Магомед | Магомед Магомет Мухаммед | Магамед
m Ibrahim | Ібрагім | Ибрагим | Ібрагім
m Aslan | Аслан | Аслан | Аслан
m Arman | Арман | Арман | Арман
m Armen | Армен | Армен | Армен
m Tyhran Tigran | Тигран | Тигран | Тыгран
m Vladlen | Владлен | Владлен | Уладлен
m Yefrem Efrem | Єфрем Охрім | Ефрем | Яфрэм
m Innokentii Innokenty | Інокентій | Иннокентий | Інакенцій
m Klyment Clement | Климент | Климент | Клімент
m Lazar | Лазар | Лазарь | Лазар
m Mytrofan | Митрофан | Митрофан | Мітрафан
m Potap | Потап | Потап | Патап
m Sylvestr Sylvester | Сильвестр | Сильвестр | Сільвестр
m Tryfon | Трифон | Трифон | Трыфон
m Boleslav | Болеслав | Болеслав | Баляслаў
m Boryslav | Борислав | Борислав | Барыслаў
m Zorian | Зорян | - | -
m Adrian | Адріан Адріян | Адриан | Адрыян
m Milan | Мілан | Милан | Мілан
m Dominik | Домінік | Доминик | Дамінік
m Alan | Алан | Алан | Алан
m Alfred | Альфред | Альфред | Альфрэд
m Arnold | Арнольд | Арнольд | Арнольд
m Edhar Edgar | Едгар | Эдгар | Эдгар
m Leon | Леон | Леон | Леон
m Emmanuil Emmanuel | Еммануїл | Эммануил | Эмануіл
m Frants Franz | Франц | Франц | Францішак Франц
m Fylymon Filimon | Филимон | Филимон | Філімон
m Avhustyn Augustin | Августин | Августин | Аўгусцін
m Onysym Anisim | Онисим | Анисим | Анісім
m Harry Garri | Гаррі | Гарри | Гары
# --- feminine given names ----------------------------------------------------
f Olena Elena Helena Helen Alena Alyona | Олена Альона | Елена Алёна Алена | Алена Алёна
f Kateryna Ekaterina Catherine Katherine Katarina Katharina | Катерина | Екатерина Катерина | Кацярына
f Hanna Anna Hannah | Ганна Анна | Анна | Ганна Анна
f Mariia Maria Mary Marie Marya | Марія | Мария Марья | Марыя
f Nataliia Natalia Natalie Nathalie | Наталія Наталя | Наталья Наталия | Наталля Наталія
f Yuliia Julia Yulia | Юлія | Юлия | Юлія
f Oksana Oxana | Оксана | Оксана | Аксана
f Tetiana Tatiana Tatyana | Тетяна | Татьяна | Таццяна Тацяна
f Iryna Irina | Ірина | Ирина | Ірына
f Svitlana Svetlana | Світлана | Светлана | Святлана
f Liudmyla Ludmila Lyudmila | Людмила | Людмила | Людміла
f Olha Olga | Ольга | Ольга | Вольга
f Halyna Galina | Галина | Галина | Галіна
f Valentyna Valentina | Валентина | Валентина | Валянціна
f Viktoriia Victoria Viktoria | Вікторія | Виктория | Вікторыя
f Larysa Larissa | Лариса | Лариса | Ларыса
f Liubov Lyubov Lubov | Любов | Любовь | Любоў
f Nadiia Nadezhda Nadia | Надія | Надежда | Надзея
f Vira Vera | Віра | Вера | Вера
f Anastasiia Anastasia | Анастасія | Анастасия | Анастасія Настасся
f Dariia Daria Darya | Дарія Дар'я | Дарья | Дар'я
f Daryna Darina | Дарина | Дарина | Дарына
f Yevheniia Eugenia Evgenia | Євгенія | Евгения | Яўгенія
f Oleksandra Alexandra Aleksandra | Олександра | Александра | Аляксандра
f Alina | Аліна | Алина | Аліна
f Alla | Алла | Алла | Ала
f Alisa Alice | Аліса | Алиса | Аліса
f Anzhela Angela | Анжела | Анжела | Анжэла
f Anzhelika Angelika Angelica | Анжеліка | Анжелика | Анжаліка
f Antonina | Антоніна | Антонина | Антаніна
f Valeriia Valeria Valerie | Валерія | Валерия | Валерыя
f Varvara Barbara | Варвара | Варвара | Варвара
f Vasylyna | Василина | Василина | Васіліна
f Vasylysa Vasilisa | Василиса | Василиса | Васіліса
f Veronika Veronica | Вероніка | Вероника | Вераніка
f Vitaliia | Віталія | Виталия | Віталія
f Vitalina | Віталіна | Виталина | Віталіна
f Vladyslava | Владислава | Владислава | Уладзіслава
f Diana | Діана | Диана | Дыяна
f Dina | Діна | Дина | Дзіна
f Yeva Eva Ewa | Єва | Ева | Ева
f Yelyzaveta Elizabeth Elisabeth Elizaveta | Єлизавета | Елизавета | Лізавета Елізавета
f Zhanna Janna | Жанна | Жанна | Жанна
f Zinaida | Зінаїда | Зинаида | Зінаіда
f Zoia Zoya Zoe | Зоя | Зоя | Зоя
f Zlata | Злата | Злата | Злата
f Ivanna | Іванна | Иванна | Іванна
f Yana Jana | Яна | Яна | Яна
f Yanina Janina | Яніна | Янина | Яніна
f Inna | Інна | Инна | Іна
f Inha Inga | Інга | Инга | Інга
f Inesa Inessa | Інеса | Инесса | Інеса
f Karyna Karina | Карина | Карина | Карына
f Kira | Кіра | Кира | Кіра
f Khrystyna Kristina Christina Krystyna | Христина | Кристина Христина | Крысціна Хрысціна
f Kseniia Xenia Ksenia | Ксенія | Ксения | Ксенія
f Lesia Lesya | Леся | Леся | Леся
f Lidiia Lydia Lidia | Лідія | Лидия | Лідзія
f Liliia Lilia | Лілія | Лилия | Лілія
f Liliana | Ліліана | Лилиана | Ліліяна
f Marharyta Margarita | Маргарита | Маргарита | Маргарыта
f Maryna Marina | Марина | Марина | Марына
f Mariana Maryana Marianna | Мар'яна Маріанна | Марьяна Марианна | Мар'яна
f Marta Martha | Марта | Марта | Марта
f Myroslava | Мирослава | Мирослава | Міраслава
f Nina | Ніна | Нина | Ніна
f Nonna | Нонна | Нонна | Нона
f Nelia Nelly | Неля Неллі | Нелли Неля | Нэлі
f Olesia Olesya Alesia | Олеся | Олеся Алеся | Алеся
f Polina | Поліна | Полина | Паліна
f Raisa | Раїса | Раиса | Раіса
f Rehina Regina | Регіна | Регина | Рэгіна
f Rymma Rimma | Римма | Римма | Рыма
f Roksolana | Роксолана | Роксолана | Раксалана
f Ruslana | Руслана | Руслана | Руслана
f Snizhana Snezhana | Сніжана | Снежана | Сняжана
f Solomiia Solomiya | Соломія | Соломия | Саламея
f Sofiia Sophia Sofia Sofya | Софія | София Софья | Соф'я Сафія
f Stanislava | Станіслава | Станислава | Станіслава
f Stefaniia Stefania Stephanie | Стефанія | Стефания | Стэфанія
f Taisiia Taisia | Таїсія | Таисия | Таісія
f Tamara | Тамара | Тамара | Тамара
f Uliana Ulyana | Уляна | Ульяна | Ульяна
f Faina | Фаїна | Фаина | Фаіна
f Yaryna | Ярина | Ярина | Ярына
f Yaroslava | Ярослава | Ярослава | Яраслава
f Bohdana Bogdana | Богдана | Богдана | Багдана
f Vanda Wanda | Ванда | Ванда | Ванда
f Vlada | Влада | Влада | Улада
f Dominika | Домініка | Доминика | Дамініка
f Emiliia Emilia | Емілія | Эмилия | Эмілія
f Emma | Емма | Эмма | Эма
f Elvira | Ельвіра | Эльвира | Эльвіра
f Eleonora | Елеонора | Элеонора | Элеанора
f Elina | Еліна | Элина | Эліна
f Ella | Елла | Элла | Эла
f Zoriana Zoryana | Зоряна | - | -
f Ilona | Ілона | Илона | Ілона
f Kamila Camilla | Каміла | Камила Камилла | Каміла
f Karolina Carolina | Кароліна | Каролина | Караліна
f Klavdiia Claudia | Клавдія | Клавдия | Клаўдзія
f Lada | Лада | Лада | Лада
f Lina | Ліна | Лина | Ліна
f Liana | Ліана | Лиана | Ліяна
f Luiza Louisa Luisa | Луїза | Луиза | Луіза
f Maia Maya | Майя | Майя | Мая
f Melaniia Melania | Меланія | Мелания | Меланія
f Milana | Мілана | Милана | Мілана
f Milena | Мілена | Милена | Мілена
f Nika | Ніка | Ника | Ніка
f Orysia | Орися | - | -
f Pavlina Paulina | Павліна Павлина | Павлина | Паўліна
f Roza Rosa | Роза | Роза | Роза
f Roksana Roxana | Роксана | Роксана | Раксана
f Sabina | Сабіна | Сабина | Сабіна
f Serafyma | Серафима | Серафима | Серафіма
f Ustyna Ustinya | Устина | Устинья | Усціння
f Yustyna Justina | Юстина | Юстина | Юсціна
f Yuliana Juliana | Юліана | Юлиана | Юльяна
f Adelina | Аделіна | Аделина | Адэліна
f Aida | Аїда | Аида | Аіда
f Albina | Альбіна | Альбина | Альбіна
f Anhelina Angelina | Ангеліна | Ангелина | Ангеліна
f Anfisa | Анфіса | Анфиса | Анфіса
f Arina | Аріна | Арина | Арына
f Bella | Белла | Белла | Бэла
f Bozhena | Божена | Божена | Бажэна
f Violetta | Віолетта Віолета | Виолетта | Віялета
f Vita | Віта | Вита | Віта
f Dana | Дана | Дана | Дана
f Evelina | Евеліна | Эвелина | Эвеліна
f Erika Erica | Еріка | Эрика | Эрыка
f Zarina | Заріна | Зарина | Зарына
f Izabella Isabella | Ізабелла | Изабелла | Ізабэла
f Kalyna | Калина | Калина | Каліна
f Klara Clara | Клара | Клара | Клара
f Mahdalyna Magdalena Magdalina | Магдалина | Магдалина | Магдаліна
f Marfa | Марфа | Марфа | Марфа
f Mykhailyna Michalina | Михайлина | Михалина | Міхаліна
f Paraska Praskovya | Параска Парасковія | Прасковья | Параскева Прасковія
f Pelahiia Pelageya | Пелагія | Пелагея | Пелагея
f Tamila | Таміла | Тамила | Таміла
f Yevdokiia Evdokia | Євдокія | Евдокия | Еўдакія Аўдоцця
f Yefrosyniia Efrosinia | Єфросинія | Ефросинья Евфросиния | Ефрасіння
f Ahafiia Agafya | Агафія | Агафья | Агаф'я
f Ahata Agatha Agata | Агата | Агата | Агата
f Ahnesa Agnes Agnessa | Агнеса | Агнесса | Агнеса Агнешка
f Ahniia Agnia | Агнія | Агния | Агнія
f Ada | Ада | Ада | Ада
f Adriana | Адріана | Адриана | Адрыяна
f Amina | Аміна | Амина | Аміна
f Leila Layla | Лейла | Лейла | Лэйла
f Elmira | Ельміра | Эльмира | Эльміра
f Dinara | Дінара | Динара | Дзінара
f Hulnara Gulnara | Гульнара | Гульнара | Гульнара
f Madina | Мадіна | Мадина | Мадзіна
f Renata | Рената | Рената | Рэната
f Laura | Лаура | Лаура | Лаўра
f Linda | Лінда | Линда | Лінда
f Monika Monica | Моніка | Моника | Моніка
f Nikol Nicole | Ніколь | Николь | Ніколь
f Sandra | Сандра | Сандра | Сандра
f Stella | Стелла | Стелла | Стэла
f Tina | Тіна | Тина | Ціна
f Venera | Венера | Венера | Венера
f Miia Mia | Мія | Мия | Мія
f Mila | Міла | Мила | Міла
f Yeseniia Esenia Yesenia | Єсенія | Есения | Есенія
f Ameliia Amelia | Амелія | Амелия | Амелія
f Adel Adele | Адель | Адель | Адэль
f Yadviha Jadwiga Yadviga | Ядвіга | Ядвига | Ядвіга
f Tereza Theresa Teresa | Тереза | Тереза | Тэрэза
f Liubomyra Lubomyra | Любомира | Любомира | Любаміра
f Sviatoslava | Святослава | Святослава | Святаслава
f Yevanheliia Evangelina | Євангеліна | Евангелина | Евангеліна
f Ioanna Joanna | Іоанна | Иоанна | Іаанна
# --- diminutives (used only with diminutives=True) ---------------------------
d Sasha Sascha | Саша | Oleksandr Oleksandra
d Sanya | Саня | Oleksandr
d Shura | Шура | Oleksandr Oleksandra
d Sashko | Сашко | Oleksandr
d Alex | Алекс | Oleksandr Oleksii Oleksandra
d Lyosha Lesha | Льоша Лёша Леша | Oleksii
d Alyosha Alesha | Альоша Алёша Алеша | Oleksii
d Vova | Вова | Volodymyr
d Volodya | Володя | Volodymyr
d Vlad | Влад | Vladyslav Volodymyr
d Kolya | Коля | Mykola
d Dima | Діма Дима | Dmytro
d Mitya | Митя Мітя | Dmytro
d Seryozha Serezha | Серьожа Серёжа Сережа | Serhii
d Andryusha | Андрюша | Andrii
d Misha Mischa | Міша Миша | Mykhailo
d Mishko | Мишко | Mykhailo
d Pasha | Паша | Pavlo
d Petya | Петя | Petro
d Zhenya | Женя | Yevhen Yevheniia
d Vanya | Ваня | Ivan
d Ivanko | Іванко | Ivan
d Yura | Юра | Yurii
d Vasya | Вася | Vasyl
d Vitya | Вітя Витя | Viktor
d Vika | Віка Вика | Viktoriia
d Tolya | Толя | Anatolii
d Tolik | Толік Толик | Anatolii
d Vitalik | Віталік Виталик | Vitalii
d Valera | Валера | Valerii
d Valya | Валя | Valentyn Valentyna
d Hrysha Grisha | Гриша | Hryhorii
d Borya | Боря | Borys
d Lyonya Lenya | Льоня Лёня Леня | Leonid
d Styopa Stepa | Стьопа Стёпа Степа | Stepan
d Max | Макс | Maksym
d Tyoma Tema | Тьома Тёма Тема | Artem
d Roma | Рома | Roman
d Bodya | Бодя | Bohdan
d Kostya | Костя | Kostiantyn
d Zhora | Жора | Heorhii
d Gosha | Гоша | Heorhii
d Slava | Слава | Viacheslav Stanislav Yaroslav Sviatoslav Vladyslav Rostyslav Myroslav
d Stas | Стас | Stanislav
d Vadik | Вадік Вадик | Vadym
d Yarik | Ярік Ярик | Yaroslav
d Danya | Даня | Danylo
d Tima | Тіма Тима | Tymofii Tymur
d Fedya | Федя | Fedir
d Hena Gena | Гена | Hennadii
d Lyova Leva | Льова Лёва Лева | Lev
d Tosha | Тоша | Anton
d Edik | Едік Эдик | Eduard
d Yasha | Яша | Yakiv
d Syoma | Сьома Сёма | Semen
d Ilyusha | Ілюша Илюша | Illia
d Lena | Лєна Лена | Olena
d Olenka | Оленка | Olena
d Katya | Катя | Kateryna
d Katrusia | Катруся | Kateryna
d Katyusha | Катюша | Kateryna
d Anya | Аня | Hanna
d Hannusia | Ганнуся | Hanna
d Anyuta | Анюта | Hanna
d Masha | Маша | Mariia
d Marusia | Маруся | Mariia
d Mariika | Марійка | Mariia
d Natasha Natascha | Наташа | Nataliia
d Natalka | Наталка | Nataliia
d Ksyusha | Ксюша | Kseniia Oksana
d Tanya | Таня | Tetiana
d Ira | Іра Ира | Iryna
d Sveta | Свєта Света | Svitlana
d Lyuda | Люда | Liudmyla
d Olya | Оля | Olha
d Halya Galya | Галя | Halyna
d Lara | Лара | Larysa
d Lyuba | Люба | Liubov
d Nastya | Настя | Anastasiia
d Dasha | Даша | Dariia
d Liza | Ліза Лиза | Yelyzaveta
d Sonya | Соня | Sofiia
d Lida | Ліда Лида | Lidiia
d Rita | Рита Ріта | Marharyta
d Toma | Тома | Tamara
d Tonya | Тоня | Antonina
d Zina | Зіна Зина | Zinaida
d Asya | Ася | Anastasiia
d Polya | Поля | Polina
d Lilya | Ліля Лиля | Liliia
d Ulya | Уля | Uliana
d Varya | Варя | Varvara
d Nyusha | Нюша | Hanna
d Alya | Аля | Alina Alla Oleksandra
d Lera | Лєра Лера | Valeriia
d Yulya | Юля | Yuliia
d Nadya | Надя | Nadiia
"""

_PATRONYMIC_STEMS = {"lv": "Lev", "akovl": "Yakiv", "pavl": "Pavlo", "mixal": "Mykhailo"}

ENTRIES: list = []         # (kind, canonical, forms) with kind 'm' | 'f' | 'd'
_BY_NAME: dict = {}        # canonical -> entry id
_BUCKETS: dict = {}        # skeleton -> [(entry id, phonemes)]
_SHORT_FOR: dict = {}      # diminutive entry id -> frozenset of full-name entry ids
_FIRST: dict = {}          # entry id -> first phonemes of its forms
_FATHERS: dict = {}        # folded stem -> set of masculine entry ids
_FATHERS_A: dict = {}      # same, only for names ending in -a (Illia -> Illich)

_RESOLVE_MIN = 0.93
_RESOLVE_MARGIN = 0.02


def stem_key(seq) -> str:
    """Fold a phoneme sequence into the key used to recognise a father's name."""
    syms = [x.p for x in seq]
    while syms and (syms[-1] in "aeiouyj"):
        syms.pop()
    fold = {"g": "h", "ɣ": "h", "y": "i", "w": "v", "j": ""}
    return "".join(fold.get(s, s) for s in syms)


def _add_form(eid, seq, forms):
    if not seq:
        return
    forms.append(seq)
    for k in skeletons(seq):
        _BUCKETS.setdefault(k, []).append((eid, seq))
    _FIRST.setdefault(eid, []).append(seq[0])


def _load():
    pending = []
    for line in _DATA.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        kind, rest = line.split(None, 1)
        fields = [f.split() for f in rest.split("|")]
        latin = fields[0]
        canonical = latin[0]
        if canonical in _BY_NAME:
            raise ValueError(f"duplicate lexicon entry {canonical!r}")
        eid = len(ENTRIES)
        forms = []
        _BY_NAME[canonical] = eid
        for w in latin:
            _add_form(eid, latin_phonemes(clean_latin(w)), forms)
        if kind == "d":
            for w in fields[1]:
                _add_form(eid, cyrillic_phonemes(clean_cyrillic(w), None), forms)
            pending.append((eid, fields[2]))
        else:
            for lang, words in zip(("uk", "ru", "be"), fields[1:4]):
                for w in words:
                    if w != "-":
                        _add_form(eid, cyrillic_phonemes(clean_cyrillic(w), lang), forms)
        ENTRIES.append((kind, canonical, tuple(forms)))
        if kind == "m":
            for seq in forms:
                key = stem_key(seq)
                if len(key) >= 2:
                    _FATHERS.setdefault(key, set()).add(eid)
                    if seq[-1].p == "a":
                        _FATHERS_A.setdefault(key, set()).add(eid)
    for eid, names in pending:
        _SHORT_FOR[eid] = frozenset(_BY_NAME[n] for n in names)   # KeyError = typo in the table
    for key, name in _PATRONYMIC_STEMS.items():
        _FATHERS.setdefault(key, set()).add(_BY_NAME[name])


_load()


def canonical(eid: int) -> str:
    return ENTRIES[eid][1]


@lru_cache(maxsize=50_000)
def _resolve(seq: tuple) -> frozenset:
    scored = {}
    best = 0.0
    for k in skeletons(seq):
        for eid, ref in _BUCKETS.get(k, ()):
            s = similarity(seq, ref)
            if s >= _RESOLVE_MIN:
                if s > scored.get(eid, 0.0):
                    scored[eid] = s
                if s > best:
                    best = s
    if best >= 1.0 - 1e-9:
        # an exact spelling of a listed form is that name only, not also its
        # near neighbours (Marfa is not Marta just because Martha is listed)
        return frozenset(eid for eid, s in scored.items() if s >= 1.0 - 1e-9)
    return frozenset(eid for eid, s in scored.items() if s >= best - _RESOLVE_MARGIN)


def name_ids(seq: tuple, diminutives: bool = False) -> frozenset:
    """Lexicon entries a spelling confidently stands for (may be empty).

    With ``diminutives=True`` a short form also stands for its full names.
    """
    if not seq:
        return frozenset()
    ids = _resolve(seq)
    if diminutives and ids:
        extra = set()
        for eid in ids:
            extra |= _SHORT_FOR.get(eid, frozenset())
        if extra:
            ids = ids | extra
    return ids


def is_given_name(seq: tuple) -> bool:
    return any(ENTRIES[eid][0] != "d" for eid in _resolve(seq)) if seq else False


def first_phonemes(ids) -> list:
    """First phoneme of every form of the given entries (for matching initials)."""
    out = []
    for eid in ids:
        out.extend(_FIRST.get(eid, ()))
    return out


def father_ids(stem: tuple, a_stems_only: bool = False) -> frozenset:
    """Masculine names a patronymic stem derives from (may be empty)."""
    table = _FATHERS_A if a_stems_only else _FATHERS
    return frozenset(table.get(stem_key(stem), ()))
