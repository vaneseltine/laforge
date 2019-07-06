import pytest

from laforge.command import run_cli  # env, consult, create, build

## version


class TestBasicCLI:
    def t_version(self, cli_runner):
        result = cli_runner.invoke(run_cli, ["--version"])
        assert result.exit_code == 0
        assert "laforge" in result.output.lower()
        assert "python" in result.output.lower()

    @pytest.mark.parametrize("additions", ["-h", "--help"])
    def t_explicit_help(self, cli_runner, additions):
        result = cli_runner.invoke(run_cli, additions)
        assert result.exit_code == 0
        for command in ("build", "env", "create"):
            assert command in result.output

    def t_implicit_help(self, cli_runner):
        result = cli_runner.invoke(run_cli)
        assert result.exit_code == 0
        for command in ("build", "env", "create"):
            assert command in result.output


class TestBuild:
    def t_empty_dir_fails(self, cli_runner):
        with cli_runner.isolated_filesystem():
            result = cli_runner.invoke(run_cli, ["build"])
            assert result.exit_code != 0
            assert result.output


class TestEnv:
    def t_env_works_with_flag(self, cli_runner):
        result = cli_runner.invoke(run_cli, ["env", "--no-warning"])
        assert result.exit_code == 0
        assert "LFTEST" in result.output

    def t_env_works_with_Y_to_warning(self, cli_runner):
        result = cli_runner.invoke(run_cli, ["env"], input="Y\n")
        assert result.exit_code == 0
        assert "LFTEST" in result.output

    def t_env_cancels_with_N_to_warning(self, cli_runner):
        result = cli_runner.invoke(run_cli, ["env"], input="N\n")
        assert result.exit_code == 0
        assert "LFTEST" not in result.output
