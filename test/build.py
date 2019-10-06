from pathlib import Path

import laforge as lf

if __name__ == "__main__":
    lf.build()

SAMPLES = Path("./samples")
OUTPUT = Path("./__output")


@lf.read("small", SAMPLES / "small.csv")
def read_in_data(small):
    print("HERE GOEEEESSS MY FUNCTIONNNNN")
    print(f"Wow, the dimensions are {small.shape}")
    print(small)


@lf.exist(SAMPLES / "smafll.csv")
def just_a_thing():
    # print(read_in_data.small.shape)
    print("BORING FUNNNCTTIOOONN")
    print("But we still run it. :)")
    _skip_but_use_me_still("oogabooga")


def _skip_me_with_exclude_pattern():
    raise RuntimeError


def _skip_but_use_me_still(s):
    print(f" -- ", f"yes we still say {s}", " --", sep="\n")
