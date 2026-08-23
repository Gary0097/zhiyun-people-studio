import tempfile
import unittest
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))
from people_workflow import PeopleWorkflowStore


class PeopleWorkflowTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.store = PeopleWorkflowStore(Path(self.tmp.name) / "people.db")

    def tearDown(self):
        self.tmp.cleanup()

    def test_artifact_lifecycle(self):
        created = self.store.create_artifact("permission", "权限建议", {"users": []})
        self.assertEqual(created["status"], "pending_review")
        reviewed = self.store.review_artifact(created["id"], "accept", "刘经理", "建议可信")
        self.assertEqual(reviewed["status"], "accepted")
        self.assertEqual(len(reviewed["reviews"]), 1)

    def test_reviewer_required(self):
        created = self.store.create_artifact("hr", "人力分析", {"summary": {}})
        with self.assertRaises(ValueError):
            self.store.review_artifact(created["id"], "accept", "  ")

    def test_export_only_accepted(self):
        created = self.store.create_artifact("approval", "审批路径", {"path": []})
        with self.assertRaises(ValueError):
            self.store.export_artifact(created["id"])
        self.store.review_artifact(created["id"], "accept", "刘经理")
        content, media_type = self.store.export_artifact(created["id"])
        self.assertEqual(media_type, "application/json")
        self.assertIn("approval", content)

    def test_invalid_kind(self):
        with self.assertRaises(ValueError):
            self.store.create_artifact("bogus", "标题", {})


if __name__ == "__main__":
    unittest.main()
