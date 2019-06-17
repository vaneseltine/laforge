from pathlib import Path
from setuptools import find_packages, setup
import laforge

extras_require = {
    "postgresql": ["psycopg2>=2.8"],  # PostgreSQL
    "mysql": ["pymysql>=0.9"],  # MySQL or MariaDB
    "mssql": ["pyodbc>=4.0"],  # Microsoft SQL Server
}
extras_require["all"] = set(x for y in extras_require.values() for x in y)

long_description = Path("./README.rst").read_text()

setup(
    name="laforge",
    version=laforge.__version__,
    author="Matt VanEseltine",
    author_email="matvan@umich.edu",
    description=laforge.__doc__,
    long_description=long_description,
    long_description_content_type="text/x-rst",
    url="https://git.sr.ht/~matvan/laforge",
    license="AGPL-3.0-or-later",
    packages=find_packages(),
    include_package_data=True,
    # data_files=[("config", ["laforge/sql_reserved_words.toml"])],
    entry_points={"console_scripts": ["laforge = laforge:run_laforge"]},
    zip_safe=False,
    install_requires=[
        "Click>=7.0",
        "pandas>=0.22",
        "pyparsing>=2.3",
        "SQLAlchemy>=1.3",
    ],
    extras_require=extras_require,
    classifiers=[
        "Development Status :: 2 - Pre-Alpha",
        "Environment :: Console",
        "Intended Audience :: Developers",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: "
        "GNU Affero General Public License v3 or later (AGPLv3+)",
        "Natural Language :: English",
        "Operating System :: Microsoft :: Windows",
        "Operating System :: POSIX :: Linux",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3 :: Only",
        "Programming Language :: SQL",
        "Topic :: Database",
        "Topic :: Scientific/Engineering",
        "Topic :: Software Development :: Build Tools",
    ],
    keywords="data build SQL database",
)
