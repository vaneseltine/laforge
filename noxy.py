import nox

DEPS = {
    "core": [],
    "all": [
        "coverage",
        "hypothesis",
        "openpyxl",
        "pandas",
        "psycopg2",
        "PyInquirer",
        "pymysql",
        "pyodbc",
        "pyparsing",
        "pytest",
        "pytest-cov",
        "SQLAlchemy",
    ],
}


def make_cmd(*various):
    return " ".join(various).split()


@nox.session
def pytest(session):
    # session.install(*DEPS["all"])
    session.install("-r dev-requirements.txt")
    cmd = make_cmd(
        "pytest",
        "--cov --cov-config=tox.ini --cov-report=html:docs/_static/htmlcov",
        "-k-slow",
    )
    session.run(*cmd)


@nox.session
def flake8(session):
    session.install("flake8")
    session.run("flake8", "laforge")


@nox.session
def pylint(session):
    session.install("pylint")
    cmd = make_cmd(
        "pylint ./laforge",
        "-d missing-docstring",
        "-d empty-docstring",
        "-d fixme",
        "-d import-error",
    )
    session.run(*cmd)
