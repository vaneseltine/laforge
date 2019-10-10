from pathlib import Path

import laforge as lf
from laforge import sql

SAMPLES = Path("./samples")
OUTPUT = Path("./__output")
OUTPUT.mkdir(exist_ok=True)


@lf.save("channel")
def setup_sql():
    return sql.Channel(distro="sqlite", database="./__testdb.sqlite")


@lf.read("small", SAMPLES / "small.csv")
@lf.read("medium", SAMPLES / "medium.csv")
@lf.save("details")
@lf.save("details2")
def read_in_data(small, medium):
    print("HERE GOEEEESSS MY FUNCTIONNNNN")
    print(f"Wow, the dimensions are {small.shape} and {medium.shape}")
    small.to_csv(OUTPUT / "howdy.csv")
    return str(small.describe())


@lf.exists(OUTPUT / "howdy.csv")
@lf.load("details")
@lf.load("details2")
@lf.save("moo")
def just_a_thing(details, details2):
    print(";".join(details.splitlines()[:3]))
    print(";".join(details2.splitlines()[:3]))
    print("BORING FUNNNCTTIOOONN")
    print("But we still run it. :)")
    _skip_but_can_still_call_internally("oogabooga")
    print(read_in_data)
    return "moo"


@lf.load("moo")
@lf.load("channel")
@lf.read("medium", SAMPLES / "medium.csv")
@lf.save("blah")
def mooooooo(moo, medium, channel):
    print(moo)
    tab = sql.Table("roster")
    print(tab.exists())
    tab.write(medium)
    tab2 = channel.find("%")[0]
    print(tab2)
    # print(tab.exists())
    # sql.execute("drop table schemer.tabula;")
    print(sql.execute("select name, dob from roster;", fetch="tuples"))
    # tab.write(medium)
    # print(repr(tab), repr(tab.channel))
    return "lolol"
    # print(tab.read())


@lf.load("blah")
@lf.exists("tabula")
@lf.write(OUTPUT / "__lol.html")
@lf.read("df2", "sqlite_master")
def sqlitey(blah, df2):
    df = sql.execute("select * from sqlite_master;", fetch="df")
    print(blah)
    print(df == df2)
    return df


def _skip_me_with_exclude_pattern():
    raise RuntimeError


def _skip_but_can_still_call_internally(s):
    print(f"Okay {s}")
