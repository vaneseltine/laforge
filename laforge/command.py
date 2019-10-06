#!/usr/bin/env python3
"""Command-line interface for laforge."""

import functools
import importlib
import importlib.util
import inspect
import logging
import os
import re
import sys
import time
import types
from contextlib import redirect_stdout
from pathlib import Path

from .logo import get_version_display


def run(args=None):
    """Parse arguments as from CLI and execute buildfile

    .. todo:

        "--dry-run", "-n", default=False

    .. todo:

        "--loop", default=False

    .. todo:

        "--log=LOG"         default="laforge.log"
    """
    if args is None:
        args = sys.argv[1:]

    if args in (["-V"], ["--version"]):
        version_info()

    if set(args) & {"-h", "--help"}:
        usage_info()

    try:
        args.remove("--debug")
    except ValueError:
        debug = False
    else:
        debug = True

    try:
        buildfile = find_buildfile(" ".join(args))
    except FileNotFoundError as err:
        print(" ".join(["Error!", *err.args]))
        usage_info(exit_code=1)

    build(buildfile, debug=debug)
    exit(0)


def version_info():
    print(get_version_display())
    exit(0)


def usage_info(exit_code=0):

    usage = """Usage: laforge [OPTIONS] (PATH)...

    laforge: A low-key build system for working with data.

    Options
    -V, --version   Show the package version.
    -h, --help      Show this usage message.
    --debug         Increase logging.

    Path            Path for buildfile; default current dir."""

    print(usage)
    exit(exit_code)


def find_buildfile(path):
    path = Path(path).resolve()
    if not path.exists():
        raise FileNotFoundError(f"{path} does not exist.")
    if path.is_file():
        return path
    _acceptable_globs = ["build*.py", "*laforge*.py"]
    build_files = []
    for fileglob in _acceptable_globs:
        build_files.extend(list(path.glob(fileglob)))
    if not build_files:
        globs = " or ".join(_acceptable_globs)
        raise FileNotFoundError(
            f"No laforge buildfile (e.g., {globs}) found in {path}."
        )
    if len(build_files) > 1:
        found = "; ".join(str(x) for x in build_files)
        raise FileNotFoundError(f"Multiple possible laforge buildfiles found: {found}.")
    return build_files[0]


def build(buildfile=None, log="./laforge.log", debug=False, dry_run=False):
    print(sys.argv)
    if buildfile is None:
        buildfile = sys.argv[0]
    buildfile = Path(buildfile).resolve()
    os.chdir(buildfile.parent)
    run_one_build(
        list_class=FuncList, path=buildfile, log=Path(log), debug=debug, dry_run=dry_run
    )


class FuncList:
    def __init__(self, file, logger):
        # i = importlib.import_module(str(file))
        self.source = Path(file)
        self.logger = logger
        self.mod = self.get_module_from_path(self.source)
        self.functions = list(self.get_functions_from_modules(self.mod))

    def get_functions_from_modules(self, mod, exclude=r"^_.*$"):
        # TODO -- make these a class instead
        for name, obj in inspect.getmembers(mod):
            if not isinstance(obj, (types.FunctionType, functools.partial)):
                continue
            _, line_number = inspect.getsourcelines(obj)
            # self.logger.debug(str(inspect.getsourcelines(obj)))
            if re.match(exclude, name):
                self.logger.debug(f"Exclude {self.source.name}:{line_number} {name}()")
                continue
            self.logger.debug(f"Include {self.source.name}:{line_number:<4}{name}()")
            yield (name, obj, line_number)

    @staticmethod
    def get_module_from_path(path):
        spec = importlib.util.spec_from_file_location("buildfile", str(path))
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        return mod

    def execute(self):
        total_number = len(self.functions)
        for i, stuff in enumerate(sorted(self.functions, key=lambda x: x[-1])):
            name, func, _ = stuff
            self.logger.info(f"{i+1} of {total_number} - {name}:")

            capture_print_to_log = PrintCapture(self.logger)
            with redirect_stdout(capture_print_to_log):
                func()


class PrintCapture(object):
    def __init__(self, logger, stream=sys.stdout):
        self.logger = logger
        self.stream = stream

    def __getattr__(self, name):
        return getattr(self.stream, name)

    def write(self, text):
        useful_lines = (s for s in text.splitlines() if s)
        for line in useful_lines:
            new_line = f"  | {line}"
            self.logger.info(new_line)


def run_one_build(*, list_class, path, log, debug=False, dry_run=False):
    start_time = time.time()
    # THEN set logging -- helps avoid importing pandas at debug level
    logger = get_laforge_logger(log, debug)

    logger.info("%s launched.", path)
    if debug:
        logger.debug("Debug mode is on.")

    task_list = list_class(path, logger=logger)
    if dry_run:
        task_list.dry_run()
        return
    task_list.execute()
    elapsed = round(time.time() - start_time, 2)
    logger.info("%s completed in %s seconds.", path, elapsed)


def get_laforge_logger(log_file, debug):
    noisiness = logging.DEBUG if debug else logging.INFO

    if noisiness == logging.DEBUG:
        formatter = logging.Formatter(
            fmt="{asctime} {name:<20} {lineno:>3}:{levelname:<7} {message}",
            style="{",
            datefmt=r"%Y%m%d-%H%M%S",
        )
    else:
        formatter = logging.Formatter(
            fmt="{asctime} {levelname:>7} {message}", style="{", datefmt=r"%H:%M:%S"
        )
    file_handler = logging.FileHandler(filename=log_file)
    file_handler.setFormatter(formatter)
    stream_handler = logging.StreamHandler(sys.stdout)
    stream_handler.setFormatter(formatter)
    handlers = [file_handler, stream_handler]
    logging.basicConfig(level=logging.INFO, handlers=handlers)

    logging.getLogger().setLevel(noisiness)

    new_logger = logging.getLogger(__name__)
    new_logger.debug(f"Logging: {log_file}")
    return new_logger
