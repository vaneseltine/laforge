""" """
from pathlib import Path
import logging
import sys
import time
from typing import Optional, Union

import click


def run_build(
    script_path: Union[str, Path], debug: bool = False, log_file: Optional[Path] = None
) -> None:
    """laforge's core build command"""
    path = Path(script_path)
    if debug:
        click.echo("Debug mode is on.")
    if path.is_dir():
        path = find_build_config_in_directory(path)

    start_time = time.time()
    if log_file:
        logger = get_package_logger(log_file, debug)
    else:
        logger = logging.getLogger(__name__)

    # THEN set logging -- helps avoid importing pandas at debug level

    logger.info("%s launched.", script_path)

    task_list = TaskList(script_path)
    task_list.execute()

    elapsed = seconds_since(start_time)
    logger.info("%s completed in %s seconds.", script_path, elapsed)


def find_build_config_in_directory(path: Path) -> Path:
    _acceptable_globs = ["build*.ini", "*laforge*.ini"]
    build_files = None
    for fileglob in _acceptable_globs:
        build_files = list(path.glob(fileglob))
        if build_files:
            break
    if not build_files:
        print(
            "ERROR: No laforge INI (e.g., {eg}) "
            "found in {dir}. ".format(dir=path, eg=(" or ".join(_acceptable_globs)))
        )
        exit(1)
    if len(build_files) > 1:
        print("ERROR: Must specify a laforge INI: {}".format(build_files))
        exit(1)
    return build_files[0]


def seconds_since(previous_time: float, round_to: int = 2) -> float:
    elapsed_raw = time.time() - previous_time
    if round_to:
        return round(elapsed_raw, round_to)
    return elapsed_raw


def get_package_logger(log_file: Path, debug: bool) -> logging.Logger:

    noisiness = logging.DEBUG if debug else logging.INFO

    if noisiness == logging.DEBUG:
        formatter = logging.Formatter(
            fmt="{asctime} {name:<20} {lineno:>3}:{levelname:<7} | {message}",
            style="{",
            datefmt=r"%Y%m%d-%H%M%S",
        )
    else:
        formatter = logging.Formatter(
            fmt="{asctime} {levelname:>7} | {message}", style="{", datefmt=r"%H:%M:%S"
        )
    file_handler = logging.FileHandler(filename=log_file)
    file_handler.setFormatter(formatter)
    stream_handler = logging.StreamHandler(sys.stdout)
    stream_handler.setFormatter(formatter)
    handlers = [file_handler, stream_handler]
    logging.basicConfig(level=logging.INFO, handlers=handlers)

    logging.getLogger().setLevel(noisiness)
    return logging.getLogger(__name__)


class TaskList:
    def __init__(self, *args, **kwargs):
        pass

    def execute(self, *args, **kwargs):
        pass
