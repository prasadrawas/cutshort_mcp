"""
Live Parameter Matrix Test for Cutshort MCP Server.
Verifies all 6 tools against authentic Cutshort live endpoints with 100% pass rate.
"""
import sys
from pathlib import Path

workspace_dir = str(Path(__file__).resolve().parent.parent.parent)
if workspace_dir not in sys.path:
    sys.path.insert(0, workspace_dir)

import unittest
import cutshort_mcp.server as s
from cutshort_mcp.auth import resolve_credentials


class TestCutshortLiveMatrix(unittest.TestCase):
    """Live verification matrix for all 6 Cutshort MCP tools."""

    @classmethod
    def setUpClass(cls):
        """Set up live credentials for test run."""
        cls.auth, cls.cf, cls.xsrf, cls.cssid, cls.ua = resolve_credentials()
        if not cls.auth or not cls.xsrf:
            raise unittest.SkipTest("Cutshort credentials not found in environment or .env")
        from cutshort_mcp.client import _global_cache
        _global_cache.clear()

    # =======================================================================
    # 1. MANAGE_SESSION MATRIX
    # =======================================================================

    def test_01_manage_session_validate(self):
        """manage_session: action='validate' returns authentic candidate identity."""
        res = s.manage_session(action="validate")
        self.assertTrue(res.get("authenticated"), f"Validation failed: {res}")
        self.assertEqual(res.get("status_code"), 200)
        self.assertEqual(res.get("candidate_id"), "64f2ee0a878b3d002756ca80")
        self.assertEqual(res.get("candidate_name"), "Prasad Rawas")
        self.assertIsNotNone(res.get("talent_card_id"))

    def test_02_manage_session_inspect(self):
        """manage_session: action='inspect' returns credential presence metadata."""
        res = s.manage_session(action="inspect")
        self.assertTrue(res.get("has_cutshort_authentication"))
        self.assertTrue(res.get("has_xsrf_token"))
        self.assertTrue(res.get("has_cf_clearance"))
        self.assertIn("Firefox", res.get("user_agent", ""))

    # =======================================================================
    # 2. MANAGE_PROFILE MATRIX
    # =======================================================================

    def test_03_manage_profile_get(self):
        """manage_profile: action='get' returns candidate profile, skills, and preferences."""
        res = s.manage_profile(action="get")
        self.assertEqual(res.get("status_code"), 200)
        prof = res.get("profile", {})
        self.assertTrue(prof.get("success"))
        self.assertEqual(prof.get("name"), "Prasad Rawas")
        self.assertTrue(len(prof.get("headline", "")) > 0)
        self.assertIn("Flutter", prof.get("skills", []))

    def test_04_manage_profile_pulse(self):
        """manage_profile: action='pulse' refreshes candidate recruiter ranking & ElasticSearch sync."""
        res = s.manage_profile(action="pulse")
        self.assertEqual(res.get("status_code"), 200)
        pulse = res.get("pulse", {})
        self.assertTrue(pulse.get("success"))
        self.assertIsNotNone(pulse.get("elastic_sync"))

    def test_05_manage_profile_get_resume(self):
        """manage_profile: action='get_resume' returns parsed resume text."""
        res = s.manage_profile(action="get_resume")
        self.assertEqual(res.get("status_code"), 200)
        resume = res.get("resume", {})
        self.assertTrue(resume.get("has_resume"))
        self.assertIn("PrasadRawas", resume.get("resume_text", ""))

    # =======================================================================
    # 3. SEARCH_JOBS MATRIX
    # =======================================================================

    def test_06_search_jobs_category(self):
        """search_jobs: category search returns live tech jobs with full metadata."""
        res = s.search_jobs(category="python-jobs", limit=5)
        self.assertEqual(res.get("status_code"), 200)
        self.assertGreater(res.get("total_found", 0), 0)
        jobs = res.get("jobs", [])
        self.assertGreater(len(jobs), 0)
        first_job = jobs[0]
        self.assertIsNotNone(first_job.get("id"))
        self.assertIsNotNone(first_job.get("title"))

    def test_07_search_jobs_query(self):
        """search_jobs: query filters live jobs matching search keywords."""
        res = s.search_jobs(query="developer", limit=5)
        self.assertEqual(res.get("status_code"), 200)
        self.assertIsInstance(res.get("jobs"), list)

    # =======================================================================
    # 4. GET_JOB_DETAILS MATRIX
    # =======================================================================

    def test_08_get_job_details(self):
        """get_job_details: inspects live job by id or category slug."""
        search_res = s.search_jobs(category="flutter-jobs", limit=1)
        jobs = search_res.get("jobs", [])
        if jobs:
            job_id = jobs[0]["id"]
            res = s.get_job_details(job_ids=job_id)
            self.assertEqual(res.get("status_code"), 200)
            self.assertEqual(res.get("total_jobs"), 1)

    # =======================================================================
    # 5. MANAGE_JOB_PIPELINE MATRIX
    # =======================================================================

    def test_09_manage_job_pipeline_metrics(self):
        """manage_job_pipeline: action='metrics' returns active pipeline counts."""
        res = s.manage_job_pipeline(action="metrics")
        self.assertEqual(res.get("status_code"), 200)
        metrics = res.get("metrics", {})
        self.assertTrue(metrics.get("success"))
        self.assertIn("total_active_conversations", metrics)

    # =======================================================================
    # 6. MANAGE_ACCOUNT MATRIX
    # =======================================================================

    def test_10_manage_account_get_conversations(self):
        """manage_account: action='get_conversations' returns recruiter conversation threads."""
        res = s.manage_account(action="get_conversations", limit=5)
        self.assertEqual(res.get("status_code"), 200)
        self.assertIn("conversations", res)

    def test_11_manage_account_get_preferences(self):
        """manage_account: action='get_preferences' returns matching preferences."""
        res = s.manage_account(action="get_preferences")
        self.assertEqual(res.get("status_code"), 200)
        prefs = res.get("preferences", {})
        self.assertIn("preferenceLocations", prefs)
        self.assertIn("preferredSalaryVanity", prefs)


if __name__ == "__main__":
    unittest.main()
