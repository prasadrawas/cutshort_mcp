# Cutshort MCP Server

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![MCP Specification](https://img.shields.io/badge/MCP-2024--11--05-brightgreen.svg)](https://modelcontextprotocol.io/)
[![FastMCP](https://img.shields.io/badge/FastMCP-Official%20SDK-orange.svg)](https://github.com/modelcontextprotocol/python-sdk)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A production-ready **Model Context Protocol (MCP)** server for **[Cutshort](https://cutshort.io)** (India's leading conversational AI & modern tech hiring marketplace). Enables AI agents (Claude Web, Claude Desktop, Gemini, Cursor, ChatGPT, and custom autonomous hiring bots) to manage candidate profiles, synchronize talent cards, search 50+ live opportunities across tech categories, inspect detailed job postings, execute **direct 1-click applications**, track recruiter conversations, and pulse candidate availability.

---

## 🌟 Key Capabilities

- **Zero-Config Multi-Tenant Remote Deployment**: Securely connects to **Claude Web** (Custom Connectors) and **Gemini** without needing environment variables on the server. Simply pass your credentials directly in the connection URL (`?cutshort_authentication=...&cf_clearance=...&xsrf_token=...`).
- **Complete Profile & Talent Card Sync**: View and update candidate profile headline, summary bio, total experience, salary preferences, location preferences, and technical skill stacks.
- **Automated Recruiter Activity Pulse (`touch_profile_pulse`)**: Triggers Cutshort's candidate verification pulse, flagging `dataVerifiedRecently` and requesting instant Elasticsearch synchronization (`syncToElasticRequestedOn`) to rank candidate profiles at the top of recruiter searches.
- **Curated Tech Matching Feed & Job Search**:
  - `search_jobs`: Full-text search and category-based feeds across `python-jobs`, `flutter-jobs`, `reactjs-jobs`, `fullstack-developer-jobs`, and more.
  - `get_job_details`: Structured inspection returning title, company, salary band, remote work policies, required skills, and recruiter contact metadata.
- **Direct 1-Click Application Pipeline**:
  - `apply`: Instantly submits candidate talent card (`tcid`) to matching jobs via Cutshort's 1-click application API (`/make-application-with-tc`).
  - `save` / `pass`: Bookmark jobs or mark irrelevant to refine match recommendations.
  - `metrics`: Live count and breakdown of active recruiter conversations and pipelines.
- **Recruiter Inbox & Conversations**:
  - `get_conversations`: Fetch candidate-recruiter messaging threads, unread counts, and interview invitations.
  - `reply_conversation`: Send real-time follow-up messages directly to hiring managers and recruiters.

---

## 🛠️ Unified 6-Tool Architecture

The Cutshort MCP server implements the standardized **Unified 6-Tool Architecture**, reducing context token consumption by **~80%** while providing comprehensive control over the candidate lifecycle.

| Tool | Action Options / Parameters | Description |
| :--- | :--- | :--- |
| **`manage_profile`** | `action`: `"get"`, `"update"`, `"pulse"`, `"get_resume"` | Complete candidate profile lifecycle: view profile, update headline, bio, experience, preferred locations & salary, bump recruiter search visibility pulse, and inspect parsed resume text. |
| **`search_jobs`** | `query`, `category`, `location`, `limit` | Discover active tech jobs. Supports category filtering (e.g. `python-jobs`, `flutter-jobs`, `fullstack-developer-jobs`) and keyword filtering. |
| **`get_job_details`** | `job_ids`: `Union[str, List[str]]`, `job_slug`: `str` | Comprehensive inspection for single or multiple jobs. Returns full job description, salary range, tech requirements, remote policy, and recruiter details. |
| **`manage_job_pipeline`** | `action`: `"apply"`, `"save"`, `"pass"`, `"list_applications"`, `"metrics"` | 1-click apply (`make-application-with-tc`), bookmark job (`save-job`), decline (`markJobAsIrrelevant`), and track pipeline metrics. |
| **`manage_account`** | `action`: `"get_conversations"`, `"reply_conversation"`, `"get_preferences"`, `"update_preferences"` | Recruiter communications inbox, thread messaging, and matching preference configuration. |
| **`manage_session`** | `action`: `"validate"`, `"inspect"` | Authentication verification, cookie validation, and candidate talent card discovery. |

---

## 🚀 Quick Start & Connection Guide

### How to Retrieve Your Cutshort Credentials

1. Log in to your candidate account on **[cutshort.io](https://cutshort.io)**.
2. Open Developer Tools (`F12` or `Cmd + Option + I`).
3. Navigate to **Storage** (Firefox) or **Application** (Chrome) &rarr; **Cookies** &rarr; `https://cutshort.io`.
4. Copy the following cookie values:
   - `cutshort_authentication`: Session authentication token (`s%3A...`)
   - `cf_clearance`: Cloudflare clearance token
   - `XSRF-TOKEN`: Anti-CSRF token
   - `cssid`: Session tracking identifier
5. In the **Console** tab, run `navigator.userAgent` to get your exact browser User-Agent.

---

### Local Installation & Running

```bash
# Clone the repository
git clone https://github.com/prasadrawas/cutshort_mcp.git
cd cutshort_mcp

# Install dependencies
pip install -e .

# Configure your environment
cp .env.example .env
# Edit .env with your credentials

# Run in SSE mode (default, port 8000)
python -m cutshort_mcp --transport sse --port 8000

# Or run in stdio mode for local LLM clients
python -m cutshort_mcp --transport stdio
```

---

### Connecting to Claude Desktop

Add this configuration to `~/Library/Application Support/Claude/claude_desktop_config.json` (macOS) or `%APPDATA%\Claude\claude_desktop_config.json` (Windows):

```json
{
  "mcpServers": {
    "cutshort": {
      "command": "python3",
      "args": ["-m", "cutshort_mcp", "--transport", "stdio"],
      "env": {
        "CUTSHORT_AUTHENTICATION": "s%3A...",
        "CUTSHORT_CF_CLEARANCE": "CnwR_...",
        "CUTSHORT_XSRF_TOKEN": "...",
        "CUTSHORT_CSSID": "...",
        "CUTSHORT_USER_AGENT": "Mozilla/5.0 ..."
      }
    }
  }
}
```

---

### Remote Deployment & Claude Web (Custom Connectors)

Run the server on a cloud host or via Docker:

```bash
docker build -t cutshort-mcp .
docker run -p 8000:8000 --env-file .env cutshort-mcp
```

In **Claude Web** (or custom MCP clients), configure the SSE connection URL with query parameters:

```
https://your-domain.com/sse?cutshort_authentication=s%3A...&cf_clearance=...&xsrf_token=...&cssid=...
```

---

## 📄 License

MIT License. Designed and maintained by Prasad Rawas.
