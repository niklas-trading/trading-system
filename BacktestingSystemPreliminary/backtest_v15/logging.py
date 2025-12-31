import logging
from pathlib import Path
from typing import Any
from logging.handlers import RotatingFileHandler
import glob
import os

_LOG_INITIALISED = False

class PrefixFilter(logging.Filter):
    def __init__(self, prefix: str):
        super().__init__()
        self.prefix = prefix

    def filter(self, record: logging.LogRecord) -> bool:
        return record.name.startswith(self.prefix)

def _wipe_logs(log_dir: Path, base_names: list[str]) -> None:
    # delete *.log and rotated *.log.N
    for name in base_names:
        pattern = str(log_dir / f"{name}*")
        for p in glob.glob(pattern):
            try:
                os.remove(p)
            except OSError:
                pass

def _rotating_file_handler(
        logfile: Path,
        level: int,
        fmt: logging.Formatter,
        max_bytes: int,
        backup_count: int,
        mode_overwrite: bool,
) -> RotatingFileHandler:
    # RotatingFileHandler ignores "w" semantics; we emulate overwrite by deleting files before setup.
    h = RotatingFileHandler(
        logfile,
        mode="a",
        maxBytes=max_bytes,
        backupCount=backup_count,
        encoding="utf-8",
        delay=True,
    )
    h.setLevel(level)
    h.setFormatter(fmt)
    return h

def setup_logging(
        *,
        log_dir: str = "logs",
        console_level: int = logging.INFO,
        file_level: int = logging.DEBUG,
        overwrite: bool = True,
        max_bytes: int = 5_000_000,
        backup_count: int = 10,
) -> Path:
    global _LOG_INITIALISED

    log_path = Path(log_dir)
    log_path.mkdir(parents=True, exist_ok=True)

    # Avoid duplicate handlers
    if _LOG_INITIALISED:
        return log_path

    root = logging.getLogger()
    root.setLevel(logging.DEBUG)

    # Remove existing handlers
    for h in list(root.handlers):
        root.removeHandler(h)

    fmt = logging.Formatter(
        fmt="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Wipe old logs on each run if requested
    if overwrite:
        _wipe_logs(log_path, ["backtest.log", "system.log", "data.log", "universe.log"])

    # Console (high-level)
    ch = logging.StreamHandler()
    ch.setLevel(console_level)
    ch.setFormatter(fmt)
    root.addHandler(ch)

    # Root file (everything)
    root_file = _rotating_file_handler(
        log_path / "backtest.log",
        file_level,
        fmt,
        max_bytes,
        backup_count,
        overwrite,
        )
    root.addHandler(root_file)

    # Split by subsystem (optional but recommended)
    system_h = _rotating_file_handler(log_path / "system.log", file_level, fmt, max_bytes, backup_count, overwrite)
    system_h.addFilter(PrefixFilter("backtest_v15"))
    root.addHandler(system_h)

    data_h = _rotating_file_handler(log_path / "data.log", file_level, fmt, max_bytes, backup_count, overwrite)
    data_h.addFilter(PrefixFilter("backtest_v15.data"))
    root.addHandler(data_h)

    uni_h = _rotating_file_handler(log_path / "universe.log", file_level, fmt, max_bytes, backup_count, overwrite)
    uni_h.addFilter(PrefixFilter("backtest_v15.universe"))
    root.addHandler(uni_h)

    _LOG_INITIALISED = True
    logging.getLogger("backtest_v15").info("Logging initialised (rotating, multi-file) dir=%s", str(log_path))
    return log_path

def log_kv(logger: logging.Logger, level: int, event: str, **fields: Any) -> None:
    if fields:
        parts = []
        for k, v in fields.items():
            sv = "None" if v is None else str(v)
            sv = sv.replace("\n", " ").replace("\r", " ")
            parts.append(f"{k}={sv}")
        msg = event + " " + " ".join(parts)
    else:
        msg = event
    logger.log(level, msg)
