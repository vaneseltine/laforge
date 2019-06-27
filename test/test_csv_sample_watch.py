from pathlib import Path
from textwrap import dedent

import pandas as pd
import pytest

from laforge import builder, sql

raw_ini_contents = dedent(
    """\
    [DEFAULT]
    build_dir = {0}
    distro = sqlite
    database = {0}/sqlite.db

    [original_csv_to_sql]
    exist = sample_in.csv
    shell = dir
    read = sample_in.csv
    write = sample_one

    [sql_to_csv]
    exist = sample_one
    read = sample_one
    write = sample_out.csv

    [csv_back_to_sql]
    read = sample_out.csv
    write = sample_two
    exist =
        sample_one
        sample_two

"""
)

sample = dedent(
    """\
    name,rank,ancestry,height,favorite_number,thing
    "Ironfoundersson, Carrot",Captain,dwarf,78,1,302.4
    "Vimes, Samuel",Commander,human,70,10,2524.535
    "Colon, Fred",Sergeant,human,73,1000000,23.4
    "Nobbs, Nobby",Corporal,unknown,52,42398235025,234.33
    The Librarian,Special Constable,orang-utan,36,0,
    Detritus,Sergeant,troll,90,2,423.4

"""
)


def test_run(tmpdir):
    ini_contents = raw_ini_contents.format(tmpdir)
    sample_csv = Path(tmpdir / "sample_in.csv")
    sample_csv.write_text(sample)
    db = Path(tmpdir / "sqlite.db")
    c = sql.Channel("sqlite", database=db)
    # print(c)

    builder.TaskList(from_string=ini_contents, location=tmpdir).execute()
    # print(sql.execute("select * from sqlite_master;", fetch="df", channel=c))

    sampin = pd.read_csv(Path(tmpdir / "sample_in.csv"))
    t1 = sql.Table("sample_one", channel=c)
    # print(t1.metal)
    # print(ini_contents)
    samp1 = t1.read()
    sampout = pd.read_csv(Path(tmpdir / "sample_out.csv"))
    samp2 = sql.Table("sample_two", channel=c).read()

    results = {
        "sample_in.csv": sampin,
        "sample_one": samp1,
        "sample_out.csv": sampout,
        "sample_two": samp2,
    }

    resultset = set((str(df) for df in results.values()))
    assert len(resultset) == 1
    # pprint((sql.Channel.known_channels, sql.Channel.known_engines))
