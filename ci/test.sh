#!/bin/bash

set -eux

# Add chromedriver to PATH, manually installed by ci/setup.sh.
export PATH="${PWD}/chromedriver:$PATH"

# Tests run under Python 2.  Run once with SQLite and again with MySQL.
if [[ "$TRAVIS_PYTHON_VERSION" == 2* ]]; then
    MEROU_TEST_DATABASE='mysql://travis:@localhost/merou' py.test -v
    py.test -x -v
fi

# Python 3 currently only does static analysis.
if [[ "$TRAVIS_PYTHON_VERSION" == 3* ]]; then
    mypy .
    black --check .
    flake8 --count
fi
