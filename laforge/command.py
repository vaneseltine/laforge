#!/usr/bin/env python3
"""Command-line interface for laforge."""

import logging
import sys
import time
from pathlib import Path

import functools
import importlib
import importlib.util
import inspect
import io
import re
import types
from contextlib import redirect_stdout

USAGE = """Usage: laforge [OPTIONS] (PATH)...

laforge: A low-key build system for working with data.

Options
-V, --version   Show the package version.
-h, --help      Show this usage message.
--debug         Increase logging.

Path            Path for buildfile; default current dir."""


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

    build_dir = buildfile.parent
    build(buildfile, build_dir=build_dir, debug=debug)
    exit(0)


def version_info():
    from .logo import get_version_display

    print(get_version_display())
    exit(0)


def usage_info(exit_code=0):
    print(USAGE)
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


def build(
    buildfile, build_dir, log="./laforge.log", debug=False, dry_run=False, loop=False
):
    runs = 1 if not loop else 100
    for _ in range(runs):
        run_one_build(
            list_class=FuncList,
            path=Path(buildfile),
            home=build_dir,
            log=Path(log),
            debug=debug,
            dry_run=dry_run,
        )
        if loop:
            response = input("\nEnter to rebuild, anything else to quit: ")
            if response:
                break
            print("")


HOME = None


class FuncList:
    def __init__(self, file, home, logger):
        # i = importlib.import_module(str(file))
        self.source = file
        global HOME
        HOME = home
        self.logger = logger
        self.mod = self.get_module_from_path(self.source)
        self.functions = self.get_functions_from_modules(self.mod)

    @staticmethod
    def get_functions_from_modules(mod, exclude=r"^_.*$"):
        # TODO -- make these a class instead
        return (
            (name, obj, inspect.getsourcelines(obj)[-1])
            for name, obj in inspect.getmembers(mod)
            # if callable(obj)
            if isinstance(obj, (types.FunctionType, functools.partial))
            and not re.match(exclude, name)
        )

    @staticmethod
    def get_module_from_path(path):
        spec = importlib.util.spec_from_file_location("buildfile", str(path))
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        return mod

    def execute(self):
        for name, obj, lineno in sorted(self.functions, key=lambda x: x[-1]):
            self.logger.info(f"Line #{lineno}")
            self.logger.info(f"{name}()")

            with redirect_stdout(FilteredPrint()):
                obj()

    def modified_print(self, output):
        for line in output.splitlines():
            self.logger.info(f"|  {line}")


class FilteredPrint(object):
    def __init__(self, stream=sys.stdout, default_sep=" ", default_end="\n"):
        self.stdout = stream
        self.default_sep = default_sep
        self.default_end = default_end
        self.continuing_same_print = False
        self.file = open("log.txt", "a")

    def __getattr__(self, name):
        return getattr(self.stdout, name)

    def write(self, text):
        if text is self.default_end:
            self.continuing_same_print = False
        elif text is self.default_sep:
            self.continuing_same_print = True

        new_text = text
        if text in {self.default_sep, self.default_end}:
            pass
        elif self.continuing_same_print:
            pass
        else:
            new_text = f"| {new_text}"

        self.stdout.write(new_text)
        self.flush()


def run_one_build(*, list_class, path, home, log, debug=False, dry_run=False):
    start_time = time.time()
    # THEN set logging -- helps avoid importing pandas at debug level
    logger = get_package_logger(log, debug)

    logger.info("%s launched.", path)
    if debug:
        logger.debug("Debug mode is on.")

    task_list = list_class(path, home=home, logger=logger)
    if dry_run:
        task_list.dry_run()
        return
    task_list.execute()
    elapsed = round(time.time() - start_time, 2)
    logger.info("%s completed in %s seconds.", path, elapsed)


def get_package_logger(log_file, debug):
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
