# logger_manager.py
import logging

class EmojiFormatter(logging.Formatter):
    EMOJIS = {
        logging.DEBUG: "🐛",
        logging.INFO: "✅",
        logging.WARNING: "⚠️ ",
        logging.ERROR: "❌",
        logging.CRITICAL: "💥",
    }

    def format(self, record):
        emoji = self.EMOJIS.get(record.levelno, "")
        record.levelname = emoji  # substitui INFO/WARNING/etc. por emoji
        return super().format(record)


class LoggerManager:
    @staticmethod
    def setup(level=logging.INFO):
        """Configure the root logger with emoji-based formatter."""
        handler = logging.StreamHandler()
        formatter = EmojiFormatter(
            fmt="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
            datefmt="%H:%M:%S"
        )
        handler.setFormatter(formatter)

        root_logger = logging.getLogger()
        root_logger.setLevel(level)
        root_logger.handlers.clear()  # limpa handlers anteriores, evita duplicação
        root_logger.addHandler(handler)

    @staticmethod
    def get_logger(name: str) -> logging.Logger:
        """Get a named logger for the current module."""
        return logging.getLogger(name)
