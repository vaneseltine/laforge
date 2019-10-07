from pathlib import Path

import laforge as lf
from laforge import sql

CHANNEL = sql.Channel(
    distro="postgresql",
    username="postgres",
    password="postgres",
    server="localhost",
    database="tester",
    schema="schemer",
)

SAMPLES = Path("./samples")
OUTPUT = Path("./__output")
OUTPUT.mkdir(exist_ok=True)


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
    return "moo"


@lf.load("moo")
@lf.read("medium", SAMPLES / "medium.csv")
def mooooooo(moo, medium):
    print(moo)
    tab = sql.Table("schemer.tabula")
    print(tab.read())
    x = sql.execute("select count(*) from information_schema.columns;", fetch="tuples")
    tab2 = CHANNEL.find("%")[0]
    print(tab == tab2)
    print(x)
    print(tab.exists())
    # sql.execute("drop table schemer.tabula;")
    # tab.read()
    tab.write(medium)
    print(repr(tab), repr(tab.channel))
    # print(tab.read())


def _skip_me_with_exclude_pattern():
    raise RuntimeError


def _skip_but_can_still_call_internally(s):
    print(f"Okay {s}")
