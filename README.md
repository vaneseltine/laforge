<h2> laforge is a low-key build system for working with data.</h2>

[![PyPI - License](https://img.shields.io/pypi/l/laforge.svg?color=violet&style=flat-square)](https://www.gnu.org/licenses/agpl-3.0)<br>

[![PyPI - Status](https://img.shields.io/pypi/status/laforge.svg?style=flat-square&label=pypi%20status)](https://pypi.python.org/pypi/laforge)<br>

[![PyPI - Version](https://img.shields.io/pypi/v/laforge.svg?style=flat-square&label=pypi%20version)](https://pypi.python.org/pypi/laforge)<br>

[![Tickets](https://img.shields.io/badge/tickets-todo.sr.ht-yellow.svg?style=flat-square)](https://todo.sr.ht/~matvan/laforge)<br>

[![Builds](https://img.shields.io/badge/builds-builds.sr.ht-green.svg?style=flat-square)](https://builds.sr.ht/~matvan/laforge)<br>

[![Maintenance](https://img.shields.io/maintenance/yes/2019.svg?style=flat-square&label=actively%20maintained)](https://git.sr.ht/~matvan/laforge)<br>

[![Dependencies](https://img.shields.io/librariesio/release/pypi/laforge.svg?style=flat-square)](https://libraries.io/pypi/laforge)<br>

[![PyPI - Python Versions](https://img.shields.io/pypi/pyversions/laforge.svg?&style=flat-square)](https://pypi.python.org/pypi/laforge)<br>

[![PyPI - Downloads](https://img.shields.io/pypi/dw/laforge.svg?color=blueviolet&style=flat-square)](https://pepy.tech/project/laforge/week)<br>

![Built with coffee](https://img.shields.io/badge/built_with-coffee-5C4033.svg?style=flat-square)<br>

[![Cat - Onigiri](https://img.shields.io/badge/project_cat-Onigiri-333.svg?style=flat-square)](https://raw.githubusercontent.com/vaneseltine/vaneseltine.github.io/master/Oni.jpg)<br>

<!--![GitHub release](https://img.shields.io/github/release-pre/vaneseltine/laforge.svg?label=github%20mirror&style=flat-square) -->
<!--![GitHub release](https://img.shields.io/readthedocs/laforge.svg?style=flat-square) <!-- https://readthedocs.org/dashboard/> -->

### 💻 Getting Started ‖-)
 
*You know, I've always thought technology could solve almost any problem.*

```sh
> pip install laforge
```

*Data—I mean—Holmes, old boy, what are we looking for?*

```sh
> laforge create build.ini
```

*There's theory and then there's application. They don't always jibe.*

```ini
> cat ./build.ini
[DEFAULT]
read_dir: ./data
write_dir: ./output
distro: mssql
server: MSSQL
database: laforge
schema: demo

# Reading Excel; writing to a SQL table
[load_individual] 
read: 2019_indiv_data.xlsx
write: raw_grp

# Reading CSV; writing to a SQL table
[load_group] 
read: 2019_grp_data.csv
write: raw_indiv

# Execute a standalone SQL script; read SQL table; write CSV
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

*Yeah, but that's imposs— yes, sir.*

```sh
> laforge build
```

### 🚧 Development

*Captain, we can do it... It'll take fifteen years and a research team of a hundred.*

- Canonical repository: https://git.sr.ht/~matvan/laforge
- Issue tracking: https://todo.sr.ht/~matvan/laforge
- Build status: https://builds.sr.ht/~matvan/laforge
- Github mirror: https://github.com/vaneseltine/laforge
- PyPI package: https://pypi.org/project/laforge

### 🧙‍ Author

Matt VanEseltine
- Email: matvan@umich.edu
- Github: https://github.com/vaneseltine
- sr.ht: https://git.sr.ht/~matvan
- Twitter: https://twitter.com/vaneseltine
