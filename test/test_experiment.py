import unittest
from typing import Optional

"""
playground for testing the test framework
"""


def character_count(string) -> Optional[int]:
    """
    Counts characters in a string
    :param string: string of characters
    :return: length of string; None if not a string (includes None)
    """
    if type(string) is str:
        lll = len(string)
        return lll
    return None


class TestExperiment(unittest.TestCase):
    """ for experimenting with tests
    """

    def setUp(self) -> None:
        pass

    def test_character_count(self):
        assert character_count("ami") == 3
        assert character_count("pyami") == 5
        assert character_count("") == 0
        assert character_count(1.3) is None
        assert character_count(None) is None
