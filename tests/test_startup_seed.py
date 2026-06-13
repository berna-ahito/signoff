import importlib
import sys
from types import SimpleNamespace

import app.main as main_module
from app.core.config import settings


def test_startup_seed_skips_by_default(monkeypatch, caplog):
    monkeypatch.setattr(settings, "run_seed_on_start", False)
    caplog.set_level("INFO")

    main_module.run_startup_seed()

    assert "Startup seed skipped" in caplog.text


def test_startup_seed_runs_existing_seed_logic_when_enabled(monkeypatch, caplog):
    calls = []

    class DummySession:
        def close(self):
            calls.append(("close",))

    def fake_session_local():
        calls.append(("session",))
        return DummySession()

    def fake_seed_all(db, reset=False):
        calls.append(("seed_all", db, reset))

    monkeypatch.setattr(settings, "run_seed_on_start", True)
    monkeypatch.setattr(main_module, "SessionLocal", fake_session_local)
    monkeypatch.setitem(sys.modules, "scripts.seed", SimpleNamespace(seed_all=fake_seed_all))
    caplog.set_level("INFO")

    main_module.run_startup_seed()

    assert calls[0] == ("session",)
    assert calls[1][0] == "seed_all"
    assert calls[1][2] is False
    assert calls[2] == ("close",)
    assert "Startup seed completed" in caplog.text


def test_seed_module_imports_in_production(monkeypatch):
    monkeypatch.setenv("APP_ENV", "production")
    sys.modules.pop("scripts.seed", None)

    module = importlib.import_module("scripts.seed")

    assert hasattr(module, "seed_all")
