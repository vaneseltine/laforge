"""Run via nox

For .env setup, see .circleci/env"""

import os
import sys
from pathlib import Path
from shutil import rmtree

import dotenv
import nox

# -r on CLI to override and reuse all instead
nox.options.reuse_existing_virtualenvs = False
# --no-stop-on-first-error on CLI to override
nox.options.stop_on_first_error = True

SUPPORTED_PYTHONS = ("python3.6", "python3.7")  # , "python3.8")
WINDOWS = sys.platform.startswith("win")

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
def test_version(session):
    session.install("-r", "requirements.txt")
    session.install("-e", ".[excel]")
    session.run(
        "coverage",
        "run",
        "--parallel-mode",
        "-m",
        "pytest",
        "-rxXs",
        env={
            "LFTEST_DISTRO": "sqlite",
            "LFTEST_SQLITE": "1",
            "LFTEST_SQLITE_DATABASE": ":memory:",
        },
    )


@nox.session(python=SUPPORTED_PYTHONS)
def cli(session):
    session.install("-e", ".")
    session.chdir("/")
    session.run("laforge", "--version", silent=True)


@nox.session(python=False)
def coverage(session):
    clean_dir("./build/coverage")
    if len(list(Path(".").glob(".coverage*"))) > 1:
        try:
            Path(".coverage").unlink()
        except FileNotFoundError:
            pass
        session.run("coverage", "combine")
    session.run("coverage", "report")
    session.run("coverage", "html")


@nox.session(python=False)
def coveralls(session):
    if not os.getenv("COVERALLS_REPO_TOKEN"):
        session.skip()
    session.run("coveralls")


@nox.session(python=False)
def lint_docs(session):
    if WINDOWS:
        session.run("doc8", "./docs", "-q", "--ignore=D002", "--ignore=D004")
    else:
        session.run("doc8", "./docs", "-q")


@nox.session(python=False)
def lint_flake8(session):
    session.run("python", "-m", "flake8", "./laforge", "--show-source")


@nox.session(python=False)
def lint_pylint(session):
    session.run("pylint", "./laforge", "-d", "import-error", "--score=n")


@nox.session(python=False)
def lint_black(session):
    session.run("python", "-m", "black", "--target-version", "py36", "-q", ".")


if __name__ == "__main__":
    sys.stderr.write(f"Invoke {__file__} by running Nox.")
    sys.exit(1)
