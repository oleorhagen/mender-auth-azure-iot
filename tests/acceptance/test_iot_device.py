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

import pytest
import threading

from daemon import daemon


def test_daemon(spinup_mqtt_broker, spinup_mqtt_iot_hub_mock_server):
    server = spinup_mqtt_iot_hub_mock_server
    server.expected(
        uploads={"device_id": {"foo": ["bar"]}},
        replies={"desired": {"JWT": "FOOBARBAZ"}, "reported": {},},
    )
    import time

    # TODO - Should possibly be replaced with a healthcheck
    time.sleep(3)
    server.spin()
    # TODO - Same for the server
    time.sleep(3)

    class Stop:
        def __init__(self):
            self.stop = False

        def now(self):
            self.stop = True

    stop  = Stop()

    # Quick for tests
    daemon.DEVICE_UPDATE_INTERVAL = 5
    threading.Thread(target=daemon.run_daemon, args=(stop,), daemon=True).start()
    time.sleep(10)
    assert len(server.received_twins) >= 1
    assert server.received_twins[0] == {
        "device_id": {"foo": ["bar"]},
    }
    assert daemon.JWT_TOKEN == "FOOBARBAZ"

    stop.now()
    time.sleep(10)
    server.teardown()
