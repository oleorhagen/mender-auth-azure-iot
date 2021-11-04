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

import pytest

from daemon.config import config


class TestFileNotFound:
    @pytest.fixture(autouse=True)
    def set_log_level(self, caplog):
        caplog.set_level(log.DEBUG)

    def test_file_not_found_error(self, caplog):
        with pytest.raises(config.NoConfigurationFileError):
            config.load("")
        assert "Configuration file: '' not found" in caplog.text

    def test_correct_configuration_file(self):
        conf = config.load("tests/unit/testdata/azure.json")
        assert conf.ConnectionString == "foobarbaz"
