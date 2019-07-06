import subprocess


import pytest

from laforge.command import run_cli  # env, consult, create, build


def test_version(cli_runner):
    result = cli_runner.invoke(run_cli, ["--version"])
    assert result.exit_code == 0
    assert "laforge" in result.output.lower()
    assert "python" in result.output.lower()


def test_build_in_empty_dir_fails(cli_runner):
    with cli_runner.isolated_filesystem():
        result = cli_runner.invoke(run_cli, ["build"])
        assert result.exit_code != 0
        assert result.output


def test_env_works(cli_runner):
    result = cli_runner.invoke(run_cli, ["env", "--no-warning"])
    assert result.exit_code == 0
    assert "LFTEST" in result.output


@pytest.mark.skip
@pytest.mark.parametrize(
    "cmd", ["python -m laforge --version", "python -m laforge env --no-warning"]
)
def test_simple_runs(cmd):
    subprocess.run(cmd, shell=True, check=True)


@pytest.mark.skip
def test_better_env(cmd):
    subprocess.run("python -m laforge env --filter LFTEST", shell=True, check=True)


@pytest.mark.skip
def test_build():
    build()


@pytest.mark.skip
def test_consult():
    consult()


@pytest.mark.skip
def test_create():
    create()
