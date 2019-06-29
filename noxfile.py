from pathlib import Path
from shutil import rmtree

import nox

# -r to ovveride and reuse them instead
nox.options.reuse_existing_virtualenvs = False

SUPPORTED_PYTHONS = ("python3.6", "python3.7")


def clean_dir(s):
    folder = Path(s)
    if folder.exists():
        rmtree(folder, ignore_errors=True)


@nox.session(python=SUPPORTED_PYTHONS)
def pytest(session):
    """

    Note: tox required passenv = WINDIR
    See https://www.kidstrythisathome.com/2017/02/tox-pyodbc-and-appveyor.html

    """
    session.install("-r", "requirements.txt")
    session.install("-e", ".[all]")
    clean_dir("./build/coverage")
    session.run(
        "pytest",
        "--cov",
        "--cov-config=setup.cfg",
        "--cov-report=html:build/coverage",
        "-k-slow",
    )


@nox.session(python=SUPPORTED_PYTHONS)
def cli(session):
    session.install("-e", ".")
    session.chdir("/")
    session.run("python", "-m", "laforge", "--version", silent=True)
    session.run("laforge", "--version", silent=True)
    session.run("laforge", "env", "--no-warning", silent=True)


@nox.session()
def slow(session):
    session.install("-r", "requirements.txt")
    session.install("-e", ".[all]")
    session.run("pytest", "-k", "slow")


@nox.session(reuse_venv=True)
def doc8(session):
    session.install("-U", "doc8", "Pygments")
    session.run("doc8", "./docs")


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
