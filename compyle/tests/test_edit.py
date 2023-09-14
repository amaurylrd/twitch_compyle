import os
import sys
import uuid
from typing import Any, Dict, Iterable, Optional, Union
from unittest import TestCase, main

from compyle.actions.edit import dfs, ne


class TestParser(TestCase):
    maxDiff = None

    def setUp(self):
        os.environ = {}
        self.original_stdout = sys.stdout
        self.original_stderr = sys.stderr
        sys.stdout = open(os.devnull, "w")
        sys.stderr = open(os.devnull, "w")

    def tearDown(self):
        sys.stdout.close()
        sys.stderr.close()
        sys.stdout = self.original_stdout
        sys.stderr = self.original_stderr


class TestNe(TestCase):
    def is_commutative(
        self, data: Iterable[Union[Any, Dict[str, Any]]], i: int, j: int, key: Optional[str] = None
    ) -> bool:
        return ne(data, key, i, j) and ne(data, key, j, i)

    def is_valid(self, data: Iterable[Any], i: int, j: int, key: str = uuid.uuid1()) -> bool:
        return self.is_commutative([{key: e} for e in data], i, j, key) and self.is_commutative(data, i, j)

    def test_returns_false_i_equal_j(self):
        self.assertFalse(self.is_valid([1], 0, 0))

    def test_returns_false_for_equal_values(self):
        self.assertFalse(self.is_valid([1, 1], 0, 1))

    def test_returns_true_for_unequal_values(self):
        self.assertTrue(self.is_valid([1, 2], 0, 1))


class TestBfs(TestCase):
    def is_sorted(self, data: Iterable[Union[Any, Dict[str, Any]]], key: Optional[str] = None) -> bool:
        return all(ne(data, key, i, i + 1) for i in range(len(data) - 1))

    def is_valid(self, data: Iterable[Any], key: str = uuid.uuid1(), start: int = 0) -> bool:
        scd = [{key: e} for e in data]
        return dfs(scd, key, start) and self.is_sorted(scd, key) and dfs(data, i=start) and self.is_sorted(data)

    def test_returns_true_for_empty_list(self):
        self.assertTrue(self.is_valid([]))

    def test_returns_true_for_sorted_list(self):
        self.assertTrue(self.is_valid([1, 2, 3]))

    def test_returns_true_for_unsorted_list(self):
        self.assertTrue(self.is_valid([1, 3, 2]))

    def test_returns_false_for_impossible_sort(self):
        self.assertFalse(self.is_valid([1, 2, 2, 2]))

    def test_does_not_affect_data_for_impossible_sort(self, data=[1, 2, 2, 2]):
        self.assertFalse(self.is_valid(data) or data != [1, 2, 2, 2])

    def test_keeps_the_first_element_in_first_place(self, data=[1, 1, 2, 3]):
        self.assertTrue(self.is_valid(data, start=1) and data[0] == 1)


if __name__ == "__main__":
    main()
