from pathlib import Path

import laforge as lf


@lf.read("small", "small.csv")
@lf.save("smallsaved")
def read_in_data(small):
    small.to_csv("small_out.csv", index=False)
