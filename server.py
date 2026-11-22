"""
Production FastMCP Server for Cutshort.
Implements the Unified 6-Tool Architecture:
1. manage_profile: Candidate profile, headline, summary, skills, pulse, and resume.
2. search_jobs: Search tech jobs across categories (Python, React, Node, AI/ML, Fullstack).
3. get_job_details: Full JD, recruiter contact, salary range, and company profile.
4. manage_job_pipeline: 1-Click Apply (/make-application-with-tc), save/bookmark, pass, and metrics.
5. manage_account: Recruiter inbox threads, message replies, and matching preferences.
6. manage_session: Multi-tenant session validation and credentials inspection.
"""
import os
import time
from typing import Dict, Any, Optional, List, Union, Literal
from urllib.parse import parse_qs

try:
    from mcp.server.fastmcp import FastMCP
except ImportError:
    from mcp.server.mcpserver import MCPServer as FastMCP

import cutshort_mcp.client as client
import cutshort_mcp.auth as auth
from cutshort_mcp.auth import (
    current_cutshort_authentication,
    current_cutshort_cf_clearance,
    current_cutshort_xsrf_token,
    current_cutshort_cssid,
    current_cutshort_user_agent,
    SESSION_STORE,
    resolve_credentials,
    discover_candidate_info
)

mcp = FastMCP("cutshort-mcp")


# ===========================================================================
# TOOL 1: MANAGE_PROFILE
# ===========================================================================

@mcp.tool()
def manage_profile(
    action: Literal["get", "update", "pulse", "get_resume"] = "get",
    headline: Optional[str] = None,
    summary: Optional[str] = None,
    experience: Optional[int] = None,
    current_company: Optional[str] = None,
    skills: Optional[List[str]] = None,
    locations: Optional[List[str]] = None,
    preferred_salary: Optional[int] = None,
    cutshort_authentication: Optional[str] = None,
    cf_clearance: Optional[str] = None,
    xsrf_token: Optional[str] = None,
    cssid: Optional[str] = None,
    user_agent: Optional[str] = None
) -> Dict[str, Any]:
    """
    Manage Cutshort candidate profile, headline, summary, activity pulse, and resume.
    Args:
        action:
            - 'get': Retrieve full candidate profile, talent card, skills, and preferences
            - 'update': Update headline, summary, experience, or career preferences
            - 'pulse': Touch candidate pulse (/activatesignal) to boost recruiter ranking
            - 'get_resume': Check active resume document status
        headline: Professional headline (e.g., 'Senior Full Stack Developer | Python, FastAPI, React')
        summary: Comprehensive professional summary / bio
        experience: Total professional experience in years
        current_company: Current employer name
        skills: List of key technical skills
        locations: Preferred job locations
        preferred_salary: Target minimum salary in INR
    """
    if action == "get":
        status, res = client.get_candidate_profile(
            cutshort_authentication=cutshort_authentication,
            cf_clearance=cf_clearance,
            xsrf_token=xsrf_token,
            cssid=cssid,
            user_agent=user_agent
        )
        return {"status_code": status, "profile": res}

    elif action == "update":
        if headline is None and summary is None and experience is None and locations is None and preferred_salary is None:
            return {"status_code": 400, "error": "At least one field (headline, summary, experience, locations, preferred_salary) is required for update."}

        status, res = client.update_candidate_profile(
            headline=headline,
            summary=summary,
            experience=experience,
            current_company=current_company,
            skills=skills,
            locations=locations,
            preferred_salary=preferred_salary,
            cutshort_authentication=cutshort_authentication,
            cf_clearance=cf_clearance,
            xsrf_token=xsrf_token,
            cssid=cssid,
            user_agent=user_agent
        )
        return {"status_code": status, "result": res}

    elif action == "pulse":
        status, res = client.touch_profile_pulse(
            cutshort_authentication=cutshort_authentication,
            cf_clearance=cf_clearance,
            xsrf_token=xsrf_token,
            cssid=cssid,
            user_agent=user_agent
        )
        return {"status_code": status, "pulse": res}

    elif action == "get_resume":
        status, res = client.get_resume_info(
            cutshort_authentication=cutshort_authentication,
            cf_clearance=cf_clearance,
            xsrf_token=xsrf_token,
            cssid=cssid,
            user_agent=user_agent
        )
        return {"status_code": status, "resume": res}

    return {"status_code": 400, "error": f"Unsupported action: '{action}'"}


