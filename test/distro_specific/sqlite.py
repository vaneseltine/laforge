import pytest
from laforge.sql import Channel, Table, Script, execute
from laforge.distros import Distro

import pandas as pd

df = pd.DataFrame([1, 2, 3, 4, 5], columns=["a"])

cm = Channel(distro="sqlite", database=":memory:")
cf = Channel(distro="sqlite", database="./__test_sqlite.db")

tm = Table("himem", channel=cm)
tf = Table("hifile", channel=cf)
