## laforge is a low-key build system for working with data.

[![Development](https://img.shields.io/badge/development-active-44344f.svg)](https://git.sr.ht/~matvan/laforge)
[![PyPI](https://img.shields.io/badge/pypi-alpha-564d80.svg)](https://pypi.python.org/pypi/laforge)
[![AGPL v3](https://img.shields.io/badge/license-AGPL%20v3-98a6d4.svg)](https://www.gnu.org/licenses/agpl-3.0)
[![Builds](https://builds.sr.ht/~matvan/laforge.svg)](https://builds.sr.ht/~matvan/laforge?)
[![Tickets](https://img.shields.io/badge/ticket%20tracking-sr.ht-c0e6c2.svg)](https://todo.sr.ht/~matvan/laforge)
[![Downloads](https://pepy.tech/badge/laforge/week)](https://pepy.tech/project/laforge/week)  

---

## 💻 Getting Started
 
### Install.

```sh
> pip install laforge
```

### Create a build file.

```sh
> laforge create build.ini
```

### Edit until it's actually, say, useful...

```ini
> cat ./build.ini
[DEFAULT]
read_dir: ./data
write_dir: ./output
distro: mssql
server: MSSQL
database: laforge
schema: demo

[load_individual]# Reading Excel; writing to a SQL table
read: 2019_indiv_data.xlsx
write: raw_grp

[load_group]# Reading CSV; writing to a SQL table
read: 2019_grp_data.csv
write: raw_indiv

[do_some_things]# Execute a standalone SQL script; read SQL table; write CSV
execute: do_stuff.sql
read: laforge.demo.aggregate
write: aggregate.csv

[probs]# Read the result of an ad-hoc SQL query; write to an HTML table
read: 
    "select * from demo.aggregate agg
    left join demo.raw_indiv ri 
        on agg.v1 = r1.v2
    order by newid();"
write: 99_problems.html 
```

### Make it so.

```sh
> laforge build
```

## 🚧 Development

- Canonical repository: https://git.sr.ht/~matvan/laforge
- Github mirror: https://github.com/vaneseltine/laforge
- Issue tracking: https://todo.sr.ht/~matvan/laforge
- Build status: https://builds.sr.ht/~matvan/laforge
- Package distribution: https://pypi.org/project/laforge

## 🧙‍ Author: Matt VanEseltine

- Twitter: https://twitter.com/vaneseltine
- Github: https://github.com/vaneseltine
- Email: matvan@umich.edu 🖖

## Testing the output here...

- [x] foo
  - [ ] bar
  - [x] baz
- [ ] bim

≣-)