# ===========================================================================
# TOOL 2: SEARCH_JOBS
# ===========================================================================

@mcp.tool()
def search_jobs(
    query: Optional[str] = None,
    category: Optional[str] = None,
    location: Optional[str] = None,
    remote: bool = False,
    min_exp: Optional[int] = None,
    max_exp: Optional[int] = None,
    limit: int = 20,
    cutshort_authentication: Optional[str] = None,
    cf_clearance: Optional[str] = None,
    xsrf_token: Optional[str] = None,
    cssid: Optional[str] = None,
    user_agent: Optional[str] = None
) -> Dict[str, Any]:
    """
    Search active tech jobs on Cutshort.
    Args:
        query: Role or skill keywords (e.g., 'Python', 'React', 'Fullstack', 'Flutter', 'AI', 'Node')
        category: Explicit category slug (e.g., 'python-jobs', 'flutter-jobs', 'react-js-jobs')
        location: Target city (e.g., 'Pune', 'Bangalore', 'Mumbai', 'Delhi')
        remote: Filter for remote-only / hybrid roles
        min_exp: Minimum experience filter (years)
        max_exp: Maximum experience filter (years)
        limit: Max jobs to return (default: 20)
    """
    status, res = client.search_jobs(
        query=query,
        category=category,
        location=location,
        remote=remote,
        min_exp=min_exp,
        max_exp=max_exp,
        limit=limit,
        cutshort_authentication=cutshort_authentication,
        cf_clearance=cf_clearance,
        xsrf_token=xsrf_token,
        cssid=cssid,
        user_agent=user_agent
    )
    return {
        "status_code": status,
        "total_found": res.get("total_count", 0),
        "jobs": res.get("jobs", []),
        "category": res.get("category"),
        "search_results": res
    }


# ===========================================================================
# TOOL 3: GET_JOB_DETAILS
# ===========================================================================

@mcp.tool()
def get_job_details(
    job_ids: Optional[Union[str, List[str]]] = None,
    slug: Optional[str] = None,
    cutshort_authentication: Optional[str] = None,
    cf_clearance: Optional[str] = None,
    xsrf_token: Optional[str] = None,
    cssid: Optional[str] = None,
    user_agent: Optional[str] = None
) -> Dict[str, Any]:
    """
    Retrieve full job description, salary range, recruiter contact, and company details.
    Args:
        job_ids: Single job ID or list of job IDs from search_jobs
        slug: Optional job URL slug
    """
    if not job_ids and not slug:
        return {"status_code": 400, "error": "job_ids or slug parameter is required."}

    if isinstance(job_ids, list):
        results = []
        for jid in job_ids:
            st, res = client.get_job_details(
                job_id=str(jid).strip(),
                cutshort_authentication=cutshort_authentication,
                cf_clearance=cf_clearance,
                xsrf_token=xsrf_token,
                cssid=cssid,
                user_agent=user_agent
            )
            results.append({"job_id": jid, "status_code": st, "data": res})
        return {"status_code": 200, "batch_count": len(results), "jobs": results, "total_jobs": len(results)}

    single_id = str(job_ids).strip() if job_ids else None
    status, res = client.get_job_details(
        job_id=single_id,
        slug=slug,
        cutshort_authentication=cutshort_authentication,
        cf_clearance=cf_clearance,
        xsrf_token=xsrf_token,
        cssid=cssid,
        user_agent=user_agent
    )
    return {
        "status_code": status,
        "total_jobs": 1 if (status == 200 and res.get("id")) else 0,
        "job": res
    }


