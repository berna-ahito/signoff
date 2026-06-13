from pathlib import Path
import shutil
import uuid

import app.main as main_module
import pytest


def _fake_frontend_dist(tmp_path: Path) -> Path:
    dist_dir = tmp_path / "dist"
    assets_dir = dist_dir / "assets"
    assets_dir.mkdir(parents=True)
    (dist_dir / "index.html").write_text("<!doctype html><div id=\"root\"></div>", encoding="utf-8")
    (assets_dir / "app.js").write_text("console.log('ok')", encoding="utf-8")
    return dist_dir


@pytest.fixture
def static_tmp_path():
    temp_dir = Path.cwd() / ".tmp_static_frontend_test" / uuid.uuid4().hex
    temp_dir.mkdir(parents=True)
    try:
        yield temp_dir
    finally:
        shutil.rmtree(temp_dir.parent, ignore_errors=True)


@pytest.mark.parametrize("path", ["/login", "/dashboard", "/requests", "/admin"])
def test_spa_routes_return_frontend_index(client, monkeypatch, static_tmp_path, path):
    dist_dir = _fake_frontend_dist(static_tmp_path)
    monkeypatch.setattr(main_module, "FRONTEND_DIST_DIR", dist_dir)
    monkeypatch.setattr(main_module, "FRONTEND_INDEX_FILE", dist_dir / "index.html")

    response = client.get(path)

    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert '<div id="root"></div>' in response.text


def test_frontend_assets_are_served_from_dist(client, monkeypatch, static_tmp_path):
    dist_dir = _fake_frontend_dist(static_tmp_path)
    monkeypatch.setattr(main_module, "FRONTEND_DIST_DIR", dist_dir)
    monkeypatch.setattr(main_module, "FRONTEND_INDEX_FILE", dist_dir / "index.html")

    response = client.get("/assets/app.js")

    assert response.status_code == 200
    assert response.text == "console.log('ok')"


def test_api_like_unknown_routes_are_not_spa_fallbacks(client, monkeypatch, static_tmp_path):
    dist_dir = _fake_frontend_dist(static_tmp_path)
    monkeypatch.setattr(main_module, "FRONTEND_DIST_DIR", dist_dir)
    monkeypatch.setattr(main_module, "FRONTEND_INDEX_FILE", dist_dir / "index.html")

    response = client.get("/auth/not-a-real-route")

    assert response.status_code == 404
    assert response.headers["content-type"].startswith("application/json")
    assert response.json()["detail"] == "Not Found"


def test_existing_api_routes_are_not_spa_fallbacks(client, monkeypatch, static_tmp_path):
    dist_dir = _fake_frontend_dist(static_tmp_path)
    monkeypatch.setattr(main_module, "FRONTEND_DIST_DIR", dist_dir)
    monkeypatch.setattr(main_module, "FRONTEND_INDEX_FILE", dist_dir / "index.html")

    response = client.get("/requests/")

    assert response.status_code == 401
    assert response.headers["content-type"].startswith("application/json")
