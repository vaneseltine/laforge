import functools
import pandas as pd
from .builder import Task, Target, Verb
from pathlib import Path


def read(variable, content):
    target = Target.parse(content)
    task = Task.from_qualified(
        verb=Verb.READ,
        target=target,
        content=content,
        config={"dir": {}},
        identifier="READ:hi",
    )
    result = task.implement()
    kwargs = {variable: result}

    def decorator_read(func):
        # TODO: fucntools.wraps() this so it's the proper function?
        @functools.wraps(func)
        def wrapped_read():
            return functools.partial(func, **kwargs)()

        return wrapped_read

    return decorator_read
