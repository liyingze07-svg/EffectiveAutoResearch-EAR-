"""Configuration is data; loading it never imports candidate code."""
from __future__ import annotations

from dataclasses import asdict, dataclass, fields
import json
from pathlib import Path
from typing import Any


@dataclass
class EngineConfig:
    backend: str = "codex"
    direction: str = "Find a substantial, tractable open problem in ML theory."
    workspace: str = ".autonomousmath"
    episodes: int = 1
    continuous: bool = False
    offline: bool = False
    dry_run: bool = False
    candidate_root: str | None = None
    model: str | None = None
    effort: str | None = None
    codex_command: str = "codex"
    claude_command: str = "claude"
    timeout_sec: int = 7200
    max_turns: int = 12
    max_calls: int = 12
    max_review_revisions: int = 2
    max_infra_retries: int = 2
    cooldown_sec: int = 300
    interval_sec: int = 0
    review_backends: list[str] | None = None
    review_model: str | None = None
    review_timeout_sec: int = 1800
    review_effort: str = "high"
    final_check_command: list[str] | None = None
    final_check_timeout_sec: int = 600
    sandbox: str = "workspace-write"
    network_access: bool = True
    resume: bool = True

    @classmethod
    def load(cls, path: Path | None = None, overrides: dict[str, Any] | None = None) -> "EngineConfig":
        data: dict[str, Any] = {}
        if path is not None:
            data = json.loads(path.read_text(encoding="utf-8"))
            if not isinstance(data, dict):
                raise ValueError("config.json must contain an object")
        names = {f.name for f in fields(cls)}
        unknown = set(data) - names
        if unknown:
            raise ValueError("Unknown engine config fields: " + ", ".join(sorted(unknown)))
        data.update({k: v for k, v in (overrides or {}).items() if k in names and v is not None})
        config = cls(**data)
        config.validate()
        return config

    def validate(self) -> None:
        if self.backend not in ("codex", "claude"):
            raise ValueError("backend must be codex or claude")
        for name in ("episodes", "timeout_sec", "max_turns", "max_calls", "review_timeout_sec", "final_check_timeout_sec"):
            if isinstance(getattr(self, name), bool) or int(getattr(self, name)) < 1:
                raise ValueError(f"{name} must be a positive integer")
        for name in ("max_review_revisions", "max_infra_retries", "cooldown_sec", "interval_sec"):
            if isinstance(getattr(self, name), bool) or int(getattr(self, name)) < 0:
                raise ValueError(f"{name} must be a nonnegative integer")
        if self.sandbox not in ("workspace-write", "danger-full-access"):
            raise ValueError("research sandbox must permit writing artifacts")
        if self.review_backends is None:
            self.review_backends = ["codex", "claude"] if self.backend == "claude" else ["codex", "codex"]
        if len(self.review_backends) != 2 or any(b not in ("codex", "claude") for b in self.review_backends):
            raise ValueError("review_backends must contain exactly two codex/claude entries")
        if self.final_check_command is not None and (not isinstance(self.final_check_command, list) or
                not self.final_check_command or any(not isinstance(v, str) for v in self.final_check_command)):
            raise ValueError("final_check_command must be a nonempty argv list")
        self.workspace = str(Path(self.workspace).expanduser().resolve())
        if self.candidate_root:
            self.candidate_root = str(Path(self.candidate_root).expanduser().resolve())

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)
