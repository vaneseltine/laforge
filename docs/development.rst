********************************
Contributing to Development
********************************

*laforge* supports Python 3.6 through, currently, `the 3.8.0 alpha <https://docs.python.org/dev/>`_.

==================  =========== =========================================
Process             Tool         Documentation
==================  =========== =========================================
**Automation**      tox          `<https://tox.readthedocs.io/>`_
**Test**            pytest       `<https://docs.pytest.org/>`_
**Test coverage**   pytest-cov   `<https://pytest-cov.readthedocs.io/>`_
**Format**          Black        `<https://black.readthedocs.io/>`_
**Lint**            Flake8       `<http://flake8.pycqa.org/>`_
**Document**        Sphinx       `<https://www.sphinx-doc.org/>`_
==================  =========== =========================================


Recommended Environment
================================

.. code-block:: shell

    # Create virtual environment
    python -m venv .venv

    # Activate virtual environment with shell-specific script:
    . .venv/bin/activate.fish           # fish
    # $ source ./.venv/bin/activate     # bash
    #  source ./.venv/bin/activate.csh	# csh
    # Note that Python for Windows creates ./Scripts/ rather than ./bin/
    # .\.venv\Scripts\Activate.ps1      # PowerShell
    # .venv\Scripts\Activate.bat        # cmd

    # Install packages
    python -m pip install -r requirements.txt

    # Run the gauntlet
    python -m nox

Linux Note
===========

Debian and friends, such as Ubuntu, require several packages to function.
I've installed the following (and their dependencies) for each version:

    - python3.X
    - python3.X-dev
    - python3.X-venv

For older versions of Python in Ubuntu, see:
https://launchpad.net/~deadsnakes/+archive/ubuntu/ppa
