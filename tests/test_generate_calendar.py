import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import generate_calendar


class GenerateCalendarTests(unittest.TestCase):
    def test_prefers_hash_tix_over_dollar_tix(self) -> None:
        values = [
            ["ID", "Date", "Time", "team", "Going?", "#Tix", "$Tix"],
            ["1", "03-29", "1:10 PM", "Dodgers", "TRUE", "2", "150"],
        ]

        events = list(generate_calendar._iter_events(values))

        self.assertEqual(len(events), 1)
        self.assertEqual(events[0].summary, "PP: vs Dodgers (2 tix)")

    def test_hides_tickets_when_not_going(self) -> None:
        values = [
            ["ID", "Date", "Time", "team", "Going?", "#Tix"],
            ["2", "03-30", "1:10 PM", "Athletics", "FALSE", "2"],
        ]

        events = list(generate_calendar._iter_events(values))

        self.assertEqual(len(events), 1)
        self.assertEqual(events[0].summary, "TV: vs Athletics")


if __name__ == "__main__":
    unittest.main()
