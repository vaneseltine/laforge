import functools
import importlib
import importlib.util
import inspect
import logging
import re
import sys
import time
import types
from contextlib import redirect_stdout
from pathlib import Path


class FuncRunner:
    def __init__(self, file, logger):
        self.source = Path(file)
        self.logger = logger
        self.mod = self.get_module_from_path(self.source)
        self.functions = list(self.get_functions_from_modules(self.mod))

    def get_functions_from_modules(self, mod, exclude=r"^_.*$"):
        # Make these a class instead
        for name, obj in inspect.getmembers(mod):
            if not isinstance(obj, (types.FunctionType, functools.partial)):
                continue
            _, line_number = inspect.getsourcelines(obj)
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
            human_number = i + 1
            name, func, _ = stuff
            print()
            self.logger.info(f"{human_number} of {total_number}: {name}()")

            capture_print_to_log = PrintCapture(self.logger)
            with redirect_stdout(capture_print_to_log):
                try:
                    func()
                    self.logger.info(f"{human_number} of {total_number}: complete")
                except Exception as err:  # pylint: disable=broad-except
                    handle_mid_task_exception(
                        err=err,
                        logger=self.logger,
                        human_number=human_number,
                        task_name=name,
                    )
        print()


def handle_mid_task_exception(err, logger, human_number, task_name):
    logger.exception(err)
    logger.error(f"-- HALTED at #{human_number}: {task_name} raised {repr(err)}.")
    exit(1)


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


def engage(*, path, log, debug=False, dry_run=False, list_class=FuncRunner):
    start_time = time.time()
    # Only now set logging helps avoid pandas load time
    # And keeps pandas from logging at debug level
    logger = get_laforge_logger(Path(log), debug)

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
