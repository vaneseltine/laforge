import functools
import logging

from .builder import Target, Task, Verb

logger = logging.getLogger(__name__)
logger.debug(logger.name)


"""
https://stackoverflow.com/questions/14703310/
def audit_action(action):
    def decorator_func(func):
        def wrapper_func(*args, **kwargs):
            # Invoke the wrapped function first
            retval = func(*args, **kwargs)
            # Now do something here with retval and/or action
            print('In wrapper_func, handling action {!r} after wrapped function returned {!r}'.format(action, retval))
            return retval
        return wrapper_func
    return decorator_func
"""

# __all__ = ["save", "load", "write", "execute", "read", "exist"]

RESULTS = {}


def save(variable):
    """Save return value of decorated function under `variable`."""

    def decorator_func(func):
        @functools.wraps(func)
        def wrapper_func(*args, **kwargs):
            result = func(*args, **kwargs)
            RESULTS[variable] = result
            logger.debug(f"Saved a {type(result)} under RESULTS['{variable}']...")
            return result

        return wrapper_func

    return decorator_func


def load(variable):
    """Retrieve earlier result previously saved under `variable`."""

    def decorator_func(func):
        @functools.wraps(func)
        def wrapper_func(*args, **kwargs):
            # Invoke the wrapped function first
            kwargs[variable] = RESULTS[variable]
            logger.debug(
                f"Retrieved a {type(kwargs[variable])} under RESULTS['{variable}']..."
            )
            result = func(*args, **kwargs)
            return result

        return wrapper_func

    return decorator_func


def write():
    """Return value will be written to specified target."""


def execute():
    pass


def read(variable, content):
    """Pass DataFrame of target into function parameters"""
    logger.debug(f"Adding a read of {content}, passing in as {variable}")

    def decorator_read(func):
        @functools.wraps(func)
        def wrapped_read(*args, **kwargs):
            target = Target.parse(content)
            task = Task.from_qualified(verb=Verb.READ, target=target, content=content)
            result = task.implement()
            kwargs[variable] = result
            return functools.partial(func, *args, **kwargs)()

        return wrapped_read

    return decorator_read


def exists(content):
    """Pass DataFrame of target into function parameters"""
    logger.debug(f"Adding a existence check on {content}")

    def decorator_exists(func):
        @functools.wraps(func)
        def wrapped_exists(*args, **kwargs):
            target = Target.parse(content)
            task = Task.from_qualified(verb=Verb.EXIST, target=target, content=content)
            try:
                task.implement()
            except FileNotFoundError:
                exit_failure(f"Could not verify existence of {content}", task)
            return func(*args, **kwargs)

        return wrapped_exists

    return decorator_exists


def exit_failure(reason, task):
    logger.error(reason)
    logger.debug(repr(task))
    exit(9)
