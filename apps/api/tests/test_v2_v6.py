"""V2–V6 feature API tests."""

from fastapi.testclient import TestClient


def test_sql_assistant_flow(client: TestClient, auth_headers: dict[str, str]) -> None:
    schema = client.get("/api/v1/sql/schema", headers=auth_headers)
    assert schema.status_code == 200
    assert "customers" in schema.json()["schema_text"]

    generated = client.post(
        "/api/v1/sql/generate",
        headers=auth_headers,
        json={"question": "What is total revenue from orders?"},
    )
    assert generated.status_code == 200
    sql = generated.json()["sql"]
    assert sql.lower().startswith("select")

    explained = client.post("/api/v1/sql/explain", headers=auth_headers, json={"sql": sql})
    assert explained.status_code == 200
    assert explained.json()["explanation"]

    optimized = client.post("/api/v1/sql/optimize", headers=auth_headers, json={"sql": sql})
    assert optimized.status_code == 200
    assert optimized.json()["suggestions"]

    executed = client.post("/api/v1/sql/execute", headers=auth_headers, json={"sql": sql})
    assert executed.status_code == 200
    body = executed.json()
    assert "columns" in body
    assert body["row_count"] >= 1


def test_sql_blocks_mutation(client: TestClient, auth_headers: dict[str, str]) -> None:
    bad = client.post(
        "/api/v1/sql/execute",
        headers=auth_headers,
        json={"sql": "DELETE FROM customers"},
    )
    assert bad.status_code == 422


def test_code_review(client: TestClient, auth_headers: dict[str, str]) -> None:
    source = b"def foo():\n    try:\n        eval('1')\n    except:\n        pass\n"
    upload = client.post(
        "/api/v1/code/reviews",
        headers=auth_headers,
        files={"file": ("sample.py", source, "text/x-python")},
    )
    assert upload.status_code == 201, upload.text
    review = upload.json()
    assert review["status"] == "ready"
    findings = review["result_json"]["findings"]
    assert any(f["category"] in {"bug", "security"} for f in findings)


def test_resume_analyzer(client: TestClient, auth_headers: dict[str, str]) -> None:
    resume = (
        b"Alex Chen\nalex@example.com\n+1 555 0100\n"
        b"Experience: Built FastAPI and React apps with Docker and PostgreSQL.\n"
        b"Skills: Python, FastAPI, React, Docker, SQL\nEducation: BS CS\n"
    )
    jd = "Looking for Python FastAPI engineer with Kubernetes and AWS."
    result = client.post(
        "/api/v1/resumes/analyze",
        headers=auth_headers,
        data={"job_description": jd},
        files={"file": ("resume.txt", resume, "text/plain")},
    )
    assert result.status_code == 201, result.text
    body = result.json()
    assert body["status"] == "ready"
    assert "python" in body["result_json"]["skills"]
    assert body["result_json"]["ats"]["score"] >= 50


def test_meeting_notes(client: TestClient, auth_headers: dict[str, str]) -> None:
    created = client.post(
        "/api/v1/meetings",
        headers=auth_headers,
        data={
            "title": "Planning",
            "transcript": (
                "Speaker A: Welcome.\n"
                "Action item — ship SQL assistant.\n"
                "Speaker B: Follow up with design."
            ),
        },
    )
    assert created.status_code == 201, created.text
    meeting = created.json()
    assert meeting["status"] == "ready"
    assert meeting["summary"]
    assert meeting["action_items_json"]

    export = client.get(f"/api/v1/meetings/{meeting['id']}/export", headers=auth_headers)
    assert export.status_code == 200
    assert "Summary" in export.text


def test_agents_and_dashboard(client: TestClient, auth_headers: dict[str, str]) -> None:
    run = client.post(
        "/api/v1/agents/runs",
        headers=auth_headers,
        json={"task": "What is total order revenue in SQL?"},
    )
    assert run.status_code == 201, run.text
    body = run.json()
    assert body["status"] == "ready"
    assert body["report"]
    assert body["evaluation_json"]["score"] >= 70
    assert any(s.get("agent") == "sql" for s in body["steps_json"])

    dash = client.get("/api/v1/dashboard/summary", headers=auth_headers)
    assert dash.status_code == 200
    summary = dash.json()
    assert summary["counts"]["agent_runs"] >= 1
    assert "usage_by_type" in summary
    assert summary["settings"]["email"] == "alex@example.com"
