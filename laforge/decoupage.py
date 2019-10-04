import functools
import pandas as pd
from .builder import Task, Target, Verb
from pathlib import Path


def read(variable, content):
    kwargs = {variable: content}
    target = Target.parse(content)
    task = Task.from_qualified(
        verb=Verb.READ,
        target=target,
        content=content,
        config={"dir": {}},
        # identifier=f"{config.get('section', '')}.{raw_verb}",
        identifier="READ:hi",
    )
    result = task.implement()
    print("kwargs", kwargs)
    print(result)

    def decorator_read(func):
        return functools.partial(func, **kwargs)

    return decorator_read
