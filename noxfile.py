import nox

# skip_missing_interpreters=True

nox.options.reuse_existing_virtualenvs = True

SUPPORTED_PYTHONS = ("python3.6", "python3.7")


@nox.session(python=SUPPORTED_PYTHONS)
def pytest(session):
    """

    .. note:

    tox required passenv = WINDIR
    See https://www.kidstrythisathome.com/2017/02/tox-pyodbc-and-appveyor.html

    """

    session.install("-r", "dev-requirements.txt")
    session.install("-e", ".")
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
    session.run("python", "-m", "laforge", "--version")
    session.run("laforge", "--version")


@nox.session(python="python3.7")
def sphinx(session):
    session.install("-r", "dev-requirements.txt")
    session.install("-e", ".")
    for target in ["coverage", "html"]:
        session.run(
            "python",
            "-m",
            "sphinx",
            "-E",
            "-b",
            target,
            "/home/matt/projects/laforge/docs",
            f"/home/matt/projects/laforge/docs/_build/{target}",
        )


@nox.session()
def flake8(session):
    session.install("flake8")
    session.run("python", "-m", "flake8", "/home/matt/projects/laforge/laforge")


@nox.session()
def slow(session):
    session.install("-r", "dev-requirements.txt")
    session.install("-e", ".")
    session.run("pytest", "-k", "slow")


@nox.session()
def pylint(session):
    session.install("pylint")
    session.run("pylint", "laforge", "-d", "import-error")


@nox.session()
def mypy(session):
    session.install("mypy")
    session.run("mypy", "--strict", "-p", "laforge", "--ignore-missing-imports")
