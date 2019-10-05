from pathlib import Path

import laforge.decoupage as lf


@lf.read("small", Path("../samples/small.csv"))
def read_in_data(small):
    print("HERE GOEEEESSS MY FUNCTIONNNNN")
    # print(small.describe())
    print(f"Wow, the dimensions are {small.shape}")


def just_a_thing():
    print("BORING FUNNNCTTIOOONN")
    print("But we still run it. :)")


def _skip_me_with_exclude_pattern():
    raise RuntimeError
