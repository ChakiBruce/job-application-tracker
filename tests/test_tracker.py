"""Check SQLite persistence and the command-line application flow."""

from contextlib import redirect_stdout
from functools import partial
from io import StringIO
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import app
from src import tracker


class TrackerTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.database = Path(self.directory.name) / "applications.db"
        tracker.initialize_database(self.database)

    def test_empty_database(self):
        self.assertEqual(tracker.get_applications(self.database), [])

    def test_saved_values_survive_reinitialization(self):
        values = ("O'Reilly; DROP TABLE applications; --", "Developer", "2026-10-06", "Applied")
        application_id = tracker.add_application(*values, database_path=self.database)
        tracker.initialize_database(self.database)
        applications = tracker.get_applications(self.database)
        self.assertEqual(len(applications), 1)
        self.assertEqual(applications[0]["id"], application_id)
        self.assertEqual(tuple(applications[0])[1:], values)

    def test_menu_can_save_then_view_on_next_run(self):
        with patch.object(app, "initialize_database", partial(tracker.initialize_database, self.database)), \
             patch.object(app, "add_application", partial(tracker.add_application, database_path=self.database)), \
             patch.object(app, "get_applications", partial(tracker.get_applications, self.database)):
            with patch("builtins.input", side_effect=["1", "Example Company", "Developer", "2026-10-06", "", "3"]), redirect_stdout(StringIO()) as output:
                app.main()
            self.assertIn("Application saved.", output.getvalue())
            with patch("builtins.input", side_effect=["2", "3"]), redirect_stdout(StringIO()) as output:
                app.main()
            self.assertIn("Example Company - Developer", output.getvalue())
            self.assertIn("Status: Applied", output.getvalue())


    def test_status_update_persists_and_only_changes_selected_application(self):
        first_id = tracker.add_application("First", "Developer", "2026-10-06", "Applied", self.database)
        second_id = tracker.add_application("Second", "Developer", "2026-10-06", "Applied", self.database)
        self.assertTrue(tracker.update_application_status(second_id, "Interviewing", self.database))
        tracker.initialize_database(self.database)
        applications = tracker.get_applications(self.database)
        self.assertEqual([(row["id"], row["status"]) for row in applications], [(first_id, "Applied"), (second_id, "Interviewing")])

    def test_missing_id_and_blank_status_do_not_change_existing_data(self):
        application_id = tracker.add_application("Example", "Developer", "2026-10-06", "Applied", self.database)
        self.assertFalse(tracker.update_application_status(application_id + 1, "Rejected", self.database))
        with self.assertRaises(ValueError):
            tracker.update_application_status(application_id, "   ", self.database)
        self.assertEqual(tracker.get_applications(self.database)[0]["status"], "Applied")

    def test_status_menu_reprompts_for_invalid_input_and_saves(self):
        application_id = tracker.add_application("Example", "Developer", "2026-10-06", "Applied", self.database)
        with patch.object(app, "initialize_database", partial(tracker.initialize_database, self.database)), \
             patch.object(app, "get_applications", partial(tracker.get_applications, self.database)), \
             patch.object(app, "update_application_status", partial(tracker.update_application_status, database_path=self.database)), \
             patch("builtins.input", side_effect=["4", "abc", "0", str(application_id), "", "Offer", "3"]), \
             redirect_stdout(StringIO()) as output:
            app.main()
        self.assertIn(f"ID {application_id}:", output.getvalue())
        self.assertIn("Application status updated.", output.getvalue())
        self.assertEqual(tracker.get_applications(self.database)[0]["status"], "Offer")

    def test_status_flow_handles_empty_database_and_unknown_id(self):
        with patch.object(app, "get_applications", partial(tracker.get_applications, self.database)), \
             patch("builtins.input") as user_input, redirect_stdout(StringIO()) as output:
            app.update_status_flow()
        user_input.assert_not_called()
        self.assertIn("No applications yet.", output.getvalue())
        application_id = tracker.add_application("Example", "Developer", "2026-10-06", "Applied", self.database)
        with patch.object(app, "get_applications", partial(tracker.get_applications, self.database)), \
             patch.object(app, "update_application_status") as update, \
             patch("builtins.input", side_effect=[str(application_id + 1)]), redirect_stdout(StringIO()) as output:
            app.update_status_flow()
        update.assert_not_called()
        self.assertIn("No application found", output.getvalue())

    def test_search_matches_company_or_role_and_ignores_ascii_case(self):
        first_id = tracker.add_application("Acme", "Engineer", "2026-10-06", "Applied", self.database)
        second_id = tracker.add_application("Other", "Acme specialist", "2026-10-06", "Offer", self.database)
        tracker.add_application("Unrelated", "Designer", "2026-10-06", "Applied", self.database)
        rows = tracker.search_applications(" ACME ", database_path=self.database)
        self.assertEqual([row["id"] for row in rows], [first_id, second_id])

    def test_search_combines_keyword_and_exact_status(self):
        tracker.add_application("Acme", "Engineer", "2026-10-06", "Applied", self.database)
        wanted_id = tracker.add_application("Acme", "Engineer", "2026-10-06", "Interviewing", self.database)
        tracker.add_application("Other", "Designer", "2026-10-06", "Interviewing", self.database)
        rows = tracker.search_applications("acme", " interviewing ", self.database)
        self.assertEqual([row["id"] for row in rows], [wanted_id])
        self.assertEqual(tracker.search_applications("", "Interview", self.database), [])

    def test_blank_search_returns_all_and_status_only_filters(self):
        first_id = tracker.add_application("First", "Engineer", "2026-10-06", "Applied", self.database)
        second_id = tracker.add_application("Second", "Engineer", "2026-10-06", "Offer", self.database)
        self.assertEqual([row["id"] for row in tracker.search_applications(database_path=self.database)], [first_id, second_id])
        self.assertEqual([row["id"] for row in tracker.search_applications(status="offer", database_path=self.database)], [second_id])

    def test_search_treats_special_characters_as_literal_text(self):
        wanted_id = tracker.add_application("O'Reilly 100%_", "Engineer", "2026-10-06", "Applied", self.database)
        tracker.add_application("Other", "Engineer", "2026-10-06", "Applied", self.database)
        for keyword in ("O'Reilly", "%_", "100%"):
            self.assertEqual([row["id"] for row in tracker.search_applications(keyword, database_path=self.database)], [wanted_id])
        self.assertEqual(tracker.search_applications("' OR 1=1 --", database_path=self.database), [])
        self.assertEqual(len(tracker.get_applications(self.database)), 2)

    def test_search_menu_displays_matches_and_reports_no_results(self):
        application_id = tracker.add_application("Acme", "Engineer", "2026-10-06", "Applied", self.database)
        with patch.object(app, "initialize_database", partial(tracker.initialize_database, self.database)), \
             patch.object(app, "search_applications", partial(tracker.search_applications, database_path=self.database)), \
             patch("builtins.input", side_effect=["5", "acme", "applied", "5", "missing", "", "3"]), \
             redirect_stdout(StringIO()) as output:
            app.main()
        self.assertIn(f"ID {application_id}: Acme - Engineer", output.getvalue())
        self.assertIn("No matching applications found.", output.getvalue())

    def test_statistics_for_empty_database(self):
        self.assertEqual(
            tracker.get_application_statistics(self.database),
            {"total": 0, "status_counts": {}},
        )

    def test_statistics_count_multiple_statuses_and_custom_status(self):
        for status in ("Applied", "Applied", "Interviewing", "Offer", "Awaiting referral"):
            tracker.add_application("Example", "Engineer", "2026-10-07", status, self.database)
        statistics = tracker.get_application_statistics(self.database)
        self.assertEqual(statistics["total"], 5)
        self.assertEqual(statistics["status_counts"], {
            "Applied": 2, "Interviewing": 1, "Offer": 1, "Awaiting referral": 1,
        })

    def test_statistics_reflect_status_updates_after_reinitialization(self):
        application_id = tracker.add_application("Example", "Engineer", "2026-10-07", "Applied", self.database)
        tracker.add_application("Other", "Engineer", "2026-10-07", "Offer", self.database)
        tracker.update_application_status(application_id, "Offer", self.database)
        tracker.initialize_database(self.database)
        self.assertEqual(
            tracker.get_application_statistics(self.database),
            {"total": 2, "status_counts": {"Offer": 2}},
        )

    def test_statistics_menu_displays_total_and_counts(self):
        for status in ("Applied", "Applied", "Interviewing"):
            tracker.add_application("Example", "Engineer", "2026-10-07", status, self.database)
        with patch.object(app, "initialize_database", partial(tracker.initialize_database, self.database)), \
             patch.object(app, "get_application_statistics", partial(tracker.get_application_statistics, self.database)), \
             patch("builtins.input", side_effect=["6", "3"]), \
             redirect_stdout(StringIO()) as output:
            app.main()
        self.assertIn("Total applications: 3", output.getvalue())
        self.assertIn("Applied: 2", output.getvalue())
        self.assertIn("Interviewing: 1", output.getvalue())

    def test_statistics_menu_handles_empty_database(self):
        with patch.object(app, "initialize_database", partial(tracker.initialize_database, self.database)), \
             patch.object(app, "get_application_statistics", partial(tracker.get_application_statistics, self.database)), \
             patch("builtins.input", side_effect=["6", "3"]), \
             redirect_stdout(StringIO()) as output:
            app.main()
        self.assertIn("Total applications: 0", output.getvalue())
        self.assertIn("No applications yet.", output.getvalue())

if __name__ == "__main__":
    unittest.main()
