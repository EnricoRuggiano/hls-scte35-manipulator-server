import logging
from logging import Logger
import sys

_FORMAT = '%(asctime)s | %(levelname)s | %(message)s'
_LEVEL_ALIASES = {
	"WARN": "WARNING",
}


class _LoggerSingleton:
	_instance = None

	def __new__(cls):
		if cls._instance is None:
			cls._instance = super().__new__(cls)
			cls._instance._logger = None
		return cls._instance

	def get_logger(self) -> Logger:
		if self._logger is None:
			logger = logging.getLogger("scte35_injector")
			logger.setLevel(logging.INFO)
			logger.propagate = False

			if not logger.handlers:
				handler = logging.StreamHandler(sys.stdout)
				handler.setFormatter(logging.Formatter(_FORMAT))
				logger.addHandler(handler)

			self._logger = logger
		return self._logger

	def configure(self, log_level: str = "INFO") -> Logger:
		logger = self.get_logger()
		level_name = _LEVEL_ALIASES.get(str(log_level).upper(), str(log_level).upper())
		level = getattr(logging, level_name, logging.INFO)

		logger.setLevel(level)
		for handler in logger.handlers:
			handler.setLevel(level)
		return logger


_singleton = _LoggerSingleton()


def init_logger(log_level: str = "INFO") -> Logger:
	return _singleton.configure(log_level)


def get_logger() -> Logger:
	return _singleton.get_logger()


logger: Logger = get_logger()

