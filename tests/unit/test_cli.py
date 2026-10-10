from __future__ import annotations

import argparse
import asyncio
import json
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest

from impacttrail import cli
from impacttrail.config import Settings
from impacttrail.services.pipeline import RiskPipeline
from impacttrail.storage.repositories import Repository


def test_doctor_reports_ready(
    monkeypatch: pytest.MonkeyPatch,
    settings: Settings,
    repository: Repository,
    pipeline: RiskPipeline,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setattr(cli, "get_settings", lambda: settings)
    monkeypatch.setattr(cli, "get_repository", lambda: repository)
    monkeypatch.setattr(cli, "get_pipeline", lambda: pipeline)
    assert cli._doctor() == 0
    result = json.loads(capsys.readouterr().out)
    assert result["ready"] is True
    assert result["sentiment_backend"] == "financial_lexicon_v1"


def test_replay_command_function(
    monkeypatch: pytest.MonkeyPatch, settings: Settings, pipeline: RiskPipeline
) -> None:
    monkeypatch.setattr(cli, "get_pipeline", lambda: pipeline)
    fixture = settings.project_root / "data/demo/mixed_source_events.jsonl"
    assert asyncio.run(cli._replay(fixture)) == 0


def test_watch_runs_bounded_iterations(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[str] = []

    async def fake_live(query: str) -> int:
        calls.append(query)
        return 0

    async def no_sleep(_seconds: float) -> None:
        return None

    monkeypatch.setattr(cli, "_live", fake_live)
    monkeypatch.setattr(cli.asyncio, "sleep", no_sleep)
    assert asyncio.run(cli._watch("markets", 15, 2)) == 0
    assert calls == ["markets", "markets"]


@pytest.mark.parametrize(
    ("namespace", "expected_code"),
    [
        (argparse.Namespace(command="doctor"), 0),
        (argparse.Namespace(command="live", query="markets"), 0),
        (
            argparse.Namespace(
                command="watch", query="markets", interval_seconds=None, iterations=1
            ),
            0,
        ),
        (
            argparse.Namespace(command="watch", query="markets", interval_seconds=14, iterations=1),
            2,
        ),
        (argparse.Namespace(command="reset", yes=False), 2),
    ],
)
def test_main_dispatch_and_guards(
    monkeypatch: pytest.MonkeyPatch,
    namespace: argparse.Namespace,
    expected_code: int,
) -> None:
    class Parser:
        def parse_args(self) -> argparse.Namespace:
            return namespace

    async def success(*_args: Any) -> int:
        return 0

    monkeypatch.setattr(cli, "build_parser", lambda: Parser())
    monkeypatch.setattr(
        cli,
        "get_settings",
        lambda: SimpleNamespace(project_root=Path.cwd(), poll_interval_seconds=300),
    )
    monkeypatch.setattr(cli, "_doctor", lambda: 0)
    monkeypatch.setattr(cli, "_live", success)
    with pytest.raises(SystemExit) as exc:
        cli.main()
    assert exc.value.code == expected_code


def test_main_replay_and_reset(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, repository: Repository
) -> None:
    parsed = iter(
        [
            argparse.Namespace(command="replay", fixture="fixture.jsonl"),
            argparse.Namespace(command="reset", yes=True),
        ]
    )

    class Parser:
        def parse_args(self) -> argparse.Namespace:
            return next(parsed)

    async def success(_path: Path) -> int:
        return 0

    monkeypatch.setattr(cli, "build_parser", lambda: Parser())
    monkeypatch.setattr(
        cli,
        "get_settings",
        lambda: SimpleNamespace(project_root=tmp_path, poll_interval_seconds=300),
    )
    monkeypatch.setattr(cli, "get_repository", lambda: repository)
    monkeypatch.setattr(cli, "_replay", success)

    with pytest.raises(SystemExit) as exc:
        cli.main()
    assert exc.value.code == 0
    cli.main()
