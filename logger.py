from datetime import datetime
import logging_config as config

# Цвета для разных уровней логирования
LEVEL_COLORS = {
    "DEBUG": "\033[34m",    # Синий
    "INFO": "\033[32m",     # Зелёный
    "WARNING": "\033[33m",  # Жёлтый
    "ERROR": "\033[31m",    # Красный
    "CRITICAL": "\033[35m", # Фиолетовый
}

def log(msg, level="INFO", show_time=None):
    show_time = config.SHOW_TIME if show_time is None else show_time
    if config.LEVELS[level] < config.LEVELS[config.LOG_LEVEL]:
        return

    timestamp = f"[{datetime.now().strftime('%H:%M:%S')}]" if show_time else ""
    log_str = f"{timestamp} [{level}] {msg}"

    if config.LOG_TO_CONSOLE:
        color = LEVEL_COLORS.get(level, "")
        print(f"{timestamp} {color}[{level}]\033[0m {msg}")

    if config.LOG_TO_FILE:
        with open("app.log", "a", encoding="utf-8") as f:
            f.write(log_str + "\n")
