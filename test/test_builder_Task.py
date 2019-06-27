import pytest
from laforge.builder import Task, Target, Verb
from pathlib import Path

from textwrap import dedent


@pytest.mark.win32
def test_shell():
    task = Task.from_strings(
        raw_verb="shell",
        raw_content="dir",
        config={"dir": {Verb.SHELL: Path(".").absolute()}},
    )
    print(task)
    task.implement()


def test_fail_verb():
    with pytest.raises(ValueError):
        _ = Task.from_strings(
            raw_verb="meow", raw_content=None, config={"section": "--"}
        )


def test_fail_parse():
    with pytest.raises(RuntimeError):
        _ = Task.from_strings(
            raw_verb="write", raw_content="meow.json", config={"section": "--"}
        )


@pytest.mark.parametrize("suffix", [Target.CSV])
def test_csv_do_not_parse_null_values(give_me_path, task_config):
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


@pytest.mark.parametrize("suffix", [Target.CSV, Target.DTA, Target.HTML, Target.XLSX])
def test_write_creates_specified_file(
    task_config, prior_results, random_filename, suffix
):
    # the random_filename fixture automagically receives suffix
    # it's pretty cool
    final_path = Path(task_config["write_dir"], random_filename)
    assert suffix.value in str(final_path)
    writer = Task.from_strings(
        raw_verb="write", raw_content=str(random_filename), config=task_config
    )
    try:
        writer.implement(prior_results)
    except UnicodeEncodeError:
        pytest.skip("Broken on sr.ht...")
    else:
        assert final_path.exists()
