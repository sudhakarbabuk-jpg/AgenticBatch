import os
import tempfile
import unittest
from pathlib import Path

import app


class LoadDotenvTests(unittest.TestCase):
    def test_load_dotenv_file_uses_app_directory(self):
        app_dir = Path(app.__file__).resolve().parent
        env_path = app_dir / ".env"

        with tempfile.TemporaryDirectory() as temp_dir:
            original_cwd = os.getcwd()
            os.chdir(temp_dir)
            try:
                os.environ.pop("TEST_API_KEY", None)
                env_path.write_text("TEST_API_KEY=test-value\n", encoding="utf-8")

                app.load_dotenv_file()

                self.assertEqual(os.environ.get("TEST_API_KEY"), "test-value")
            finally:
                os.chdir(original_cwd)
                os.environ.pop("TEST_API_KEY", None)
                if env_path.exists():
                    env_path.write_text("", encoding="utf-8")


if __name__ == "__main__":
    unittest.main()
