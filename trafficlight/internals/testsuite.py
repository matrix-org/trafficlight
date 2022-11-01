from typing import List

from trafficlight.internals.test import Test
from trafficlight.internals.testcase import TestCase


class TestSuite:
    def __init__(self, guid: str, test: Test, test_cases: List[TestCase]):
        self.guid = guid
        self.test = test
        self.test_cases = test_cases

    def successes(self) -> int:
        if self.test_cases is not None:
            return 0 + sum(1 for tc in self.test_cases if tc.status == "success")
        return 0

    def failures(self) -> int:
        if self.test_cases is not None:
            return 0 + sum(1 for tc in self.test_cases if tc.status == "failure")
        return 0

    def errors(self) -> int:
        if self.test_cases is not None:
            return 0 + sum(1 for tc in self.test_cases if tc.status == "error")
        return 0

    def skipped(self) -> int:
        if self.test_cases is not None:
            return 0 + sum(
                1
                for tc in self.test_cases
                if tc.status in ("waiting", "running", "skipped")
            )
        return 0
