"""
cf. https://github.com/saltstack/salt/blob
    /328989d6cc8f81fc100c9aa900a4e3613dc7c19d/noxfile.py

example selection from .env:

    LFTEST_MSSQL = 0

    LFTEST_SQLITE = 1
    LFTEST_SQLITE_DATABASE = :memory:

    LFTEST_MYSQL = 1
    LFTEST_MYSQL_SERVER = localhost
    LFTEST_MYSQL_DATABASE = test_mason
    LFTEST_MYSQL_SCHEMA = test_mason
    LFTEST_MYSQL_USERNAME = test_mason
    LFTEST_MYSQL_PASSWORD = test_mason

    LFTEST_POSTGRESQL = 1
    LFTEST_POSTGRESQL_SERVER = localhost
    LFTEST_POSTGRESQL_DATABASE = test_mason
    LFTEST_POSTGRESQL_SCHEMA = test_mason
    LFTEST_POSTGRESQL_USERNAME = test_mason
    LFTEST_POSTGRESQL_PASSWORD = test_mason

"""

import os
import sys
from pathlib import Path
from shutil import rmtree

import dotenv
import nox

# -r at the command line to ovveride and reuse all instead
nox.options.reuse_existing_virtualenvs = False

SUPPORTED_PYTHONS = ("python3.6", "python3.7")
DISTROS = ["mysql", "mssql", "postgresql", "sqlite"]

# Pull variables, especially LFTEST_*, into os.environ
dotenv.load_dotenv(dotenv.find_dotenv())


def get_machine_distros(distros):
    supported = [d for d in distros if os.environ.get(f"LFTEST_{d.upper()}") == "1"]
    return supported or ["sqlite"]


def clean_dir(s):
    folder = Path(s)
    if folder.exists():
        rmtree(folder, ignore_errors=True)


@nox.session(python=SUPPORTED_PYTHONS)
def pytest_pyv(session):
    """
    Note: tox required passenv = WINDIR
    See https://www.kidstrythisathome.com/2017/02/tox-pyodbc-and-appveyor.html
    """
    session.install("-r", "requirements.txt")
    session.install("-e", ".[all]")
    session.run("coverage", "run", "--parallel-mode", "-m", "pytest")


@nox.session()
@nox.parametrize("distro", get_machine_distros(DISTROS))
def pytest_db(session, distro):
    session.install("-r", "requirements.txt")
    session.install("-e", f".[{distro}]")
    session.run(
        "coverage",
        "run",
        "--parallel-mode",
        "-m",
        "pytest",
        env={"LFTEST_DISTRO": distro},
    )


@nox.session()
def coverage(session):
    clean_dir("./build/coverage")
    session.install("coverage", "coveralls")
    session.run("coverage", "combine")
    session.run("coverage", "report")
    session.run("coverage", "html")
    session.run("coveralls")


@nox.session(python=SUPPORTED_PYTHONS)
def cli(session):
    session.install("-e", ".")
    session.chdir("/")
    session.run("python", "-m", "laforge", "--version", silent=True)
    session.run("laforge", "--version", silent=True)
    session.run("laforge", "env", "--no-warning", silent=True)


@nox.session(reuse_venv=True)
def doc8(session):
    session.install("-U", "doc8", "Pygments")
    session.run("doc8", "./docs", "-q")


@nox.session()
def sphinx(session):
    # Treat warnings as errors.
    session.env["SPHINXOPTS"] = "-W"
    session.install("-e", ".")
    session.install("-r", "./docs/requirements.txt")
    clean_dir("./build/sphinx")
    session.run("python", "-m", "sphinx", "-b", "coverage", "./docs", "./docs/_static")
    session.run("python", "setup.py", "build_sphinx", "-b", "html", "-W")


@nox.session(reuse_venv=True)
def flake8(session):
    session.install("-U", "flake8")
    session.run("python", "-m", "flake8", "./laforge", "--show-source")


@nox.session(reuse_venv=True)
def pylint(session):
    session.install("-U", "pylint")
    session.run("pylint", "./laforge", "-d", "import-error")


@nox.session(reuse_venv=True)
def black(session):
    session.install("-U", "black")
    session.run("python", "-m", "black", "--target-version", "py36", ".")


if __name__ == "__main__":
    sys.stderr.write(f"Invoke {__file__} by running Nox.")
    exit(1)
