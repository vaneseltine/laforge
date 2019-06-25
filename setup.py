from glob import glob

from setuptools import find_packages, setup

install_requires = [
    "Click>=7.0",
    "pandas>=0.22",
    "PyInquirer>=1.0",
    "pyparsing>=2.3",
    "SQLAlchemy>=1.3",
]
extras_require = {
    "postgresql": ["psycopg2>=2.8"],  # PostgreSQL
    "mysql": ["pymysql>=0.9"],  # MySQL or MariaDB
    "mssql": ["pyodbc>=4.0"],  # Microsoft SQL Server
    "excel": ["xlrd"],  # Pandas backend for *.xls files
}
extras_require["all"] = list(set(x for y in extras_require.values() for x in y))

setup(
    packages=find_packages(),
    data_files=glob(f"laforge/**/*.txt"),
    entry_points={"console_scripts": [f"laforge = laforge:run_laforge"]},
    install_requires=install_requires,
    extras_require=extras_require,
)
