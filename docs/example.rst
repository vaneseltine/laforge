################################
An Example Build
################################

Directory Organization
================================

Because *laforge* needs to find the scripts, and because
scripts will likely interact with output from other scripts,
I tend to keep related project/sub-project files together::

    project
    ├───input
    │   ├───a.csv
    │   ├───b.xlsx
    │   └───c.csv
    ├───output
    │   ├───results_d.csv
    │   ├───results_e.csv
    │   └───results_f.csv
    ├───.env
    ├───build.ini
    ├───g.py
    ├───h.sql
    ├───i.py
    └───j.py

.env
================================

::

    distro = mssql
    server = MSSQL
    database = testdb
    schema = laforge


build.ini
================================

::

    [DEFAULT]
