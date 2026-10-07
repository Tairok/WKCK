import logging
import os

from config import Config

# Ensure every LogRecord contains a 'cls' attribute to avoid KeyError in formatters
_old_factory = logging.getLogRecordFactory()

def _record_factory(*args, **kwargs):
    record = _old_factory(*args, **kwargs)
    if not hasattr(record, 'cls'):
        record.cls = '-'
    return record

logging.setLogRecordFactory(_record_factory)

DEFAULT_LOGFILE = Config.LOG_PATH
LOG_LEVELS = logging._nameToLevel


class AddClsFilter(logging.Filter):
    def filter(self, record):
        if not hasattr(record, 'cls'):
            record.cls = '-'
        return True


class SafeFormatter(logging.Formatter):
    def format(self, record):
        try:
            return super().format(record)
        except KeyError as e:
            missing = e.args[0]
            setattr(record, missing, '-')
            return super().format(record)


def _resolve_level(name, fallback):
    return LOG_LEVELS.get(name, fallback)


def setup_logger():
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)

    # ensure a safe default field for class name
    logger.addFilter(AddClsFilter())

    # prepare formatter and ensure existing handlers can format safely
    formatter = SafeFormatter(
        "[%(asctime)s] %(levelname)s %(name)s %(module)s.%(funcName)s:%(lineno)d [%(cls)s] - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    if not logger.hasHandlers():
        os.makedirs(os.path.dirname(DEFAULT_LOGFILE), exist_ok=True)

        file_handler = logging.FileHandler(DEFAULT_LOGFILE, encoding="utf-8")
        file_handler.setFormatter(formatter)
        file_handler.setLevel(_resolve_level(Config.LOG_FILE_LEVEL, logging.DEBUG))

        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        console_handler.setLevel(_resolve_level(Config.LOG_CONSOLE_LEVEL, logging.INFO))

        logger.addHandler(file_handler)
        logger.addHandler(console_handler)
    else:
        # ensure any existing handlers use the safe formatter
        for h in logger.handlers:
            try:
                h.setFormatter(formatter)
            except Exception:
                # best-effort: ignore handler issues
                pass

    return logger
