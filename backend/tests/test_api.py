"""
Basic API and metadata endpoint tests
"""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_health_check(client: AsyncClient):
    resp = await client.get("/api/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"
    assert "version" in data


@pytest.mark.asyncio
async def test_metadata_endpoints(client: AsyncClient):
    voices_resp = await client.get("/api/voices")
    assert voices_resp.status_code == 200
    assert "voices" in voices_resp.json()

    moods_resp = await client.get("/api/moods")
    assert moods_resp.status_code == 200
    assert len(moods_resp.json()["moods"]) > 0

    styles_resp = await client.get("/api/styles")
    assert styles_resp.status_code == 200
    assert len(styles_resp.json()["styles"]) > 0
