import setuptools

BASICS = [  # For maximums tested, see requirements.txt
    "Click>=7.0",
    "python-dotenv>=0.10.3",
    "pandas>=0.22",
    "questionary>=1.0",
    "pyparsing>=2.0",
    "PyYAML>=3.10",
    "SQLAlchemy>=1.1",
]
EXTRAS = {
    "postgresql": ["psycopg2>=2.8"],  # PostgreSQL
    "mysql": ["pymysql>=0.9"],  # MySQL or MariaDB
    "mssql": ["pyodbc>=4.0"],  # Microsoft SQL Server
    "excel": ["xlrd==1.2.0", "XlsxWriter==1.1.8"],  # Pandas backends
}
EXTRAS["mariadb"] = EXTRAS["mysql"]
EXTRAS["all"] = [*{x for y in EXTRAS.values() for x in y}]


setuptools.setup(
    packages=setuptools.find_packages(),
    entry_points={"console_scripts": [f"laforge = laforge:run_laforge"]},
    install_requires=BASICS,
    extras_require=EXTRAS,
)
