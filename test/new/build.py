from pathlib import Path

import laforge.decoupage as lf


@lf.read("small", Path("../samples/small.csv"))
def read_in_data(small):
    print("HERE GOEEEESSS MY FUNCTIONNNNN")
    print("HERE GOEEEESSS MY FUNCTIONNNNN")
    print("HERE GOEEEESSS MY FUNCTIONNNNN")
    print(small)


def just_a_thing():
    print("BORING FUNNNCTTIOOONN")
