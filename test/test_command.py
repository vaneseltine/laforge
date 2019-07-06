import subprocess

import pytest

from laforge.command import env, consult, create, build


@pytest.mark.parametrize(
    "cmd", ["python -m laforge --version", "python -m laforge env --no-warning"]
)
def test_simple_runs(cmd):
    subprocess.run(cmd, shell=True, check=True)


@pytest.mark.xfail
def test_better_env(cmd):
    subprocess.run("python -m laforge env --filter LFTEST", shell=True, check=True)


@pytest.mark.xfail
def test_env():
    env()


@pytest.mark.xfail
def test_build():
    build()


@pytest.mark.xfail
def test_consult():
    consult()


@pytest.mark.xfail
def test_create():
    create()


@pytest.mark.xfail
def test_env():
    env()
