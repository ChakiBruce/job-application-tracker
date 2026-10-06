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


if __name__ == "__main__":
    unittest.main()
