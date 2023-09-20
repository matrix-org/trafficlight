import asyncio
import hashlib
from typing import List

from trafficlight.internals.test import Test
from trafficlight.internals.testcase import TestCase


class TestSuite:
    def __init__(self, test: Test, test_cases: List[TestCase]):
        self.guid = hashlib.md5(f"TestSuite{test.name()}".encode("utf-8")).hexdigest()
        self.test = test
        self.test_cases = test_cases
        futures = list(map(lambda c: c.completed, test_cases))
        self.completed = asyncio.gather(*futures)

    def name(self) -> str:
        return self.test.name()

    def running(self) -> int:
        if self.test_cases is not None:
            return 0 + sum(1 for tc in self.test_cases if tc.state == "running")
        return 0

    def successes(self) -> int:
        if self.test_cases is not None:
            return 0 + sum(1 for tc in self.test_cases if tc.state == "success")
        return 0

    def failures(self) -> int:
        if self.test_cases is not None:
            return 0 + sum(1 for tc in self.test_cases if tc.state == "failed")
        return 0

    def errors(self) -> int:
        if self.test_cases is not None:
            return 0 + sum(1 for tc in self.test_cases if tc.state == "error")
        return 0

    def waiting(self) -> int:
        if self.test_cases is not None:
            return 0 + sum(
                1 for tc in self.test_cases if tc.state in ("waiting", "preparing")
            )
        return 0
