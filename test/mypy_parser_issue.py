# https://github.com/python/typeshed/blob/master/stdlib/3/configparser.pyi
# https://docs.python.org/3/library/typing.html#

import configparser

p = configparser.ConfigParser()

assert p._comment_prefixes
assert hasattr(p, "_comment_prefixes")
assert p._converters
assert hasattr(p, "_converters")
assert p._delimiters
assert hasattr(p, "_delimiters")
assert p._dict
assert hasattr(p, "_dict")
assert p._empty_lines_in_values
assert hasattr(p, "_empty_lines_in_values")
assert p._interpolation
assert hasattr(p, "_interpolation")
assert p._optcre
assert hasattr(p, "_optcre")
assert p._proxies
assert hasattr(p, "_proxies")
assert p._strict
assert hasattr(p, "_strict")
assert p.default_section
assert hasattr(p, "default_section")

print("Everything checks out.")
