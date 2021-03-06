from pathlib import Path
from textwrap import dedent

import pandas as pd
import pytest

from laforge.builder import (
    FileReader,
    FileWriter,
    SQLExecutor,
    SQLQueryReader,
    SQLReaderWriter,
    Target,
    Task,
    TaskExecutionError,
    Verb,
)


class TestTarget:
    @pytest.mark.parametrize("verb", [Verb.READ, Verb.EXECUTE, Verb.EXIST])
    @pytest.mark.parametrize(
        "raw", ["select 1 from engineering;", "select\n    1,\n    2\nfrom engineering"]
    )
    def t_parse_raw_query_by_content_features(self, verb, raw):
        assert Target.parse(raw) == Target.RAWQUERY

    @pytest.mark.parametrize("verb", [Verb.READ, Verb.WRITE, Verb.EXIST])
    @pytest.mark.parametrize("raw", ["crew_manifest", "engineering.crew_manifest"])
    def t_parse_sql_table_by_content_features(self, verb, raw):
        assert Target.parse(raw) == Target.SQLTABLE


class TestTaskList:
    @pytest.mark.xfail(reason="Test to be implemented")
    def t_skip_unknown_key_in_section(self):
        # should make use of is_verb == False
        assert False

    @pytest.mark.xfail(reason="Test to be implemented")
    def t_start_and_stop(self, caplog):
        caplog.set_level(1)
        assert "warning" in caplog.text.lower()

    @pytest.mark.xfail(reason="Test to be implemented")
    def t_start_without_stop(self, caplog):
        caplog.set_level(1)
        assert "warning" in caplog.text.lower()

    @pytest.mark.xfail(reason="Test to be implemented")
    def t_stop_without_start(self, caplog):
        caplog.set_level(1)
        assert "warning" in caplog.text.lower()

    # @pytest.mark.xfail(reason="Test to be implemented")
    # def t_dry_run(self):
    #     assert False

    @pytest.mark.xfail(reason="Test to be implemented")
    def t_skip_when_no_content_following_key(self):
        assert False

    @pytest.mark.xfail(reason="Test to be implemented")
    def t_debug_mode(self):
        assert False

    @pytest.mark.xfail(reason="Test to be implemented")
    def t_pass_results_from_prior_to_next(self):
        assert False

    @pytest.mark.xfail(reason="Test to be implemented")
    def t_full_test(self):
        assert False


class TestTask:
    def t_basics(self):
        t = Task.from_strings(
            raw_verb="read",
            raw_content="select * from transporter_pads;",
            config={"section": "--"},
        )
        assert "read" in str(t).lower()
        assert "read" in repr(t).lower()

    def t_fail_verb(self):
        with pytest.raises(ValueError):
            _ = Task.from_strings(
                raw_verb="meow", raw_content=None, config={"section": "--"}
            )

    def t_fail_parse(self):
        with pytest.raises(RuntimeError):
            _ = Task.from_strings(
                raw_verb="write", raw_content="meow.json", config={"section": "--"}
            )


class TestFileReader:
    @pytest.mark.parametrize("suffix", [Target.CSV, Target.XLSX, Target.XLS])
    def t_read_csv(self, give_me_path, medium_df, task_config, suffix):
        outfile = give_me_path(str(suffix).lower())
        if suffix == Target.CSV:
            medium_df.to_csv(outfile)
        elif suffix == Target.XLSX:
            medium_df.to_excel(outfile, engine="xlsxwriter")
        elif suffix == Target.XLS:
            medium_df.to_excel(outfile, engine="xlsxwriter")
        else:
            raise NotImplementedError(suffix)
        t = Task.from_strings(
            raw_verb="read", raw_content=str(outfile), config=task_config
        )
        assert len(medium_df) == len(t.implement())

    @pytest.mark.parametrize("suffix", [Target.CSV])
    def t_read_csv_do_not_assume_null_values_from_text(self, give_me_path, task_config):
        arbitrarycsvfile = give_me_path("csv")
        arbitrarycsvfile.write_text(
            dedent(
                """\
                a,b,c
                Null,3.1415,0
                null,3,1
                yolo,0,2
                NA,3,3
                NaN,9.3,4
                NAN,,5
                """
            )
        )
        reader = Task.from_strings(
            raw_verb="read", raw_content=str(arbitrarycsvfile), config=task_config
        )
        df = reader.implement()
        assert (
            not df["a"].isnull().values.any()
        ), "NA, null, NaN should not produce missing values."
        assert df["b"].isnull().values.any(), "Only blank is missing."
        assert "float" in str(df["b"].dtype)


