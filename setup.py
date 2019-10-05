import setuptools

BASICS = [  # For maximums tested, see requirements.txt
    "python-dotenv>=0.10.3",
    "pandas>=0.22",
    "pyparsing>=2.0",
    "SQLAlchemy>=1.1",
]
EXTRAS = {
    "postgresql": ["psycopg2>=2.8"],  # PostgreSQL
    "mssql": ["pyodbc>=4.0"],  # Microsoft SQL Server
    "excel": ["xlrd==1.2.0", "XlsxWriter==1.1.8"],  # Pandas backends
}
EXTRAS["all"] = [*{x for y in EXTRAS.values() for x in y}]


setuptools.setup(
    packages=setuptools.find_packages(),
    entry_points={"console_scripts": [f"laforge = laforge:run"]},
    install_requires=BASICS,
    extras_require=EXTRAS,
)
