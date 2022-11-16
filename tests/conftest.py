# Copyright 2021 Canonical Ltd.
# See LICENSE file for licensing details.
from _pytest.config.argparsing import Parser


def pytest_addoption(parser: Parser):
    parser.addoption(
        "--channel",
        help="Zinc channel to deploy for integration tests. If absent"
        "the zinc charm will be built from source.",
    )
