import random
import re
from copy import deepcopy
from pathlib import Path


INPUTS = [*Path(__file__).parent.glob("*.txt")]

content = {
    "statement": [
        "{observation}",
        "{diagnosis}",
        "{diagnosis}",
        "{diagnosis}",
        "{suggestion}",
        "{suggestion}",
        "{suggestion}",
    ],
    "apology": [
        "I'm not too sure about that.",
        "I'm stumped.",
        "Sorry, but I'm not sure.",
        "I can't figure out a good next step.",
        "This is a tough one.",
        "I wish I could be of more help.",
        "I wish I could be of further assistance.",
    ],
    "observation": [
        "I am detecting {observation_phrase}.",
        "We're picking up {observation_phrase}.",
        "I'm picking up {observation_phrase}.",
        "I'm seeing {observation_phrase}.",
        "Are you also seeing {observation_phrase}?",
        "Are you seeing {noun_phrase} {preposition} {noun_phrase}?",
    ],
    "observation_phrase": [
        "{problem_adjective} levels from {noun_phrase}",
        "{problem_adjective} readings from {noun_phrase}",
        "{problem_adjective} signals from {noun_phrase}",
    ],
    "diagnosis": [
        "I think we have {diagnosis_phrase}.",
        "I'd bet the problem is {diagnosis_phrase}.",
        "I'm not sure, but it might be {diagnosis_phrase}.",
        "If it's not {diagnosis_phrase}, it has to be {noun_phrase}.",
        "It might be {diagnosis_phrase}.",
        "It must be either {diagnosis_phrase} or {diagnosis_phrase}.",
        "My guess is that we have {diagnosis_phrase}.",
        "Perhaps there's an infestation of {lifeform} in {noun_phrase}.",
    ],
    "diagnosis_phrase": ["{diagnosis_core} {preposition} {noun_phrase}"],
    "diagnosis_core": [
        "{prenoun} anomalies",
        "{prenoun} fluctuations",
        "{prenoun} interference",
        "{prenoun} malfunctions",
        "{prenoun} distortions",
        "{prenoun} problems",
        "a rupture",
        "an anomaly",
        "an over-{verb_gerund} {noun}",
        "an under-{verb_gerund} {noun}",
        "an over-{verb_past} {noun}",
        "an under-{verb_past} {noun}",
        "a critical error",
        "a severe malfunction",
        "some kind of {prenoun} problem",
    ],
    "noun_phrase": [
        "the {prenoun} {noun}",
        "the {prenoun} {noun}",
        "the {prenoun} {noun} {postnoun}",
        "the {noun} {postnoun}",
    ],
    "number": ["1", "2", "3", "4"],
}

for file in INPUTS:
    key = file.stem
    words = [line for line in file.read_text().splitlines() if line.strip()]
    if key in content:
        content[key].extend(words)
    else:
        content[key] = words


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
    def __init__(self):
        self.content = deepcopy(content)
        for _key in content:
            random.shuffle(self.content[_key])

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
        result = result.format_map(self)  # type: ignore
        return result

    def __getitem__(self, item):
        return self.generate(item)


def capitalize_sentences(phrase):
    return "".join(make_first_upper(x) for x in re.split("([!?.] )", phrase))


def make_first_upper(s):
    """Uppercase the first letter of s, leaving the rest alone."""
    return s[:1].upper() + s[1:]
