import sys
import logging
import pathlib
from logging import handlers
from systemd import journal


# log file path
log_file = pathlib.Path(__file__).absolute().parent.joinpath("logs").joinpath("ddns_updater.log")

# set formatter
formatter = logging.Formatter('%(asctime)s | %(name)s - %(levelname)s | %(message)s')

# create logger
DDNS_logger = logging.getLogger('ddns_updater')

# add handlers
journal_handler = journal.JournalHandler()
journal_handler.setFormatter(formatter)
DDNS_logger.addHandler(journal_handler)
stdout_handler = logging.StreamHandler(sys.stdout)
stdout_handler.setFormatter(formatter)
DDNS_logger.addHandler(stdout_handler)
file_handler = handlers.TimedRotatingFileHandler(
    filename=log_file, backupCount=20,
    when="midnight", interval=1)
file_handler.setFormatter(formatter)
DDNS_logger.addHandler(file_handler)

# set logging level
DDNS_logger.setLevel(logging.INFO)
