from __future__ import annotations

import json
import logging
import os
import warnings as _warnings_module
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from config import ModelSettings

_pending_log_dir: Path | None = None
_logging_configured = False


def setup_file_logging(log_dir: str | Path) -> None:
    """Register the log directory; actual handler wiring happens after TinyTroupe import.

    Call this before the first run. The file handlers are attached to the root
    logger inside configure_tinytroupe_runtime(), which runs after TinyTroupe's
    start_logger() — preventing TinyTroupe from clearing our handlers.
    """
    global _pending_log_dir
    _pending_log_dir = Path(log_dir)


def _apply_file_logging() -> None:
    """Attach file handlers to the root logger (called after TinyTroupe import).

    Creates two files per session:
      info_<ts>.log     — INFO+, clean aligned columns, easy to tail

    There used to be a second warnings_<ts>.log at WARNING+. It carried nothing the
    info log does not: verified across eleven pairs, identical WARNING/ERROR counts and
    identical message text, differing only in showing a full date instead of a time and
    wrapping the message onto its own line. It cost 8.5 MB across the collected runs.
    `grep -E 'WARNING|ERROR' info_<ts>.log` is the replacement.
    """
    global _logging_configured
    if _logging_configured or _pending_log_dir is None:
        return
    _logging_configured = True

    _pending_log_dir.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")

    info_fmt = logging.Formatter(
        fmt="%(asctime)s  %(levelname)-7s  %(name)-16s  %(message)s",
        datefmt="%H:%M:%S",
    )
    info_fh = logging.FileHandler(_pending_log_dir / f"info_{ts}.log", encoding="utf-8")
    info_fh.setLevel(logging.INFO)
    info_fh.setFormatter(info_fmt)

    root = logging.getLogger()
    root.setLevel(logging.DEBUG)
    root.addHandler(info_fh)

    # Pydantic / stdlib warnings → the info log
    _warnings_module.filterwarnings("always")
    logging.captureWarnings(True)

    print(f"  Logs → {_pending_log_dir}/info_{ts}.log")


def ensure_tinytroupe_imports() -> tuple[Any, Any, Any, Any]:
    try:
        from tinytroupe import config_manager
        from tinytroupe.agent import TinyPerson
        from tinytroupe.environment import TinyWorld
        from tinytroupe.factory import TinyPersonFactory
    except ImportError as exc:
        raise SystemExit(
            "Missing dependency: tinytroupe. Install with: "
            "pip install git+https://github.com/microsoft/tinytroupe.git"
        ) from exc

    return config_manager, TinyPerson, TinyWorld, TinyPersonFactory


def configure_tinytroupe_runtime(settings: "ModelSettings") -> None:
    """Point TinyTroupe's global client at these settings. Safe to call repeatedly —
    the discussion and vote phases use different models and re-configure between them."""
    config_manager, TinyPerson, TinyWorld, _ = ensure_tinytroupe_imports()
    _apply_file_logging()  # safe: TinyTroupe's start_logger() has already run
    os.environ["OPENAI_API_KEY"] = settings.api_key
    config_manager.update_multiple({
        "model": settings.model,
        "temperature": float(settings.temperature),
        "max_completion_tokens": int(settings.max_tokens),
    })
    TinyPerson.communication_display = False
    TinyWorld.communication_display = False


def actions_to_text(actions: list[dict[str, Any]] | None) -> str:
    if not actions:
        return ""

    talk_lines: list[str] = []
    other_lines: list[str] = []
    for entry in actions:
        if not isinstance(entry, dict):
            continue
        action = entry.get("action", {})
        if not isinstance(action, dict):
            continue
        action_type = str(action.get("type", "")).strip().upper()
        content = str(action.get("content", "")).strip()
        if action_type == "TALK" and content:
            talk_lines.append(content)
        elif action_type not in {"", "DONE"} and content:
            other_lines.append(f"[{action_type}] {content}")

    if talk_lines:
        return "\n".join(talk_lines)
    if other_lines:
        return "\n".join(other_lines)
    return json.dumps(actions, ensure_ascii=True)
