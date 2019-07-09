********************************
Contributing to Development
********************************

*laforge* supports Python 3.6+.

==================  =========== ==============================================
Process             Tool         Documentation
==================  =========== ==============================================
**Automation**      Nox          `<https://nox.readthedocs.io/>`_
**Test**            pytest       `<https://docs.pytest.org/>`_
**Test coverage**   pytest-cov   `<https://pytest-cov.readthedocs.io/>`_
**Format**          Black        `<https://black.readthedocs.io/>`_
**Lint**            Flake8       `<http://flake8.pycqa.org/>`_
**Lint more**       Pylint       `<https://pylint.readthedocs.io/en/latest/>`_
**Document**        Sphinx       `<https://www.sphinx-doc.org/>`_
==================  =========== ==============================================


Suggested Environment
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

    # Install working copy
    
    # If desired, optional packages for Excel or other DBs...
    # python -m pip install -e .[excel]
    # python -m pip install -e .[mysql]
    # python -m pip install -e .[all]

    # Run tests
    python -m pytest

    # Run the gauntlet
    python -m nox


Embedded TODOs
================================

.. todolist::


Docstring Gaps
================================

.. include:: _static/python.txt
    :literal:
