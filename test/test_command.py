from pathlib import Path

import pytest

from laforge.command import run_cli


class TestEnv:
    def t_env_works_with_flag(self, cli_runner):
        with cli_runner.isolated_filesystem():
            result = cli_runner.invoke(run_cli, ["env", "--no-warning"])
            assert result.exit_code == 0
            assert "sql" in result.output.lower()

    def t_env_works_with_Y_to_warning(self, cli_runner):
        result = cli_runner.invoke(run_cli, ["env"], input="Y\n")
        assert result.exit_code == 0
        assert "sql" in result.output.lower()

    def t_env_cancels_with_N_to_warning(self, cli_runner):
        result = cli_runner.invoke(run_cli, ["env"], input="N\n")
        assert result.exit_code == 0
        assert "sql" not in result.output.lower()

    @pytest.mark.xfail
    def t_env_works_on_remote(self, cli_runner, tmpdir):
        env_file = Path(tmpdir, ".env")
        env_file.write_text("hi: there")
        with cli_runner.isolated_filesystem():
            result = cli_runner.invoke(
                run_cli, ["env", "--no-warning", str(env_file.parent.resolve())]
            )
            # assert result.exit_code == 0
            assert "sql" in result.output.lower()
            print(result.output)
            assert False


class TestCreateINI:
    @pytest.mark.xfail
    def t_does_something(self, cli_runner, caplog, capsys):
        with cli_runner.isolated_filesystem():
            result = cli_runner.invoke(run_cli, ["create"])
            captured = capsys.readouterr()
        assert result.output == ""
        assert captured.out
        assert not captured.err
        assert result.exit_code == 0

    @pytest.mark.xfail
    def t_does_something2(self, cli_runner, caplog, capsys):
        with cli_runner.isolated_filesystem():
            result = cli_runner.invoke(run_cli, ["create", "build.ini"])
            captured = capsys.readouterr()
        assert result.output == ""
        assert captured.out
        assert not captured.err
        assert result.exit_code == 0

    @pytest.mark.xfail
    def t_does_something3(self, cli_runner, caplog, capsys):
        with cli_runner.isolated_filesystem():
            Path("build.ini").write_text("conflicting file")
            result = cli_runner.invoke(run_cli, ["create", "build.ini"])
            captured = capsys.readouterr()
        assert result.output == ""
        assert not captured.out
        assert captured.err
        assert result.exit_code != 0


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
    """'{filename} launched' is a good marker of succcess"""

    @pytest.mark.parametrize("debug", [False, True])
    @pytest.mark.parametrize("specify_filename", [True, False])
    @pytest.mark.parametrize("filename", ["build.ini", "build1.ini", "laforge.ini"])
    def t_build_here(
        self, cli_runner, caplog, specify_filename, barebones_build, debug, filename
    ):
        with cli_runner.isolated_filesystem():
            Path(filename).write_text(barebones_build)
            args = ["build"]
            if debug:
                args.append("--debug")
            if specify_filename:
                args.append(filename)
            print(args)
            cli_runner.invoke(run_cli, args)
        assert f"{filename} launched" in caplog.text
        if debug:
            assert "debug mode" in caplog.text.lower()

    @pytest.mark.parametrize("specify_filename", [True, False])
    @pytest.mark.parametrize("filename", ["build.ini", "build1.ini", "laforge.ini"])
    def t_build_elsewhere(
        self, cli_runner, specify_filename, barebones_build, filename, tmpdir, caplog
    ):
        ini = Path(tmpdir, filename).resolve()
        ini.write_text(barebones_build)
        with cli_runner.isolated_filesystem():
            target = str(ini) if specify_filename else str(ini.parent)
            cli_runner.invoke(run_cli, ["build", target])
            assert f"{filename} launched" in caplog.text

    @pytest.mark.parametrize("filenames", [[], ["build1.ini", "laforge.ini"]])
    def t_try_dir_fails_when_empty_or_too_many(
        self, cli_runner, barebones_build, filenames, caplog
    ):
        with cli_runner.isolated_filesystem():
            for f in filenames:
                Path(f).write_text(barebones_build)
            result = cli_runner.invoke(run_cli, ["build"])
            assert result.exit_code != 0
            assert "launched" not in result.output
            assert "launched" not in caplog.text

    def t_dry_run(self, cli_runner, barebones_build, caplog):
        with cli_runner.isolated_filesystem():
            Path("build.ini").write_text(barebones_build)
            result = cli_runner.invoke(run_cli, ["build", "--dry-run"])
            assert result.exit_code == 0
            assert "info" in caplog.text.lower()
            assert "complete" not in result.output
            assert "complete" not in caplog.text


class TestConsult:
    def t_prints_single_line(self, cli_runner):
        result = cli_runner.invoke(run_cli, ["consult"])
        assert len(result.output.splitlines()) == 1

    @pytest.mark.parametrize("term", ["a", "j", "x", "v"])
    def t_prints_match(self, cli_runner, term):
        result = cli_runner.invoke(run_cli, ["consult", "--match", term])
        assert term in result.output.lower()

    @pytest.mark.parametrize("term", ["xyzzy", "aviaeur"])
    def t_does_not_crash_on_bad_match(self, cli_runner, term):
        result = cli_runner.invoke(run_cli, ["consult", "--match", term])
        assert term not in result.output.lower()
