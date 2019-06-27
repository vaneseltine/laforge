import nox

nox.options.reuse_existing_virtualenvs = False

SUPPORTED_PYTHONS = ("python3.6", "python3.7")


@nox.session(python=SUPPORTED_PYTHONS)
def pytest(session):
    """

    Note: tox required passenv = WINDIR
    See https://www.kidstrythisathome.com/2017/02/tox-pyodbc-and-appveyor.html

    """

    session.install("-r", "requirements.txt")
    session.install("-e", ".[all]")
    session.run(
        "pytest",
        "--cov",
        "--cov-config=setup.cfg",
        "--cov-report=html:docs/_static/htmlcov",
        "-k-slow",
    )


@nox.session(python=SUPPORTED_PYTHONS)
def cli(session):
    session.install("-e", ".")
    session.chdir("/")
    session.run("python", "-m", "laforge", "--version", silent=True)
    session.run("laforge", "--version", silent=True)


@nox.session(python="python3.7")
def sphinx(session):
    session.install("-r", "./docs/requirements.txt")
    for target in ["coverage", "html"]:
        session.run(
            "python",
            "-m",
            "sphinx",
            "-E",
            "-b",
            target,
            "./docs",
            f"./docs/_build/{target}",
        )


@nox.session()
def flake8(session):
    session.install("flake8")
    session.run("python", "-m", "flake8", "./laforge", "--show-source")


@nox.session()
def slow(session):
    session.install("-r", "requirements.txt")
    session.install("-e", ".[all]")
    session.run("pytest", "-k", "slow")


@nox.session()
def pylint(session):
    session.install("pylint")
    session.run("pylint", "./laforge", "-d", "import-error", "--reports=yes")


@nox.session()
def black(session):
    session.install("black>=19.3b0")
    session.run("python", "-m", "black", "--target-version", "py36", "./laforge")
