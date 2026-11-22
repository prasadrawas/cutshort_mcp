"""
Unit tests for cutshort_mcp server, auth resolution, TTL cache, and client methods.
"""
import sys
from pathlib import Path

workspace_dir = str(Path(__file__).resolve().parent.parent.parent)
if workspace_dir not in sys.path:
    sys.path.insert(0, workspace_dir)

import unittest
from cutshort_mcp.server import mcp
from cutshort_mcp import auth
from cutshort_mcp.cache import TTLCache


class TestCutshortMCP(unittest.TestCase):
    """Unit test suite for Cutshort MCP components."""

    def test_mcp_initialization(self):
        """Verify FastMCP server name and exact 6-tool registration."""
        self.assertEqual(mcp.name, "cutshort-mcp")
        self.assertEqual(len(mcp._tool_manager._tools), 6)

    def test_tool_names(self):
        """Confirm all 6 unified tools exist."""
        tools = mcp._tool_manager._tools
        expected_tools = [
            "manage_profile",
            "search_jobs",
            "get_job_details",
            "manage_job_pipeline",
            "manage_account",
            "manage_session",
        ]
        self.assertEqual(len(tools), 6)
        for tool_name in expected_tools:
            self.assertIn(tool_name, tools, f"Missing tool: {tool_name}")

    def test_ttl_cache(self):
        """Test TTLCache set, get, expiration, and invalidation."""
        cache = TTLCache(default_ttl=10, max_size=5)
        cache.set("key1", "val1")
        self.assertEqual(cache.get("key1"), "val1")

        # Expiration test
        cache.set("short_key", "short_val", ttl=-1)
        self.assertIsNone(cache.get("short_key"))

        # Invalidation test
        cache.set("prefix_a", "val_a")
        cache.set("prefix_b", "val_b")
        cache.set("other", "val_other")
        cache.invalidate("prefix_")
        self.assertIsNone(cache.get("prefix_a"))
        self.assertIsNone(cache.get("prefix_b"))
        self.assertEqual(cache.get("other"), "val_other")

    def test_build_cookie_header(self):
        """Test Cookie header formatting."""
        header = auth.build_cookie_header("sess123", "cf789", "xsrf456", "cssid101")
        self.assertIn("cutshort_authentication=sess123", header)
        self.assertIn("cf_clearance=cf789", header)
        self.assertIn("XSRF-TOKEN=xsrf456", header)
        self.assertIn("cssid=cssid101", header)

    def test_manage_profile_parameter_validation(self):
        """manage_profile requires at least one field for update."""
        from cutshort_mcp import server

        res_update = server.manage_profile(action="update")
        self.assertEqual(res_update.get("status_code"), 400)
        self.assertIn("At least one field", res_update.get("error", ""))

    def test_manage_pipeline_parameter_validation(self):
        """manage_job_pipeline requires job_id for apply, save, pass."""
        from cutshort_mcp import server

        res_apply = server.manage_job_pipeline(action="apply")
        self.assertEqual(res_apply.get("status_code"), 400)
        self.assertIn("job_id is required", res_apply.get("error", ""))

        res_save = server.manage_job_pipeline(action="save")
        self.assertEqual(res_save.get("status_code"), 400)
        self.assertIn("job_id is required", res_save.get("error", ""))

        res_pass = server.manage_job_pipeline(action="pass")
        self.assertEqual(res_pass.get("status_code"), 400)
        self.assertIn("job_id is required", res_pass.get("error", ""))

    def test_manage_account_parameter_validation(self):
        """manage_account requires conversation_id and reply_text for reply_conversation."""
        from cutshort_mcp import server

        res_reply = server.manage_account(action="reply_conversation")
        self.assertEqual(res_reply.get("status_code"), 400)
        self.assertIn("conversation_id and reply_text are required", res_reply.get("error", ""))


if __name__ == "__main__":
    unittest.main()
