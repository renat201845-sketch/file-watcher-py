import json
import logging
import os
import time
from pathlib import Path


def load_config(config_path: Path) -> dict:
    default_config = {
        "target_dir": str(Path.home() / "Desktop" / "test_watch"),
        "interval_seconds": 3,
        "log_file": "watcher.log",
        "extensions": [],
    }
    if not config_path.exists():
        config_path.write_text(
            json.dumps(default_config, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        return default_config

    with config_path.open("r", encoding="utf-8") as f:
        user_config = json.load(f)

    return {**default_config, **user_config}


def setup_logger(log_file: Path) -> logging.Logger:
    logger = logging.getLogger("file_watcher")
    logger.setLevel(logging.INFO)
    logger.handlers.clear()

    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)-7s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    file_handler = logging.FileHandler(log_file, encoding="utf-8")
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    return logger


def is_allowed_file(path: Path, extensions: list[str]) -> bool:
    if not extensions:
        return True
    allowed = {ext.lower() if ext.startswith(".") else f".{ext.lower()}" for ext in extensions}
    return path.suffix.lower() in allowed


def scan_folder(folder_path: Path, extensions: list[str]) -> dict[str, tuple[int, float]]:
    snapshot: dict[str, tuple[int, float]] = {}
    if not folder_path.exists():
        return snapshot

    for root, _, files in os.walk(folder_path):
        for filename in files:
            full_path = Path(root) / filename
            if not is_allowed_file(full_path, extensions):
                continue
            try:
                stat = full_path.stat()
                snapshot[str(full_path)] = (stat.st_size, stat.st_mtime)
            except OSError:
                continue

    return snapshot


def main() -> None:
    base_dir = Path(__file__).resolve().parent
    config = load_config(base_dir / "config.json")

    target_dir = Path(config["target_dir"])
    interval = max(0.5, float(config["interval_seconds"]))
    log_path = base_dir / config["log_file"]
    extensions = config.get("extensions", [])

    logger = setup_logger(log_path)
    target_dir.mkdir(parents=True, exist_ok=True)

    logger.info(f"Запуск мониторинга: {target_dir} (интервал: {interval} сек)")
    if extensions:
        logger.info(f"Фильтр расширений: {', '.join(extensions)}")
    logger.info("Нажми Ctrl + C для остановки.")

    previous = scan_folder(target_dir, extensions)
    stats = {"new": 0, "changed": 0, "deleted": 0}

    try:
        while True:
            time.sleep(interval)
            current = scan_folder(target_dir, extensions)

            for path in current:
                if path not in previous:
                    stats["new"] += 1
                    logger.info(f"[NEW]     {path} ({current[path][0]} байт)")

            for path in previous:
                if path not in current:
                    stats["deleted"] += 1
                    logger.info(f"[DELETED] {path}")

            for path, meta in current.items():
                if path in previous and previous[path] != meta:
                    stats["changed"] += 1
                    logger.info(f"[CHANGED] {path} ({meta[0]} байт)")

            previous = current
    except KeyboardInterrupt:
        logger.info(
            f"Остановлено. Итого за сессию — новых: {stats['new']}, "
            f"изменено: {stats['changed']}, удалено: {stats['deleted']}"
        )


if __name__ == "__main__":
    main()