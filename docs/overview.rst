
********************************
Overview
********************************

*laforge* is a low-key build system designed to interoperate
Python, SQL, and Stata data work, originally developed internally
for `IRIS, the Institute for Research on Innovation and Science
<https://iris.isr.umich.edu>`_
at the `University of Michigan's Institute for Social Research
<https://isr.umich.edu>`_.

Features:

* Interoperable: Read, write, and execute Python, SQL, and Stata scripts/data.
* Straightforward: Simple build INI files designed for a one-click build.
* No lock-in: Maintain scripts independent from *laforge*.

.. .. todo::

..     This gets too deep for an overview.

.. Executing a build
.. ================================

.. Provide a path to a TOML build configuration file::

..     > laforge build build/final_build.toml

.. Or let *laforge* figure it out::

..     > ls
..     laforge.toml
..     > laforge build

.. Starting a new build
.. ================================

.. Before trying to execute one, you'll probably want to start a build config.
.. An example is included `LINKY LINK LINK`

.. **laforge init**
..     moo


.. Recording build tasks
.. ================================

.. The most important bits are the actual build tasks.
.. Each specifies one of the following supported operations:

.. **description**
..     Optional human description for logging output.

.. **read**
..     Runs a Python script by importing it directly.
..     Nothing within the Python file is altered or adjusted,
..     and no parameters are passed.

..     .. note::

..         The import process makes the script more accessible for the build
..         process, but it might be helpful to be able to adjust the script
..         depending on whether it is being directly run or imported.
..         (E.g., import paths may need to be tweaked.)
..         Here is one way to determine its status:

..             .. code-block:: Python

..                 try:
..                     assert __file__
..                     RUNNING_STANDALONE = True
..                 except NameError:
..                     RUNNING_STANDALONE = False


.. **execute**
..     Execute any number of queries written as a saved ``.sql`` script.
..     No changes are made to the SQL queries in the file,
..     and no parameters are passed.

..     .. note::

..         Following Microsoft SQL Server, the word **go** is used
..         as a batch separator across all distributions.


.. **write**
..     balh blah (relative to SCRIPT_DIR) that yields data from its final query
..     (i.e, a SELECT)


.. Build configuration
.. ================================

.. The config section of the TOML establishes core directories
.. and references for SQL connectivity.

.. **config.dir**
..     Paths can be absolute or relative to the build configuration TOML.

..     **config.dir.build**
..         Default: the directory of the build configuration TOML.

..         .. note::

..             To work from directories relative to where *laforge* is run,
..             use change the build directory to `./`.

..     **config.dir.read**
..         Default: `{dir.build}/data/`

..     **config.dir.execute**
..         Default: `{dir.build}/script/`

..     **config.dir.write**
..         Default: `{dir.build}/output/`

.. **config.sql**

..     The distribution and server are required. Default database and/or schema
..     are optional and dependent on distribution.

..     Alternatively, an OBDC SQL URL can be specified to pass to SQLAlchemy.
..     See https://www.connectionstrings.com/.

..     **config.sql.distro**
..         ...

..     **config.sql.server**
..         ...

..     **config.sql.database**
..         ...

..     **config.sql.schema**
..         ...

..     **config.sql.url**
