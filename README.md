# SSB Altinn Form Tools

[![PyPI](https://img.shields.io/pypi/v/ssb-altinn-form-tools.svg)][pypi status]
[![Status](https://img.shields.io/pypi/status/ssb-altinn-form-tools.svg)][pypi status]
[![Python Version](https://img.shields.io/pypi/pyversions/ssb-altinn-form-tools)][pypi status]
[![License](https://img.shields.io/pypi/l/ssb-altinn-form-tools)][license]

[![Documentation](https://github.com/statisticsnorway/ssb-altinn-form-tools/actions/workflows/docs.yml/badge.svg)][documentation]
[![Tests](https://github.com/statisticsnorway/ssb-altinn-form-tools/actions/workflows/tests.yml/badge.svg)][tests]
[![Coverage](https://sonarcloud.io/api/project_badges/measure?project=statisticsnorway_ssb-altinn-form-tools&metric=coverage)][sonarcov]
[![Quality Gate Status](https://sonarcloud.io/api/project_badges/measure?project=statisticsnorway_ssb-altinn-form-tools&metric=alert_status)][sonarquality]

[![pre-commit](https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit&logoColor=white)][pre-commit]
[![Black](https://img.shields.io/badge/code%20style-black-000000.svg)][black]
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)
[![Poetry](https://img.shields.io/endpoint?url=https://python-poetry.org/badge/v0.json)][poetry]

[pypi status]: https://pypi.org/project/ssb-altinn-form-tools/
[documentation]: https://statisticsnorway.github.io/ssb-altinn-form-tools
[tests]: https://github.com/statisticsnorway/ssb-altinn-form-tools/actions?workflow=Tests
[sonarcov]: https://sonarcloud.io/summary/overall?id=statisticsnorway_ssb-altinn-form-tools
[sonarquality]: https://sonarcloud.io/summary/overall?id=statisticsnorway_ssb-altinn-form-tools
[pre-commit]: https://github.com/pre-commit/pre-commit
[black]: https://github.com/psf/black
[poetry]: https://python-poetry.org/

## Features

- Tools for automatically handling forms from Altinn3
    - Transforms the data to the standard schema for SSBs editing framework
    - Ingests the data using SQLAlchemy og Parquedit.

## Requirements

- TODO

## Installation

You can install _SSB Altinn Form Tools_ via [pip] from [PyPI]:

```console
pip install ssb-altinn-form-tools
```
## Example
See ```docs/documentation``` for further information.
[Walkthrough](docs/documentation/walkthrough.md) provides a deeper guide through the example and how everything works.

```python
import logging

logging.basicConfig(
    level=logging.DEBUG,  # Set minimum log level
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    force=True,
)

from sqlalchemy import create_engine
from ssb_altinn_form_tools.default_form_processor import DefaultFormProcessor
from ssb_altinn_form_tools.default_form_extractor import DefaultFormExtractor
from ssb_altinn_form_tools.sqlalchemy_storage_connector import (
    SqlAlchemyStorageConnector,
)

extractor = DefaultFormExtractor()

engine = engine = create_engine("sqlite:///./db.db", echo=False)
connector = SqlAlchemyStorageConnector(engine)
for form_number in ["RA0187", "RA0297", "RA0307", "RA0366", "RA0479", "RA0481", "RA0530", "RA0536", "RA0689", "RA0745", "RA0825"]:
    processor = DefaultFormProcessor(
        form_name=form_number,
        form_base_path=f"/home/onyxia/work/ssb-altinn-form-tools/tests/testdata/{form_number}",
        extractor=extractor,
        connector=connector,
        alias_mapping={"omsVirksomhetPerioden": "omsetning"},
    )
    processor.process_new_forms()

from sqlalchemy import text

with engine.connect() as conn:
    tables = conn.execute(text("SELECT name FROM sqlite_master WHERE type='table';")).fetchall()
    print("Tables:", tables)

with engine.connect() as conn:
    rows = conn.execute(text("SELECT * FROM enheter LIMIT 10;")).mappings().all()
    for row in rows:
        print(dict(row))

```

## Usage

Please see the [Reference Guide] for details.

## Contributing

Contributions are very welcome.
To learn more, see the [Contributor Guide].

## License

Distributed under the terms of the [MIT license][license],
_SSB Altinn Form Tools_ is free and open source software.

## Issues

If you encounter any problems,
please [file an issue] along with a detailed description.

## Credits

This project was generated from [Statistics Norway]'s [SSB PyPI Template].

[statistics norway]: https://www.ssb.no/en
[pypi]: https://pypi.org/
[ssb pypi template]: https://github.com/statisticsnorway/ssb-pypitemplate
[file an issue]: https://github.com/statisticsnorway/ssb-altinn-form-tools/issues
[pip]: https://pip.pypa.io/

<!-- github-only -->

[license]: https://github.com/statisticsnorway/ssb-altinn-form-tools/blob/main/LICENSE
[contributor guide]: https://github.com/statisticsnorway/ssb-altinn-form-tools/blob/main/CONTRIBUTING.md
[reference guide]: https://statisticsnorway.github.io/ssb-altinn-form-tools/reference.html
