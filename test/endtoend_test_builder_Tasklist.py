import pytest
import textwrap

from laforge.builder import TaskList, Verb
from laforge import sql
from pandas import DataFrame
from pathlib import Path

TEST_DIR = Path(__file__).parent


FILE_CONTENTS = {
    ".py": textwrap.dedent(
        """\
        from pandas import DataFrame
        def main(*args, **kwargs):
            df = DataFrame(
                [["{name}", int({thing})]], columns=["name", "thing"]
            )
            return df
        """
    ),
    # "_simple.py": "assert 'laforge_test{name}' == 'laforge_test{name}'\n",
    # "_read_a.csv": "name,thing\n{name},{thing}",
    ".csv": "name,thing\n{name},{thing}",
    ".do": "lsdfist\niuadf",
    # 'top 3' MSSQL
    # ".sql": "select top 3 8, 5 as [22d], 3 as bob from information_schema.tables;",
    ".sql": "select 8, 5, 3 as bob from information_schema.tables;",
}

import logging

logger = logging.getLogger(__name__)


def preempt_tasks(cfg, tasks, secrets):
    for task in tasks:
        for subtask in task.subtasks:
            logger.warning("%s", subtask)
            if subtask.verb == Verb.EXECUTE:
                if subtask.content.endswith(";"):
                    # No file needs to be created for query
                    continue
                subdir = "execute_dir"
            elif subtask.verb == Verb.READ:
                subdir = "read_dir"
            else:
                continue
            filepath = Path(cfg["build_dir"], cfg[subdir], subtask.content)
            magically_create_file(filepath)
    magically_create_sql_tables(len(tasks), secrets)


def magically_create_file(filepath):
    if filepath.suffix not in FILE_CONTENTS:
        # probably a sql table
        return None
    if not filepath.parent.exists():
        filepath.parent.mkdir(parents=True)
    dict_bits = {"name": filepath.stem, "thing": 8}
    content = FILE_CONTENTS[filepath.suffix].format(**dict_bits)
    filepath.write_text(content)


def magically_create_sql_tables(n, secrets):
    num_to_create = n * 2
    for i in range(num_to_create):
        name = "laforge_test{}_read".format(i)
        table = sql.Table(name, **secrets["sql"])
        df = DataFrame([[name, i]], columns=["name", "thing"])
        table.write(df)


def test_builder_sql_list(secrets, tmpdir, load_toml):
    task_dict = load_toml("test_builder_sql_list.toml")
    task_dict["config"] = secrets
    task_dict["config"]["build_dir"] = tmpdir
    logger.error(str(task_dict))

    t = TaskList(from_dict=task_dict, location=tmpdir)
    preempt_tasks(task_dict["config"], t.tasks, secrets)
    logger.error(tmpdir)
    for path in tmpdir.glob("**/*"):
        logger.error(path)

    t.execute()


# def test_builder_simple_list(secrets, tmpdir, load_toml):
#     task_dict = load_toml("test_builder_simple_list.toml")
#     task_dict["config"] = secrets
#     task_dict["config"]["build_dir"] = tmpdir
#     t = TaskList(from_dict=task_dict, location=tmpdir)
#     preempt_tasks(task_dict["config"], t.tasks, secrets)
#     t.execute()


# @pytest.mark.stata
# def test_builder_stata_list(secrets, tmpdir, load_toml):
#     task_dict = load_toml("test_builder_stata_list.toml")
#     task_dict["config"] = secrets
#     task_dict["config"]["build_dir"] = tmpdir

#     t = TaskList(from_dict=task_dict, location=tmpdir)
#     preempt_tasks(task_dict["config"], t.tasks, secrets)
#     t.execute()