# ===========================================================================
# TOOL 4: MANAGE_JOB_PIPELINE
# ===========================================================================

@mcp.tool()
def manage_job_pipeline(
    action: Literal["apply", "save", "pass", "list_applications", "metrics"] = "metrics",
    job_id: Optional[str] = None,
    reason: Optional[str] = None,
    page: int = 1,
    limit: int = 10,
    cutshort_authentication: Optional[str] = None,
    cf_clearance: Optional[str] = None,
    xsrf_token: Optional[str] = None,
    cssid: Optional[str] = None,
    user_agent: Optional[str] = None
) -> Dict[str, Any]:
    """
    Manage the candidate application pipeline on Cutshort.
    Args:
        action:
            - 'apply': Direct 1-Click apply to a job with candidate Talent Card (/make-application-with-tc)
            - 'save': Bookmark / save job to candidate watchlist (/save-job)
            - 'pass': Decline / archive irrelevant job (/markJobAsIrrelevant)
            - 'list_applications': List active applications and recruiter conversation threads
            - 'metrics': Pipeline metrics breakdown (total, unread, awaiting, shortlisted)
        job_id: Target job ID for apply, save, or pass actions
        reason: Optional feedback note when passing a job
        page: Page number for list_applications
        limit: Max applications to return
    """
    if action == "apply":
        if not job_id:
            return {"status_code": 400, "error": "job_id is required for action='apply'"}
        status, res = client.apply_to_job(
            job_id=job_id,
            cutshort_authentication=cutshort_authentication,
            cf_clearance=cf_clearance,
            xsrf_token=xsrf_token,
            cssid=cssid,
            user_agent=user_agent
        )
        return {"status_code": status, "action": "apply", "job_id": job_id, "result": res}

    elif action == "save":
        if not job_id:
            return {"status_code": 400, "error": "job_id is required for action='save'"}
        status, res = client.save_job(
            job_id=job_id,
            cutshort_authentication=cutshort_authentication,
            cf_clearance=cf_clearance,
            xsrf_token=xsrf_token,
            cssid=cssid,
            user_agent=user_agent
        )
        return {"status_code": status, "action": "save", "job_id": job_id, "result": res}

    elif action == "pass":
        if not job_id:
            return {"status_code": 400, "error": "job_id is required for action='pass'"}
        status, res = client.pass_job(
            job_id=job_id,
            reason=reason,
            cutshort_authentication=cutshort_authentication,
            cf_clearance=cf_clearance,
            xsrf_token=xsrf_token,
            cssid=cssid,
            user_agent=user_agent
        )
        return {"status_code": status, "action": "pass", "job_id": job_id, "result": res}

    elif action == "list_applications":
        status, res = client.get_conversations(
            page=page,
            limit=limit,
            cutshort_authentication=cutshort_authentication,
            cf_clearance=cf_clearance,
            xsrf_token=xsrf_token,
            cssid=cssid,
            user_agent=user_agent
        )
        return {"status_code": status, "action": "list_applications", "applications": res}

    elif action == "metrics":
        status, res = client.get_pipeline_metrics(
            cutshort_authentication=cutshort_authentication,
            cf_clearance=cf_clearance,
            xsrf_token=xsrf_token,
            cssid=cssid,
            user_agent=user_agent
        )
        return {"status_code": status, "action": "metrics", "metrics": res, "pipeline_metrics": res}

    return {"status_code": 400, "error": f"Unsupported action: '{action}'"}


# ===========================================================================
# TOOL 5: MANAGE_ACCOUNT
# ===========================================================================

