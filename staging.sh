#!/bin/sh
echo "import common.fixture as fixture;fixture.showroom_fixture_state_no_confirmation()"|python3 manage.py shell
