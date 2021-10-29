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

import threading
import time

import pytest

from daemon import daemon
from daemon.settings.settings import PATHS as Config


def test_daemon(spinup_mqtt_broker, spinup_mqtt_iot_hub_mock_server):
    server = spinup_mqtt_iot_hub_mock_server
    server.expected(
        uploads={"device_id": {"foo": ["bar"]}},
        replies={"desired": {"JWT": "FOOBARBAZ"}, "reported": {},},
    )

    Config.conf_file = "tests/acceptance/testdata/mender-auth-azure-iot.json"
    Config.server_cert = "tests/acceptance/broker/server.crt"
    Config.identity_scripts = "tests/acceptance/testdata/identity_script"

    class Args:
        stop = False

    args = Args()
    daemon.DEVICE_UPDATE_INTERVAL = 5
    threading.Thread(target=daemon.run_daemon, args=(args,), daemon=True).start()
    time.sleep(10)
    assert len(server.received_twins) >= 1
    assert server.received_twins[0] == {
        "device_id": {"foo": "bar"},
        "JWT": "FOOBARBAZ",
    }

    args.stop = True
    time.sleep(10)
    server.teardown()
