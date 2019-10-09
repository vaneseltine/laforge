<h2>laforge is a low-key build system for working with data.</h2>

[![License: AGPL 3.0](https://img.shields.io/pypi/l/laforge.svg?style=flat-square&color=violet)](https://www.gnu.org/licenses/agpl-3.0)
[![Python: 3.6+](https://img.shields.io/pypi/pyversions/laforge.svg?&style=flat-square)](https://pypi.python.org/pypi/laforge)
[![GitHub last commit](https://img.shields.io/github/last-commit/vaneseltine/laforge.svg?style=flat-square)](https://github.com/vaneseltine/laforge)
[![Cat: Onigiri](https://img.shields.io/badge/cat-Onigiri-333.svg?style=flat-square)](https://github.com/vaneseltine/vaneseltine.github.io/blob/master/onigiri.jpg)

---


### 💻 Introduction

*You know, I've always thought technology could solve almost any problem.*

```
$ python -m pip install laforge -q
...

$ laforge create
Creating /home/matvan/science/build.ini
? Creating a new laforge INI at:  /home/matvan/science/build.ini

Creating /home/matvan/science/build.ini

? Default read directory, relative to /home/matvan/science/:  ./data
? Default write directory, relative to /home/matvan/science/:  ./output
? Default execute directory, relative to /home/matvan/science/:  ./
? SQL Distribution:  SQLite
?     Database:  :memory:
New laforge INI written at: /home/matvan/science/build.ini
Enjoy!

```

*There's theory and then there's application. They don't always jibe.*

```ini
$ vim ./build.ini
...

$ cat ./build.ini
[DEFAULT]
read_dir: ./data
write_dir: ./output
execute_dir: ./
distro: sqlite
database: :memory:

# Write the contents of an Excel sheet as a SQL table
[load_individual]
read: 2019_indiv_data.xlsx
write: raw_grp

# Write the contents of a CSV as a SQL table
[load_group]
read: 2019_grp_data.csv
write: raw_indiv

# Execute a standalone SQL script; read a SQL table and save as CSV
[do_some_things]
execute: do_stuff.sql
read: laforge.demo.aggregate
write: aggregate.csv

# Read the result of an ad-hoc SQL query; write to an HTML table
[peek]
read:
    "select top 50 *
    from demo.aggregate agg
    left join demo.raw_indiv ri
        on agg.v1 = r1.v2
    order by newid();"
write: results_peek.html
```

*Yeah, but that's imposs—yes, sir.*

```sh
$ laforge build
```
**‖-)**


### 📓 Documentation

https://laforge.readthedocs.io/en/latest/


### ⚗️ Development

*Captain, we can do it... It'll take fifteen years and a research team of a hundred.*

[![Canonical repository at github.](https://img.shields.io/github/tag-date/vaneseltine/laforge.svg?label=latest&style=for-the-badge&logo=github&logoColor=fff)](https://github.com/vaneseltine/laforge)

[![Issue tracking at github.](https://img.shields.io/github/issues/vaneseltine/laforge?logo=github&logoColor=fff&style=for-the-badge)](https://github.com/vaneseltine/laforge/issues)

[![PyPI receives versioned releases from the canonical repo.](https://img.shields.io/pypi/v/laforge.svg?style=for-the-badge&logo=python&logoColor=fff)](https://pypi.python.org/pypi/laforge)

[![Powered by Python...](https://img.shields.io/badge/powered_by-python-3776ab.svg?style=for-the-badge&logoWidth=5)](https://www.python.org/)

[![...and also by Diet Coke.](https://img.shields.io/badge/and_also_by-diet_coke-5C4033.svg?style=for-the-badge&logoWidth=5)]()


### 🤖 Automation

[![LGTM provides security analysis for PyPI releases.](https://img.shields.io/lgtm/alerts/github/vaneseltine/laforge.svg?style=for-the-badge)](https://lgtm.com/projects/g/vaneseltine/laforge/)

[![libraries.io audits PyPI dependencies status.](https://img.shields.io/librariesio/release/pypi/laforge.svg?style=for-the-badge&label=libraries.io)](https://libraries.io/pypi/laforge)

[![Documentation is hosted on Read the Docs.](https://img.shields.io/readthedocs/laforge.svg?style=for-the-badge&label=Read%20the%20Docs)](https://readthedocs.org/projects/laforge/builds/)

[![Travis tests across supported Python versions.)](https://img.shields.io/travis/com/vaneseltine/laforge.svg?style=for-the-badge&label=Travis&logo=travis-ci&logoColor=fff)](https://travis-ci.com/vaneseltine/laforge)

[![CircleCI is my new best friend.](https://img.shields.io/circleci/build/github/vaneseltine/laforge.svg?label=CircleCI&style=for-the-badge&logo=circleci&logoColor=fff)](https://circleci.com/gh/vaneseltine/laforge)

[![Coveralls reports coverage in a cute way.](https://img.shields.io/coveralls/github/vaneseltine/laforge.svg?style=for-the-badge&logo=coveralls)](https://coveralls.io/github/vaneseltine/laforge)




### 🧙‍ Author

[![Matt VanEseltine](https://img.shields.io/badge/name-matt_vaneseltine-888.svg?style=for-the-badge&logo=linux&logoColor=fff&color=violet)](https://vaneseltine.github.io)

[![matvan@umich.edu](https://img.shields.io/badge/email-matvan@umich.edu-888.svg?style=for-the-badge&logo=gmail&logoColor=fff&color=00274c)](matvan@umich.edu)

[![https://github.com/vaneseltine](https://img.shields.io/badge/github-vaneseltine-888.svg?style=for-the-badge&logo=github&logoColor=fff&color=2b3137)](https://github.com/vaneseltine)

[![https://twitter.com/vaneseltine](https://img.shields.io/badge/twitter-@vaneseltine-blue.svg?style=for-the-badge&logo=twitter&logoColor=fff&color=1da1f2)](https://twitter.com/vaneseltine)

[![https://stackoverflow.com/users/7846185/matt-vaneseltine](https://img.shields.io/badge/stack_overflow-matt_vaneseltine-888.svg?style=for-the-badge&logo=stack-overflow&logoColor=fff&color=f48024)](https://stackoverflow.com/users/7846185/matt-vaneseltine)
