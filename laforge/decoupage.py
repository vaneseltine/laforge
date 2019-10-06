import functools
import logging

from .builder import Target, Task, Verb

logger = logging.getLogger(__name__)
logger.debug(logger.name)


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