@mcp.tool()
def manage_account(
    action: Literal["get_conversations", "reply_conversation", "get_preferences", "update_preferences"] = "get_conversations",
    thread_id: Optional[str] = None,
    conversation_id: Optional[str] = None,
    message: Optional[str] = None,
    reply_text: Optional[str] = None,
    preferred_locations: Optional[List[str]] = None,
    preferred_salary: Optional[int] = None,
    page: int = 1,
    limit: int = 10,
    cutshort_authentication: Optional[str] = None,
    cf_clearance: Optional[str] = None,
    xsrf_token: Optional[str] = None,
    cssid: Optional[str] = None,
    user_agent: Optional[str] = None
) -> Dict[str, Any]:
    """
    Manage Cutshort recruiter communications, message replies, and matching preferences.
    Args:
        action:
            - 'get_conversations': View recruiter inbox messages and conversation threads
            - 'reply_conversation': Send a direct message reply to a recruiter thread
            - 'get_preferences': Inspect career matching preferences (tech stacks, locations, salary)
            - 'update_preferences': Update preferred locations or minimum expected salary
        thread_id: Target conversation thread ID (required for reply_conversation)
        conversation_id: Alias for thread_id
        message: Text reply to send to the recruiter
        reply_text: Alias for message
        preferred_locations: List of target locations
        preferred_salary: Target expected minimum salary in INR
    """
    if action == "get_conversations":
        status, res = client.get_conversations(
            page=page,
            limit=limit,
            cutshort_authentication=cutshort_authentication,
            cf_clearance=cf_clearance,
            xsrf_token=xsrf_token,
            cssid=cssid,
            user_agent=user_agent
        )
        return {"status_code": status, "conversations": res}

    elif action == "reply_conversation":
        target_tid = thread_id or conversation_id
        target_msg = message or reply_text
        if not target_tid or not target_msg:
            return {"status_code": 400, "error": "conversation_id and reply_text are required for reply_conversation."}
        status, res = client.send_reply_to_recruiter(
            thread_id=target_tid,
            message=target_msg,
            cutshort_authentication=cutshort_authentication,
            cf_clearance=cf_clearance,
            xsrf_token=xsrf_token,
            cssid=cssid,
            user_agent=user_agent
        )
        return {"status_code": status, "result": res}

    elif action == "get_preferences":
        status, res = client.execute_request(
            "/get-candidate-matching-preferences",
            method="GET",
            cutshort_authentication=cutshort_authentication,
            cf_clearance=cf_clearance,
            xsrf_token=xsrf_token,
            cssid=cssid,
            user_agent=user_agent
        )
        return {"status_code": status, "preferences": res}

    elif action == "update_preferences":
        pref_payload: Dict[str, Any] = {}
        if preferred_locations is not None:
            pref_payload["preferenceLocations"] = preferred_locations
        if preferred_salary is not None:
            pref_payload["preferredSalaryVanity"] = preferred_salary
        if not pref_payload:
            return {"status_code": 400, "error": "preferred_locations or preferred_salary required for update_preferences."}

        status, res = client.execute_request(
            "/save-candidate-matching-preferences",
            method="POST",
            json_data=pref_payload,
            cutshort_authentication=cutshort_authentication,
            cf_clearance=cf_clearance,
            xsrf_token=xsrf_token,
            cssid=cssid,
            user_agent=user_agent
        )
        return {"status_code": status, "result": res}

    return {"status_code": 400, "error": f"Unsupported action: '{action}'"}


# ===========================================================================
# TOOL 6: MANAGE_SESSION
# ===========================================================================

