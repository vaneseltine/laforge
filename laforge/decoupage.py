import functools
import logging

from .builder import Target, Task, Verb

logger = logging.getLogger(__name__)
logger.debug(logger.name)


def write():
    pass


def execute():
    pass


def exist(content):
    content = str(content)
    target = Target.parse(content)
    task = Task.from_qualified(verb=Verb.EXIST, target=target, content=content)
    try:
        result = task.implement()
    except FileNotFoundError:
        logger.error(f"{content} does not exist.")
        exit(2)

    def decorator_exist(func):
        @functools.wraps(func)
        def wrapped_exist():
            return func()

        logger.debug(f"Result of exist is {type(result)}")
        return wrapped_exist

    return decorator_exist


def read(variable, content):
    target = Target.parse(content)
    task = Task.from_qualified(verb=Verb.READ, target=target, content=content)
    result = task.implement()
    kwargs = {variable: result}

    def decorator_read(func):
        @functools.wraps(func)
        def wrapped_read():
            return functools.partial(func, **kwargs)()

        logger.debug(f"Result of read is {type(result)}")
        return wrapped_read

    return decorator_read