class TestFileWriter:
    @pytest.mark.parametrize(
        "suffix", [Target.CSV, Target.HTML, Target.XLS, Target.XLSX]
    )
    def t_write_creates_specified_file(
        self, task_config, minimal_df, random_filename, suffix
    ):
        # The random_filename fixture automagically receives suffix
        final_path = Path(task_config["write_dir"], random_filename)
        assert suffix.value in str(final_path)
        writer = Task.from_strings(
            raw_verb="write", raw_content=str(random_filename), config=task_config
        )
        try:
            writer.implement(minimal_df)
        except UnicodeEncodeError:
            pytest.skip("Broken on sr.ht...")
        else:
            assert final_path.exists()

    def t_write_actually_writes_correct_values(self, minimal_df, tmpdir, task_config):
        outfile = Path(tmpdir) / "out.csv"
        writer = Task.from_strings(
            raw_verb="write", raw_content=str(outfile), config=task_config
        )
        writer.implement(minimal_df)
        diff = pd.read_csv(outfile) == minimal_df
        assert diff.all().all()

    def t_writing_empty_df_gives_warning(self, tmpdir, task_config, caplog):
        outfile = Path(tmpdir) / "out.csv"
        writer = Task.from_strings(
            raw_verb="write", raw_content=str(outfile), config=task_config
        )
        writer.implement(pd.DataFrame([]))
        caplog.set_level(1)
        assert "warning" in caplog.text.lower()

    @pytest.mark.xfail(reason="Test to be implemented")
    def t_writing_to_locked_file_gives_time_to_free(self):
        assert False

    def t_write_without_any_results_fails(self, tmpdir, task_config, caplog):
        outfile = Path(tmpdir) / "out.csv"
        writer = Task.from_strings(
            raw_verb="write", raw_content=str(outfile), config=task_config
        )
        with pytest.raises(TaskExecutionError):
            writer.implement(prior_results=None)


class TestExistenceChecker:
    def t_file_fail(self, tmpdir, task_config):
        outfile = Path(tmpdir) / "nonexistent.csv"
        task = Task.from_strings(
            raw_verb="exist", raw_content=str(outfile), config=task_config
        )
        with pytest.raises(FileNotFoundError):
            task.implement()

    def t_file_pass(self, tmpdir, task_config):
        outfile = Path(tmpdir) / "existent.csv"
        outfile.write_text("Engage")
        task = Task.from_strings(
            raw_verb="exist", raw_content=str(outfile), config=task_config
        )
        task.implement()

    @pytest.mark.xfail(reason="Test to be implemented")
    def t_table_fail(self):
        assert False

    @pytest.mark.xfail(reason="Test to be implemented")
    def t_table_pass(self):
        assert False

    @pytest.mark.xfail(reason="Test to be implemented")
    def t_result_of_query_fail(self):
        assert False

    @pytest.mark.xfail(reason="Test to be implemented")
    def t_result_of_query_pass(self):
        assert False


class TestSQLReaderWriter:
    @pytest.mark.xfail(reason="Test to be implemented")
    def t_write(self):
        assert False

    @pytest.mark.xfail(reason="Test to be implemented")
    def t_read(self):
        assert False

    @pytest.mark.xfail(reason="Test to be implemented")
    def t_write_without_results_fails(self):
        assert False


class TestEchoer:
    @pytest.mark.xfail(reason="Test to be implemented")
    def t_echo(self):
        assert False


class TestInternalPythonExecutor:
    @pytest.mark.xfail(reason="Test to be implemented")
    def t_execute(self):
        assert False
