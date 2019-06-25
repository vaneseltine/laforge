### laforge is a low-key build system for working with data.
[![PyPI - License](https://img.shields.io/pypi/l/laforge.svg?color=violet&style=flat-square)](https://www.gnu.org/licenses/agpl-3.0)  
[![PyPI - Status](https://img.shields.io/pypi/status/laforge.svg?style=flat-square)](https://pypi.python.org/pypi/laforge)  
[![PyPI - Version](https://img.shields.io/pypi/v/laforge.svg?style=flat-square)](https://pypi.python.org/pypi/laforge)  
[![Tickets](https://img.shields.io/badge/tickets-sr.ht-yellow.svg?style=flat-square)](https://todo.sr.ht/~matvan/laforge)  
[![Builds](https://img.shields.io/badge/builds-sr.ht-green.svg?style=flat-square)](https://builds.sr.ht/~matvan/laforge)  
[![Maintenance](https://img.shields.io/maintenance/yes/2019.svg?style=flat-square)](https://git.sr.ht/~matvan/laforge)  
[![Dependencies](https://img.shields.io/librariesio/release/pypi/laforge.svg?style=flat-square)](https://libraries.io/pypi/laforge)  
[![PyPI - Python Versions](https://img.shields.io/pypi/pyversions/laforge.svg?&style=flat-square)](https://pypi.python.org/pypi/laforge)  
[![PyPI - Downloads](https://img.shields.io/pypi/dw/laforge.svg?color=blueviolet&style=flat-square)](https://pepy.tech/project/laforge/week)  
[![Enjoys - Badges](https://img.shields.io/badge/built_with-☕-black.svg?style=flat-square)](https://pepy.tech/project/laforge/week)  

![GitHub release](https://img.shields.io/github/release-pre/vaneseltine/laforge.svg?label=github%20mirror&style=flat-square)  
<!-- https://readthedocs.org/dashboard/> -->

### 💻 Getting Started
 
#### Install.

```sh
> pip install laforge
```

#### Create a build file.

```sh
> laforge create build.ini
```

#### Edit until it's actually, say, useful...

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

#### Make it so.

```sh
> laforge build
```

### 🚧 Development

- Canonical repository: https://git.sr.ht/~matvan/laforge
- Issue tracking: https://todo.sr.ht/~matvan/laforge
- Build status: https://builds.sr.ht/~matvan/laforge
- Github mirror: https://github.com/vaneseltine/laforge
- PyPI package: https://pypi.org/project/laforge

### 🧙‍ Author: Matt VanEseltine

- Twitter: https://twitter.com/vaneseltine
- Github: https://github.com/vaneseltine
- Email: matvan@umich.edu

#### ‖-)