@mcp.tool()
def manage_session(
    action: Literal["validate", "inspect"] = "validate",
    cutshort_authentication: Optional[str] = None,
    cf_clearance: Optional[str] = None,
    xsrf_token: Optional[str] = None,
    cssid: Optional[str] = None,
    user_agent: Optional[str] = None
) -> Dict[str, Any]:
    """
    Validate Cutshort authentication tokens, candidate identity, and security configuration.
    Args:
        action:
            - 'validate': Verifies session with Cutshort live endpoints and returns candidate profile
            - 'inspect': Displays session cookie presence and header configurations
    """
    if action == "validate":
        info = discover_candidate_info(
            cutshort_authentication=cutshort_authentication,
            cf_clearance=cf_clearance,
            xsrf_token=xsrf_token,
            cssid=cssid,
            user_agent=user_agent
        )
        return {
            "status_code": 200 if info.get("authenticated") else 401,
            "candidate_id": info.get("user_id"),
            "talent_card_id": info.get("tcid"),
            "candidate_name": info.get("name"),
            **info
        }

    auth_val, cf_val, xsrf_val, cssid_val, ua_val = resolve_credentials(
        cutshort_authentication=cutshort_authentication,
        cf_clearance=cf_clearance,
        xsrf_token=xsrf_token,
        cssid=cssid,
        user_agent=user_agent
    )

    return {
        "status_code": 200,
        "authenticated": bool(auth_val and xsrf_val),
        "has_cutshort_authentication": bool(auth_val),
        "has_cf_clearance": bool(cf_val),
        "has_xsrf_token": bool(xsrf_val),
        "has_cssid": bool(cssid_val),
        "cutshort_authentication_present": bool(auth_val),
        "cf_clearance_present": bool(cf_val),
        "xsrf_token_present": bool(xsrf_val),
        "cssid_present": bool(cssid_val),
        "user_agent": ua_val,
        "token_preview": f"{auth_val[:15]}...{auth_val[-10:]}" if auth_val and len(auth_val) > 25 else None
    }


# ===========================================================================
# MULTI-TENANT ASGI MIDDLEWARE (Dual-Transport SSE / MCP Support)
# ===========================================================================

class CutshortMultiTenantMiddleware:
    """Extracts tenant credentials from query params or headers and sets task context."""

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] == "http":
            path = scope.get("path", "")
            method = scope.get("method", "GET")

            # Health probe
            if path in ["/health", "/healthz"] and method == "GET":
                response_body = b'{"status":"ok","server":"cutshort_mcp","tools":6}'
                headers = [
                    (b"content-type", b"application/json"),
                    (b"content-length", str(len(response_body)).encode()),
                    (b"access-control-allow-origin", b"*"),
                ]
                await send({"type": "http.response.start", "status": 200, "headers": headers})
                await send({"type": "http.response.body", "body": response_body})
                return

            # CORS preflight
            if method == "OPTIONS":
                headers = [
                    (b"access-control-allow-origin", b"*"),
                    (b"access-control-allow-methods", b"GET, POST, OPTIONS"),
                    (b"access-control-allow-headers", b"*"),
                ]
                await send({"type": "http.response.start", "status": 204, "headers": headers})
                await send({"type": "http.response.body", "body": b""})
                return

            # Extract headers
            req_headers = dict(scope.get("headers", []))
            hdr_auth = req_headers.get(b"x-cutshort-authentication", b"").decode("utf-8", "ignore") or None
            hdr_cf = req_headers.get(b"x-cutshort-cf-clearance", b"").decode("utf-8", "ignore") or None
            hdr_xsrf = req_headers.get(b"x-cutshort-xsrf-token", b"").decode("utf-8", "ignore") or None
            hdr_cssid = req_headers.get(b"x-cutshort-cssid", b"").decode("utf-8", "ignore") or None
            hdr_ua = req_headers.get(b"x-cutshort-user-agent", b"").decode("utf-8", "ignore") or None

            # Extract query params
            query_string = scope.get("query_string", b"").decode("utf-8", "ignore")
            params = parse_qs(query_string)

            q_auth = params.get("cutshort_authentication", [None])[0]
            q_cf = params.get("cf_clearance", [None])[0]
            q_xsrf = params.get("xsrf_token", [None])[0]
            q_cssid = params.get("cssid", [None])[0]
            q_ua = params.get("user_agent", [None])[0]

            final_auth = q_auth or hdr_auth
            final_cf = q_cf or hdr_cf
            final_xsrf = q_xsrf or hdr_xsrf
            final_cssid = q_cssid or hdr_cssid
            final_ua = q_ua or hdr_ua

            t1 = current_cutshort_authentication.set(final_auth)
            t2 = current_cutshort_cf_clearance.set(final_cf)
            t3 = current_cutshort_xsrf_token.set(final_xsrf)
            t4 = current_cutshort_cssid.set(final_cssid)
            t5 = current_cutshort_user_agent.set(final_ua)

            try:
                await self.app(scope, receive, send)
            finally:
                current_cutshort_authentication.reset(t1)
                current_cutshort_cf_clearance.reset(t2)
                current_cutshort_xsrf_token.reset(t3)
                current_cutshort_cssid.reset(t4)
                current_cutshort_user_agent.reset(t5)
            return

        await self.app(scope, receive, send)


