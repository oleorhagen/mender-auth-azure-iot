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

import logging
import os
import time

import docker
import pytest
from docker import APIClient
from docker.models.containers import Container
from docker.types import Mount
from server import MQTTServer

logger = logging.getLogger(__name__)
logger.setLevel(level=logging.INFO)


def get_health(container: Container):
    api_client = APIClient()
    inspect_results = api_client.inspect_container(container.name)
    return inspect_results["State"]["Health"]["Status"]


@pytest.fixture
def spinup_mqtt_broker():
    print(os.getenv("CI_PROJECT_DIR"))
    client = docker.from_env()
    mqtt_broker = client.containers.run(
        "eclipse-mosquitto",
        ports={1883: 1883, 8883: 8883,},
        mounts=[
            Mount(
                source=f"{os.getenv('CI_PROJECT_DIR')}/tests/acceptance/testdata",
                target="/mosquitto/config/",
                type="bind",
            ),
            Mount(
                source=f"{os.getenv('CI_PROJECT_DIR')}/tests/acceptance/broker/",
                target="/etc/ssl/certs/broker/",
                type="bind",
            ),
        ],
        detach=True,
        healthcheck={
            "Test": ["CMD", "mosquitto_sub", "-t", "$SYS/#", "-C", "1"],
            "Interval": 1000000 * 500,  # 500 ms
            "Timeout": 1000000 * 5 * 1000,  # 5 seconds
            "Retries": 3,
            "StartPeriod": 1000000 * 5 * 1000,  # 5 seconds
        },
    )
    while not get_health(mqtt_broker) == "healthy":
        print("Waiting for the container to become healty...")
        time.sleep(3)
    yield mqtt_broker
    mqtt_broker.stop()


@pytest.fixture
def spinup_mqtt_iot_hub_mock_server():
    server = MQTTServer()
    server.spin()
    while not server.healthy():
        print("Waiting for the server to become healthy...")
        time.sleep(3)
    return server
