import random
import re
from copy import deepcopy
from pathlib import Path

INPUTS_FILENAME = "tech_inputs.txt"


def nobabble(n=1, match=""):
    for _ in range(n):
        if match:
            babble = Technobabbler.find_babble(match)
        else:
            babble = Technobabbler().babble()
        print(babble)


class ModifiableVerb:
    def __init__(self, verb_info):
        self.root, self.s_present, self.s_past, self.s_gerund, *prefixes = verb_info
        self.prefix = random.choice(prefixes)

    @property
    def present(self):
        return self.prefix + self.root + self.s_present

    @property
    def past(self):
        return self.prefix + self.root + self.s_past

    @property
    def gerund(self):
        return self.prefix + self.root + self.s_gerund


class Technobabbler:

    raw_inputs = (Path(__file__).parent / INPUTS_FILENAME).read_text()
    _content = {}
    for line in raw_inputs.splitlines():
        if not line:
            continue
        line = line.strip()
        if line.startswith("[") and line.endswith("]"):
            key = line[1:-1]
            _content[key] = []
            continue
        _content[key].append(line)

    def __init__(self):
        self.content = deepcopy(self._content)
        for key in self.content:
            random.shuffle(self.content[key])

    def babble(self):
        completed_babble = self.generate("statement")
        return capitalize_sentences(completed_babble)

    @classmethod
    def find_babble(cls, match, tries=1000):
        for _ in range(tries):
            attempt = cls().babble()
            if re.search(match, attempt, flags=re.IGNORECASE):
                return attempt
        return cls().generate("apology")

    def generate(self, item):
        if item.startswith("verb_"):
            verb_info = self.content["verb"].pop().split(",")
            verb = ModifiableVerb(verb_info)
            result = getattr(verb, item[5:])
        else:
            result = (
                self.content[item].pop()
                if len(self.content[item]) > 1
                else self.content[item][0]
            )
        result = result.format_map(self)
        return result

    def __getitem__(self, item):
        return self.generate(item)


def capitalize_sentences(phrase):
    return "".join(make_first_upper(x) for x in re.split("([!?.] )", phrase))


def make_first_upper(s):
    """Uppercase the first letter of s, leaving the rest alone."""
    return s[:1].upper() + s[1:]


"""
Copyright 2019 Matt VanEseltine.

This file is part of laforge.

laforge is free software: you can redistribute it and/or modify it under
the terms of the GNU Affero General Public License as published by the Free
Software Foundation, either version 3 of the License, or (at your option) any
later version.

laforge is distributed in the hope that it will be useful, but WITHOUT ANY
WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A
PARTICULAR PURPOSE.  See the GNU Affero General Public License for more details.

You should have received a copy of the GNU Affero General Public License along
with laforge.  If not, see <https://www.gnu.org/licenses/>.
"""
