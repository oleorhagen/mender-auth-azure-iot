# Copyright 2021 Northern.tech AS
#
#    Licensed under the Apache License, Version 2.0 (the "License");
#    you may not use this file except in compliance with the License.
#    You may obtain a copy of the License at
#
#        http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS,
#    WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#    See the License for the specific language governing permissions and
#    limitations under the License.

import logging as log
import os
import stat

import pytest

from daemon.scripts import identity


class TestIdentityAggregator:
    @pytest.fixture(autouse=True)
    def set_log_level(self, caplog):
        caplog.set_level(log.INFO)

    @pytest.fixture
    def file_create_fixture(self, tmpdir):
        d = tmpdir.mkdir("inventoryaggregator")

        def create_script(data):
            f = d.join("script")
            f.write(data)
            os.chmod(f, stat.S_IRWXU | stat.S_IRWXO | stat.S_IRWXG)
            return str(f)

        return create_script

    @pytest.mark.parametrize(
        "data, expected",
        [
            (
                """#! /bin/sh
        echo mac=c8:5b:76:fb:c8:75
    """,
                {"mac": "c8:5b:76:fb:c8:75"},
            ),
            (
                """#! /bin/sh
                echo foo=bar
                echo bar=baz""",
                {"foo": "bar", "bar": "baz",},
            ),
        ],
    )
    def test_identity(self, data, expected, file_create_fixture):
        tpath = file_create_fixture(data)
        identity_data = identity.aggregate(tpath)
        assert identity_data
        assert identity_data == expected

    def test_no_identity(self, caplog):
        identity_data = identity.aggregate(path="/i/do/not/exist")
        assert not identity_data
        assert "No identity can be collected" in caplog.text

    def test_identity_not_executable(self, caplog, tmpdir):
        d = tmpdir.mkdir("identity-test")
        f = d.join("mender-device-identity")
        f.write(
            """#! /bin/sh
        echo mac=c8:5b:76:fb:c8:75"""
        )
        identity_data = identity.aggregate(path=f)
        assert not identity_data
        assert "is not executable" in caplog.text
