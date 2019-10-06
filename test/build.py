from pathlib import Path

import laforge as lf

if __name__ == "__main__":
    lf.build(__file__)


@lf.read("small", Path("./samples/small.csv"))
def read_in_data(small):
    print("HERE GOEEEESSS MY FUNCTIONNNNN")
    print(f"Wow, the dimensions are {small.shape}")
    print(small)


def just_a_thing():
    print("BORING FUNNNCTTIOOONN")
    print("But we still run it. :)")
    _skip_but_use_me_still("oogabooga")


def _skip_me_with_exclude_pattern():
    raise RuntimeError


def _skip_but_use_me_still(s):
    print(f" -- ", f"yes we still say {s}", " --", sep="\n")