def get_app() -> Any:
    """Return unified Starlette app supporting both Streamable HTTP (/mcp) and SSE (/sse), with full CORS."""
    from starlette.applications import Starlette
    from starlette.middleware.cors import CORSMiddleware
    from starlette.routing import Route
    from mcp.server.transport_security import TransportSecuritySettings

    sec = TransportSecuritySettings(enable_dns_rebinding_protection=False)
    sse_subapp = mcp.sse_app(transport_security=sec)
    http_subapp = mcp.streamable_http_app(streamable_http_path="/mcp", transport_security=sec)

    http_handler = None
    for r in http_subapp.routes:
        if getattr(r, "path", "") == "/mcp":
            http_handler = r.endpoint
            break

    sse_handler = None
    for r in sse_subapp.routes:
        if getattr(r, "path", "") == "/sse":
            sse_handler = r.endpoint
            break

    routes = [
        Route("/sse", endpoint=sse_handler, methods=["GET", "HEAD"]),
        Route("/sse", endpoint=http_handler, methods=["POST"]),
        Route("/mcp", endpoint=http_handler, methods=["GET", "POST", "HEAD"]),
        Route("/", endpoint=http_handler, methods=["POST"]),
        *[r for r in sse_subapp.routes if getattr(r, "path", "") not in ("/sse", "/mcp")],
    ]

    unified_app = Starlette(
        routes=routes,
        lifespan=http_subapp.router.lifespan_context
    )

    wrapped_session_app = CutshortMultiTenantMiddleware(unified_app)
    return CORSMiddleware(
        wrapped_session_app,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["*"],
    )


get_asgi_app = get_app
app = get_app()


def run_server(transport: str = "stdio", port: Optional[int] = None, host: str = "0.0.0.0") -> None:
    """Run the FastMCP server in either stdio, sse, or streamable-http mode."""
    if port is None:
        port = int(os.getenv("PORT", 8000))

    if transport == "sse":
        import uvicorn
        import anyio
        print(f"Starting cutshort-mcp in SSE mode on http://{host}:{port} ...")
        app_instance = get_app()
        config = uvicorn.Config(
            app_instance,
            host=host,
            port=port,
            log_level="info",
            timeout_keep_alive=65
        )
        server = uvicorn.Server(config)
        anyio.run(server.serve)
    elif transport == "streamable-http":
        print(f"Starting cutshort-mcp in streamable-http mode on http://{host}:{port} ...")
        mcp.run(transport="streamable-http", host=host, port=port)
    else:
        mcp.run(transport="stdio")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="cutshort-mcp: Model Context Protocol Server for Cutshort.io")
    parser.add_argument("--transport", choices=["stdio", "sse", "streamable-http"], default="stdio", help="Transport mode")
    parser.add_argument("--port", type=int, default=int(os.getenv("PORT", 8000)), help="Port for SSE mode (default: PORT env or 8000)")
    parser.add_argument("--host", default="0.0.0.0", help="Host for SSE mode")
    args = parser.parse_args()

    run_server(transport=args.transport, port=args.port, host=args.host)

