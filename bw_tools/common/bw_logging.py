import logging
from pathlib import Path
from typing import Dict

import sd


def create_logger(log_file: Path) -> Dict:
    ret = {}

    # need to remove existing handlers otherwise the logger doesnt create files
    for handler in logging.root.handlers[:]:
        logging.root.removeHandler(handler)
    ret["logger"] = logging.getLogger()
    ret["logger"].setLevel(logging.DEBUG)

    # file handler
    ret["file_handler"] = logging.FileHandler(
        filename=log_file,
        mode="w",
    )
    ret["file_handler"].setFormatter(
        logging.Formatter(
            fmt="[%(asctime)s][%(levelname)s] : %(message)s",
            datefmt="%Y/%m/%d - %H:%M:%S",
        )
    )
    ret["file_handler"].setLevel(logging.DEBUG)
    ret["logger"].addHandler(ret["file_handler"])

    # Stream handler
    ret["stream_handler"] = sd.getContext().createRuntimeLogHandler()
    ret["stream_handler"].setLevel(logging.DEBUG)
    ret["logger"].addHandler(ret["stream_handler"])

    ret["logger"].propagate = False
    ret["logger"].info("Logger initialized.")

    return ret
