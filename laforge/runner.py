import functools
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

import dotenv


class Func:
    def __init__(self, name, function_object, code, line, module, logger):
        self.name = name
        self.function_object = function_object
        self.code = code
        self.line = line
        self.module = module
        self.file = Path(self.module.__file__).relative_to(Path(".").absolute())
        self.logger = logger
        self.live = False

    def apply_filters(self, *, include="", exclude=""):
        included = not include or re.search(include, self.name)
        excluded = exclude and re.search(exclude, self.name)
        self.live = included and not excluded

    def raise_exception(self, i, err):
        self.logger.exception(err)
        self.logger.error(f"BUILD HALTED at #{i}: {self.name} raised {repr(err)}.")
        exit(1)

    def __call__(self, *args, **kwargs):
        return self.function_object(*args, **kwargs)

    def __str__(self):
        return f"{self.name}, lines {self.line}-{self.line + len(self.code) - 1}"

    def __repr__(self):
        return f"Func({self.file.stem}.{self.name})"

    def __eq__(self, other):
        return self.function_object == other.function_object

    def __lt__(self, other):
        return self.line < other.line


class FuncRunner:

    MANDATORY_EXCLUDE = "^_"

    def __init__(
        self, file, *, include="", exclude="", config=None, logger=logging.NullHandler
    ):
        self.source = Path(file)
        self.include = include
        self.exclude = exclude
        self.config = config or {}
        self.logger = logger
        self.module = self.get_module_from_path(self.source)
        self.functions = sorted(self.collect_functions(self.module))

    def collect_functions(self, module):
        for code, line, name, function_object in self.pull_all_functions(module):
            func = Func(
                name=name,
                function_object=function_object,
                code=code,
                line=line,
                module=self.module,
                logger=self.logger,
            )
            func.apply_filters(include=self.include, exclude=self.exclude)
            self.logger.debug(f"Collected {func}; active: {func.live}")
            yield func

    @classmethod
    def pull_all_functions(cls, module):
        for name, function_object in inspect.getmembers(module):
            if re.search(cls.MANDATORY_EXCLUDE, name):
                continue
            if not isinstance(function_object, (types.FunctionType, functools.partial)):
                continue
            code, line = inspect.getsourcelines(function_object)
            yield code, line, name, function_object

    @staticmethod
    def get_module_from_path(path):
        spec = importlib.util.spec_from_file_location("buildfile", str(path))
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    @property
    def live_functions(self):
        return (
            (i + 1, func) for i, func in enumerate(f for f in self.functions if f.live)
        )

    def list_only(self):
        live_count = 0
        for func in self.functions:
            if func.live:
                live_count += 1
                human = human = f"{live_count} of {len(self)}"
            else:
                human = "-"
            self.logger.info(f"{human:>8} {func}")

    def __len__(self):
        return len([x for x in self.functions if x.live])

    def execute(self):
        for i, func in self.live_functions:
            if not func.live:
                continue
            print()
            self.logger.info(f"{i} of {len(self)}: {func}")

            capture_print_to_log = PrintCapture(self.logger)
            with redirect_stdout(capture_print_to_log):
                try:
                    func()
                    self.logger.info(f"{i} of {len(self)}: complete")
                except Exception as err:  # pylint: disable=broad-except
                    func.raise_exception(i, err)
        print()


class PrintCapture:
    """A simplified capture of sys.stdout into logging

    This chops up things a bit, but is fairly straightforward.
    """

    def __init__(self, logger, stream=sys.stdout):
        self.logger = logger
        self.stream = stream

    def __getattr__(self, name):
        return getattr(self.stream, name)

    def write(self, text):
        useful_lines = (s for s in text.splitlines() if s.strip())
        for line in useful_lines:
            new_line = f"  | {line}"
            self.logger.info(new_line)


def engage(
    *,
    buildfile,
    log=None,
    debug=False,
    list_only=False,
    include="",
    exclude="",
    list_class=FuncRunner,
    config=None,
):
    os.chdir(buildfile.parent)
    start_time = time.time()
    # Keeps pandas from logging at debug level
    logger = get_laforge_logger(log, debug)

    logger.info("%s launched.", buildfile)
    if debug:
        logger.debug("Debug mode is on.")

    func_list = list_class(
        buildfile, include=include, exclude=exclude, config=config, logger=logger
    )
    if list_only:
        logger.info(f"Build plan for {buildfile.absolute()}:")
        func_list.list_only()
        return
    func_list.execute()
    elapsed = round(time.time() - start_time, 2)
    logger.info("%s completed in %s seconds.", buildfile, elapsed)


def get_laforge_logger(log_file=None, debug=False):
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
    stream_handler = logging.StreamHandler(sys.stdout)
    stream_handler.setFormatter(formatter)
    handlers = [stream_handler]
    if log_file is not None:
        file_handler = logging.FileHandler(filename=log_file)
        file_handler.setFormatter(formatter)
        handlers.append(file_handler)
    logging.basicConfig(level=logging.INFO, handlers=handlers)

    logging.getLogger().setLevel(noisiness)

    new_logger = logging.getLogger(__name__)
    new_logger.debug(f"Logging: {log_file}")
    return new_logger
