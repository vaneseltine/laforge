################################
An Example Build
################################

Directory Organization
================================

Because *laforge* needs to find the scripts, and because
scripts will likely interact with output from other scripts,
I tend to keep related project/sub-project files together::

    project_nemesis
    ├───input
    │   ├───adjustments.csv
    │   ├───evil_lair_data.xlsx
    │   └───overrides.csv
    ├───output
    │   ├───results_general.csv
    │   ├───results_employee.csv
    │   └───results_troll.csv
    ├───build.toml
    ├───get_material_costs.py
    ├───create_oubliette.sql
    ├───calc_assess_timeline.py
    └───cover_all_tracks.py

build.toml
================================

::

    [[config.dir]]
    output = 'N:/output/'

    [[config.sql]]
    load = './sqlecrets.py'

    [[task]]
    description = 'Assess project timeline'
    read = ''
    execute = 'calc_assess_timeline.py'
    write = ''

    [[task]]
    description = 'Gather cost estimates'
    execute = [
        'get_material_costs.py',
        'query_goblin_salaries.py',
    ]
    write = ''

    [[task]]
    description = 'Crunch numbers'

    [[task]]
    description = 'Contingency plans'
    read = ''
    execute = 'create_oubliette.sql'
    write = ''

    [[task]]
    description = 'Teardown and cleanup'
    execute = [
        'remove_evidence',
        'cover_tracks.py',
    ]
