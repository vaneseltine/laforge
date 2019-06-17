import string
from pathlib import Path
from textwrap import dedent

import pandas as pd
import pytest

from laforge import builder, sql

hypothesis = pytest.importorskip("hypothesis")
from hypothesis import given, reproduce_failure, settings, strategies  # noqa
from hypothesis.extra.pandas import column, data_frames, range_indexes


TEST_TASKS = dedent(
    """\

    [original_csv_to_sql]
    read = sample1.csv
    write = sample2

    [sql_to_csv]
    read = sample2
    write = sample3.csv

    [csv_back_to_sql]
    read = sample3.csv
    write = sample4

    [sql_to_csv2]
    read = sample4
    write = sample5.csv

    [csv_back_to_sql2]
    read = sample5.csv
    write = sample6

"""
)


columns = [
    column(
        name="text_col",
        elements=strategies.text(min_size=0, max_size=4000, alphabet=string.printable),
        unique=True,
    ),
    column(name="int_col", elements=strategies.integers()),
    column(
        name="float_col",
        elements=strategies.floats(
            # min and max value brought to you by MSSQL --
            # if you want it larger, take it up with MSSQL.
            allow_infinity=False,
            min_value=-1.79e308,
            max_value=1.79e308,
        ),
    ),
    column(name="email_col", elements=strategies.emails()),
]
hypo_df = data_frames(columns=columns, index=range_indexes(5, 5))


def makeset(results):
    """
    this addresses two potential non-concerning inconsistencies:

    - Nan vs. None
    - 0. vs. 0.0

    """

    return set((str(df).replace("0.", "  ") for df in results))


def create_ini_contents(build_dir, tasks, **secrets):
    INI_HEADER = f"[DEFAULT]\nbuild_dir = {build_dir}\n"
    ini_secrets = "\n".join(f"{key} = {value}" for key, value in secrets.items())
    return INI_HEADER + ini_secrets + "\n\n" + tasks


@pytest.mark.slow
@given(df=hypo_df)
@settings(max_examples=50, deadline=5000)
def test_run_sqlite(tmpdir, df):

    db = Path(tmpdir / "sqlite.db")
    if not db.exists():
        db.touch()
    c = sql.Channel("sqlite", database=db)

    original_file = Path(tmpdir / "sample1.csv").resolve()
    df.to_csv(original_file)
    try:
        _ = pd.read_csv(original_file)
    except pd.errors.ParserError:
        return None

    ini_contents = create_ini_contents(
        build_dir=tmpdir,
        tasks=TEST_TASKS,
        distro="sqlite",
        database=f"{tmpdir}/sqlite.db",
    )

    builder.TaskList(from_string=ini_contents).execute()

    sql_results = [
        sql.Table(f"sample{i}", channel=c).read().fillna(0) for i in (2, 4, 6)
    ]
    csv_results = [
        pd.read_csv(Path(tmpdir / f"sample{i}.csv")).fillna(0) for i in (3, 5)
    ]
    resultset1 = makeset(sql_results + csv_results)
    assert len(resultset1) == 1


@pytest.mark.slow
@given(df=hypo_df)
@settings(max_examples=50, deadline=None)
def test_run_default_sql(tmpdir, secrets, df):

    original_file = Path(tmpdir / "sample1.csv").resolve()
    df.to_csv(original_file)
    try:
        _ = pd.read_csv(original_file)
    except pd.errors.ParserError:
        return None

    c = sql.Channel(**secrets["sql"])
    ini_contents = create_ini_contents(
        build_dir=tmpdir, tasks=TEST_TASKS, **secrets["sql"]
    )

    builder.TaskList(from_string=ini_contents).execute()

    sql_results = [
        sql.Table(f"sample{i}", channel=c).read().fillna(0) for i in (2, 4, 6)
    ]
    csv_results = [
        pd.read_csv(Path(tmpdir / f"sample{i}.csv")).fillna(0) for i in (3, 5)
    ]

    resultset1 = makeset(sql_results + csv_results)
    assert len(resultset1) in (1, 2)
    for t in ("sample2", "sample4", "sample6"):
        sql.Table(t, channel=c).drop()
