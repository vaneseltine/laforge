from pathlib import Path

from laforge import sql


class TestServer:
    def test_init(self):
        server = sql.Server("TESTMSSQLSERVER")
        assert server

    def test_name_saved(self):
        server = sql.Server("TESTMSSQLSERVER")
        assert server.name == "TESTMSSQLSERVER"

    def test_repr(self):
        server = sql.Server("TESTMSSQLSERVER")
        assert repr(server) == "Server('TESTMSSQLSERVER')"

    def test_str(self):
        server = sql.Server("TESTMSSQLSERVER")
        assert str(server) == "TESTMSSQLSERVER"


class TestDatabase:
    def test_init(self):
        server = sql.Server("TESTMSSQLSERVER")
        db = server.TESTmain
        assert db.name == "TESTmain"

    def test_repr(self):
        server = sql.Server("TESTMSSQLSERVER")
        db = server.TESTmain
        assert repr(db) == "Database('TESTmain', Server('TESTMSSQLSERVER'))"

    def test_str(self):
        server = sql.Server("TESTMSSQLSERVER")
        db = server.TESTmain
        assert str(db) == "TESTMSSQLSERVER.TESTmain"


class TestSchema:
    def test_init(self):
        server = sql.Server("TESTMSSQLSERVER")
        database = server.TESTmain
        schema = database.schemaname
        assert schema.name == "schemaname"

    def test_repr(self):
        server = sql.Server("TESTMSSQLSERVER")
        database = server.TESTmain
        schema = database.schemaname
        assert repr(schema) == "Schema('schemaname')"

    def test_str(self):
        server = sql.Server("TESTMSSQLSERVER")
        database = server.TESTmain
        schema = database.schemaname
        assert str(schema) == "TESTMSSQLSERVER.TESTmain.schemaname"


# TEST_DIR = Path(__file__).parent
# BUILD_DIR = TEST_DIR / "buildfiles"
# DATA_DIR = TEST_DIR / "data"
# SMALL = DATA_DIR / "small.csv"


# class TestBuildFiles:
#     def test_csvs(self, make_temp, equal_csvs):
#         buildfile = make_temp(BUILD_DIR / "csvs.py", SMALL)
#         build(buildfile)
#         assert equal_csvs(SMALL, buildfile.parent / "small_out.csv")


# class TestCommandLine:

#     KEYWORDS = BUILD_DIR / "keywords.py"

#     def test_keywords_include(self):
#         build(buildfile=self.KEYWORDS, include="good")

#     def test_keywords_exclude(self):
#         build(buildfile=self.KEYWORDS, exclude="bad")

#     def test_keywords_avoid_underscored(self):
#         build(buildfile=self.KEYWORDS, include="never")
