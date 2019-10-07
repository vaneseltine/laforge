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

ACCUMULATED_RESULTS = {}


def save(variable):
    """Specify a variable; return value will be provided as fixture."""

    def decorator_func(func):
        @functools.wraps(func)
        def wrapper_func(*args, **kwargs):
            # Invoke the wrapped function first
            retval = func(*args, **kwargs)
            # Now do something here with retval and/or action
            ACCUMULATED_RESULTS[variable] = retval
            logger.debug(
                f"Saved a {type(retval)} under ACCUMULATED_RESULTS['{variable}']..."
            )
            return retval

        return wrapper_func

    return decorator_func


def load(variable):
    """Specify a variable; retrieve and pass earlier save."""

    def decorator_func(func):
        @functools.wraps(func)
        def wrapper_func(*args, **kwargs):
            # Invoke the wrapped function first
            kwargs[variable] = ACCUMULATED_RESULTS[variable]
            logger.debug(
                f"Retrieved a {type(kwargs[variable])} under ACCUMULATED_RESULTS['{variable}']..."
            )
            return func(*args, **kwargs)

        return wrapper_func

    return decorator_func


def write():
    """Return value will be written to specified target."""


def execute():
    pass


def exist(content):
    assert content

    def decorator_exist(func):
        content = str(content)
        target = Target.parse(content)
        task = Task.from_qualified(verb=Verb.EXIST, target=target, content=content)
        try:
            result = task.implement()
        except FileNotFoundError:
            logger.error(f"{content} does not exist.")
            exit(2)

        @functools.wraps(func)
        def wrapped_exist():
            return func

        logger.debug(f"Result of exist is {type(result)}")
        return wrapped_exist()

    return decorator_exist


def read(variable, content):
    logger.debug(f"Adding a read for {variable} of {content}")

    def decorator_read(func):
        # result = None

        @functools.wraps(func)
        def wrapped_read(*args, **kwargs):
            target = Target.parse(content)
            task = Task.from_qualified(verb=Verb.READ, target=target, content=content)
            result = task.implement()
            kwargs[variable] = result
            logger.debug(f"Result of read is {type(result)}")
            print(func)
            setattr(func, variable, result)
            return functools.partial(func, *args, **kwargs)()

        print("func", func)
        print("wrapped_read", wrapped_read)
        # Attach result to function
        # setattr(wrapped_read, variable, result)
        return wrapped_read

    print("decorator_read", decorator_read)
    # setattr(wrapped_read, variable, result)

    return decorator_read
