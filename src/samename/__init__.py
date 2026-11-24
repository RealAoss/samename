"""samename - match East Slavic personal names across scripts, romanizations and languages.

>>> import samename
>>> samename.is_match("Володимир Зеленський", "Vladimir Zelensky")
True
>>> samename.is_match("Oleksandr Kovalenko", "Oleksii Kovalenko")
False
"""

from .index import NameIndex, dedupe
from .match import DEFAULT_THRESHOLD, Match, compare, is_match, keys, score
from .parse import parse_name

__version__ = "0.1.0"
__all__ = [
    "compare", "score", "is_match", "keys", "parse_name",
    "Match", "NameIndex", "dedupe", "DEFAULT_THRESHOLD", "__version__",
]
