from pathlib import Path
from textwrap import dedent

import pytest

from laforge.builder import Target, Task, Verb


class TestTask:
    @pytest.mark.win32
    def t_shell(self,):
        task = Task.from_strings(
            raw_verb="shell",
            raw_content="dir",
            config={"dir": {Verb.SHELL: Path(".").absolute()}},
        )
        # print(task)
        task.implement()

    def t_fail_verb(self,):
        with pytest.raises(ValueError):
            _ = Task.from_strings(
                raw_verb="meow", raw_content=None, config={"section": "--"}
            )

    def t_fail_parse(self,):
        with pytest.raises(RuntimeError):
            _ = Task.from_strings(
                raw_verb="write", raw_content="meow.json", config={"section": "--"}
            )

    @pytest.mark.parametrize("suffix", [Target.CSV])
    def t_csv_do_not_parse_null_values(self, give_me_path, task_config):
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

    @pytest.mark.parametrize(
        "suffix", [Target.CSV, Target.DTA, Target.HTML, Target.XLSX]
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
