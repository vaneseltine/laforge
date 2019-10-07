from pathlib import Path

import laforge as lf

if __name__ == "__main__":
    lf.build()

SAMPLES = Path("./samples")
OUTPUT = Path("./__output")
OUTPUT.mkdir(exist_ok=True)


@lf.save("details")
@lf.save("details2")
@lf.read("small", SAMPLES / "small.csv")
@lf.read("medium", SAMPLES / "medium.csv")
def read_in_data(small, medium):
    print("HERE GOEEEESSS MY FUNCTIONNNNN")
    print(f"Wow, the dimensions are {small.shape} and {medium.shape}")
    # print(small)
    small.to_csv(OUTPUT / "howdy.csv")
    return str(small.describe())


@lf.read("howdy", OUTPUT / "howdy.csv")
@lf.load("details")
def just_a_thing(howdy, details):
    print(howdy.shape)
    print(";".join(details.splitlines()))
    print("BORING FUNNNCTTIOOONN")
    print("But we still run it. :)")
    _skip_but_can_still_call_internally("oogabooga")


def _skip_me_with_exclude_pattern():
    raise RuntimeError


def _skip_but_can_still_call_internally(s):
    print(f"Okay {s}")
