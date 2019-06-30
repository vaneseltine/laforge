import logging
import os
import sys
from pathlib import Path

logger = logging.getLogger("__name__")


PACKAGE_NAME = "laforge"

FIRST_LINE = "# Automatically created by {}\n.".format(PACKAGE_NAME)

choices = []
if sys.platform.startswith("win"):
    choices.append(os.environ.get("APPDATA"))
    choices.append(os.environ.get("XDG_CONFIG_HOME"))
    choices.append(os.environ.get("USERPROFILE"))
    subfolder = PACKAGE_NAME.capitalize()
elif sys.platform.startswith("linux"):
    choices.append(os.environ.get("XDG_CONFIG_HOME"))
    subfolder = PACKAGE_NAME.lower()
else:
    raise NotImplementedError(sys.platform)
choices.append(str(Path.home() / ".config"))

first_valid_folder = next(x for x in choices if x)
logger.debug(first_valid_folder)

CFG_DIR = Path(first_valid_folder) / subfolder
CFG = Path(CFG_DIR / PACKAGE_NAME.lower()).with_suffix(".ini")

logger.debug(CFG_DIR)


def test_creation():
    if not CFG_DIR.exists():
        CFG_DIR.mkdir(parents=True)

    if CFG.exists():
        assert CFG.read_text()
    else:
        CFG.write_text(FIRST_LINE)
        assert CFG.read_text() == FIRST_LINE
