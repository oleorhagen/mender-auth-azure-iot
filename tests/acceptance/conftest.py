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

import docker
from docker.types import Mount
import pytest
import time
import logging

from server import MQTTServer

logger = logging.getLogger(__name__)
logger.setLevel(level=logging.INFO)


@pytest.fixture
def spinup_mqtt_broker():
    # TODO - also spin up the test server
    client = docker.from_env()
    mqtt_broker = client.containers.run(
        "eclipse-mosquitto",
        [
            # "-p",
            # "1883:1883",
            # "-v",
            # "mosquitto.conf:/mosquitto/config/mosquitto.conf",
        ],
        ports={1883: 1883, 8883: 8883,},
        # volumes=["mosquitto.conf:/mosquitto/config/", "broker:/etc/ssl/certs/broker"],
        mounts=[
            Mount(
                source="/home/olepor/mendersoftware/mender-auth-azure-iot/tests/acceptance/testdata",
                target="/mosquitto/config/",
                type="bind",
            ),
            Mount(
                source="/home/olepor/mendersoftware/mender-auth-azure-iot/tests/acceptance/broker/",
                target="/etc/ssl/certs/broker/",
                type="bind",
            ),
        ],
        detach=True,
    )
    yield mqtt_broker
    # TODO - run as a teardown method
    mqtt_broker.stop()


@pytest.fixture
def spinup_mqtt_iot_hub_mock_server():
    server = MQTTServer().spin()
    yield server
    server.teardown()
