import sys
import logging
import pathlib
from logging import Logger, handlers
from systemd import journal


class TaskLogger(logging.Logger):

    def __new__(cls, name: str, level: int | str = logging.INFO) -> Logger:
        new_logger = logging.getLogger(name=name)
        new_logger.setLevel(level=level)

        # log file path
        log_file = pathlib.Path(__file__).absolute().parent.joinpath("logs").joinpath(name + ".log")
        # set formatter
        formatter = logging.Formatter('%(asctime)s | %(name)s - %(levelname)s | %(message)s')

        # add handlers
        journal_handler = journal.JournalHandler()
        journal_handler.setFormatter(formatter)
        new_logger.addHandler(journal_handler)
        stdout_handler = logging.StreamHandler(sys.stdout)
        stdout_handler.setFormatter(formatter)
        new_logger.addHandler(stdout_handler)
        file_handler = handlers.TimedRotatingFileHandler(
            filename=log_file, backupCount=20,
            when="midnight", interval=1)
        file_handler.setFormatter(formatter)
        new_logger.addHandler(file_handler)

        return new_logger
