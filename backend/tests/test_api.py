import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.core.database import SessionLocal
from app.models.models import User, Session as UserSession

@pytest.mark.asyncio
async def test_public_gallery():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/api/projects")
        assert response.status_code == 200
        assert isinstance(response.json(), list)

@pytest.mark.asyncio
async def test_judge_isolation():
    # Judge A headers
    headers_a = {"Cookie": "session=jdg_a_91bc"}
    # Judge B headers
    headers_b = {"Cookie": "session=jdg_b_44de"}

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # Judge A accesses own scores
        res_a = await ac.get("/api/judge/scores", headers=headers_a)
        assert res_a.status_code == 200

        # Judge B attempts to query Judge A scores (should be 403 Forbidden)
        res_peer = await ac.get("/api/judge/scores?judge=jdg_01", headers=headers_b)
        assert res_peer.status_code == 403

@pytest.mark.asyncio
async def test_participant_blocked():
    headers_prt = {"Cookie": "session=prt_2e88"}
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        res = await ac.get("/api/judge/scores", headers=headers_prt)
        assert res.status_code == 403

@pytest.mark.asyncio
async def test_organizer_csv_export():
    headers_org = {"Cookie": "session=org_7f2a"}
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        res = await ac.get("/api/export.csv", headers=headers_org)
        assert res.status_code == 200
        assert "text/csv" in res.headers.get("content-type", "")
        assert "," in res.text
