<h2>laforge is a low-key build system for working with data.</h2>

 [![License: AGPL 3.0](https://img.shields.io/pypi/l/laforge.svg?style=flat-square&color=violet)](https://www.gnu.org/licenses/agpl-3.0)
 [![Python: 3.6+](https://img.shields.io/pypi/pyversions/laforge.svg?&style=flat-square)](https://pypi.python.org/pypi/laforge) 
 [![GitHub last commit](https://img.shields.io/github/last-commit/vaneseltine/laforge.svg?style=flat-square)](https://git.sr.ht/~matvan/laforge)
 [![Cat: Onigiri](https://img.shields.io/badge/cat-Onigiri-333.svg?style=flat-square)](https://raw.githubusercontent.com/vaneseltine/vaneseltine.github.io/master/Oni.jpg)

---

### 💻 Begin

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

### 📓 Documentation

https://laforge.readthedocs.io/en/latest/

### ⚗️ Development

*Captain, we can do it... It'll take fifteen years and a research team of a hundred.*

[![Canonical repository is at git.sr.ht.](https://img.shields.io/badge/canonical_repo-git.sr.ht-orange.svg?style=for-the-badge&logoWidth=0)](https://git.sr.ht/~matvan/laforge)

[![Issue tracker is at todo.sr.ht.](https://img.shields.io/badge/issue_tracker-todo.sr.ht-yellow.svg?style=for-the-badge&logoWidth=0)](https://todo.sr.ht/~matvan/laforge)

[![Build service is at builds.sr.ht.](https://img.shields.io/badge/build_service-builds.sr.ht-green.svg?style=for-the-badge&logoWidth=0)](https://builds.sr.ht/~matvan/laforge)

<!-- [![PyPI release.](https://img.shields.io/pypi/dw/laforge.svg?label=PyPI%20Downloads&style=for-the-badge&logoWidth=0)](https://pypi.org/project/laforge) -->

[![Designed with Diet Coke.](https://img.shields.io/badge/designed_with-diet_coke-5C4033.svg?style=for-the-badge&logoWidth=5)]()

### 🤖 Automated Checks

[![LGTM Alerts](https://img.shields.io/lgtm/alerts/github/vaneseltine/laforge.svg?style=for-the-badge)](https://lgtm.com/projects/g/vaneseltine/laforge/)

[![Dependencies analysis](https://img.shields.io/librariesio/release/pypi/laforge.svg?style=for-the-badge&label=libraries.io)](https://libraries.io/pypi/laforge)

[![Latest version of documentation on Read the Docs](https://img.shields.io/readthedocs/laforge.svg?style=for-the-badge&label=Read%20the%20Docs)](https://readthedocs.org/projects/laforge/builds/)

[![Travis (.com)](https://img.shields.io/travis/com/vaneseltine/laforge.svg?style=for-the-badge&label=Travis)](https://travis-ci.com/vaneseltine/laforge)

### 🚀 Descendant Releases

[![GitHub tag (latest by date)](https://img.shields.io/github/tag-date/vaneseltine/laforge.svg?label=github&style=for-the-badge)](https://github.com/vaneseltine/laforge)

[![PyPI](https://img.shields.io/pypi/v/laforge.svg?style=for-the-badge)](https://pypi.python.org/pypi/laforge)

### 🧙‍ Author: Matt VanEseltine

[![matvan@umich.edu](https://img.shields.io/badge/email-matvan@umich.edu-888.svg?style=for-the-badge&logo=gmail&color=00274c)](matvan@umich.edu)

[![https://git.sr.ht/~matvan](https://img.shields.io/badge/sr.ht-matvan-888.svg?style=for-the-badge&color=007bff&logo=data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAIAAAACACAMAAAD04JH5AAAACXBIWXMAAAsTAAALEwEAmpwYAAAAB3RJTUUH4QIGCC8n92KyhQAAAj1QTFRFAAAA////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////anIwUQAAAL50Uk5TAAECAwQFBgcICQoLDA4PEBESExQVFhcYGRobHB0eHyAhIyQmJygpKistLzAzNDU2Nzg5Ozw9QEFDREZHSElLTE1OT1BRVFdYWVpbXF1eX2BhZGZnaGltbnBxdHV3eHp7fn+AgYKDhIWGh4iJio2TlJucnqGio6Smp6ipqqusrbCxsrO0tre4ury9vr/Cw8TFxsfIycrMzc7P0dLT1dbY2dvf4OLj5OXm5+jq6+zt7u/w8fL09fb3+Pn6+/z9/gNzyOkAAAABYktHRL6k3IPDAAAFwUlEQVQYGe3B+VtUVQAG4G9i0TQZZyA1S0JxydzDNFTUqXBfcylzS8UE21TMyjAQUQnFEi0BHQU3cAc0UGbm+9v65Zw7y70zc++dc3qenof3xZAhQ4b8T+V/uGn/kdrm1psdHTdbm2uP7Ns434//yLD5e+u7aOH+6T0ludBszGf1L5jC87rNBdDm9XXnw0wrfG71cOhQ9N0z2vTk20Ko9t5PYToQOj4FKr17IkKHwtUToMobVQN0of/rkVDik7t06c5yZC7/V1rqajq6f9vKQFlZYNW2A0cvdNPSL35kaPEDmgxerFiSjwQFZQebQzTpKkUmsg4xUX/Nijwk4V15aoAJIhVZcM13ngnatuQhJe/WNiY464VLE28xXsMCD9LyLDzLeMEiuDLzIeM0zIRNs88xTvcMuFDSx1htC+FA6XXG6pkLx0qeM8aLHdlwJGfnP4zRNw8OzexjjOaJcGzSn4zR8z4cmfiQUZF9WXAhuyLCqO4iOOC7xahni+BSWQ+jgl7YlnWeUR3FcG1qJ6MasmDXIUZdexMZGNvGqAOwaTGjrnqREd/fNERKYUvBAxqueZEhXzsNXX7Y8SsNHW8iY+M6afgZNnxKw7NiKDCtl4YA0nrjHqXIIiixjIY7I5FOFQ37oEglDZVIo+glpeYsKJJ9mdJAIVI7QenFRChT3E+pGim9F6G0AwrtohSeglR+otSWDYVygpSqkUJRmNJCKLWEUmgCkvuOUgPU8vxO6TCSev0ZpZlQ7ANKj4YhmXWUGqBcI6UVSOY8pQVQbhGlM0hiTJhCmwfKeW5QCPlh7TNKW6DBdkobYa2eQn8eNPC9pPAbLA17QaEGWtRS6MuBlfmUVkCLtZTmwspeCoN50MIXprATVuopXIQmLRROwUoXhQpoUkXhNizkU1oCTZZRyoPZh5Tyock4SnNgtolCF3TxPKKwBmb7KTRBm0sUdsPsCIWj0OY4hR9gVkthP7SppHASZs0UtkGbLyg0wqyVwkpos4FCC8xuUghAm3IK7TDroFAGbQIUgjDroFAGbQIUgjC7SSEAbcoptMOslcIqaLOBQgvMmilsgzY7KDTCrJbCAWhTReEkzI5QOAptfqTwPcz2UbgAbS5R2AWzjRS6oYvnMYXVMJtPqQCavEVpNsz8lMqgyXJKo2DhPoWD0OQwhU5YOU2hGZpcoVADK3sohLzQwh+h8CWslFBaCS3WUZoDK7nPKZyCFnUUerNh6TSFAS808L+iUANrmylthQafU1oPawVhCm0eKOcJUhgcjSTOUVoI5RZTqkMyqymdhXJNlMqRzPAnlGZDsRJKD3OR1LeUzkEtTxOlSiRXGKL0EZRaSmlwPFI4Tul6DhTKvUXpGFKZEqa0EwrtoRQqRkrVlP6ZBGUmD1A6htQm9FP6IxuK5Fyl1P8O0viahgoo8g0NB5HOyDuUImVQ4mMabo9AWgEaeqZCgel9NCyFDb/Q0DkWGXv7Lg0nYIe/i4Y2HzKUf4OGe6NhS2mEhr98yEh+Kw3hBbCpglHt45CB8TcY9RXsyjrLqM5pcG36XUadfg22eYOM6l0Glz7uY9T1UXCg6AFjHMqGCznfMMb9Qjgyo4cxLhfDsclXGePpdDg0r48x+nflwJHcPQOM0TsLjs3rYazgEtjnWXqLsZ7Oggszuhnn9w9gU0kT49yfDleKgozXuMiDtDyLmxjveiFc8jYwwY3tPqTk/zzIBPWj4FpWRYQJXtau9SEJ/7q6V0wQ/uo1ZKK0iybhlqplYxHP89byw1ciNLm3ABny/0xLjy4dr/xiQ3kgUL5hR9WPlx7T0onRyFzgDl26vRRKjKwcoAv9B0dAlcLqMB0KH3sHKk2pDtGBwWPFUG3C4Ue06WHleOgwbMWZENMarCvPhTb+jb/1MYXemvWjoVnO3J2nbtNCZ82Xc7LxH8mbs2b3DycbW9qDwfaWxpPf71o9exSGDBky5P/pX9F6dsCMuJp+AAAAAElFTkSuQmCC)](https://git.sr.ht/~matvan)


[![https://github.com/vaneseltine](https://img.shields.io/badge/github-vaneseltine-888.svg?style=for-the-badge&logo=github&color=2b3137)](https://github.com/vaneseltine)

[![https://twitter.com/vaneseltine](https://img.shields.io/badge/twitter-@vaneseltine-blue.svg?style=for-the-badge&logo=twitter&color=1da1f2)](https://twitter.com/vaneseltine)

#### ‖-)
