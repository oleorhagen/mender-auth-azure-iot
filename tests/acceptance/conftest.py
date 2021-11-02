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

# import pytest
# import docker


# @pytest.fixture
# def spinup_mqtt_broker():
#     client = docker.from_env()
#     mqtt_broker = client.containers.run(
#         "eclipse-mosquitto",
#         [
#             # "-p",
#             # "1883:1883",
#             # "-v",
#             # "mosquitto.conf:/mosquitto/config/mosquitto.conf",
#         ],
#         ports={1883: 1883},
#         volumes=["mosquitto.conf:/mosquitto/config/"],
#         detach=True,
#     )
#     yield mqtt_broker
#     # TODO - run as a teardown method
#     mqtt_broker.stop()
import pytest
import functools
import time
import e2e_settings
import logging
from utils import create_client_object
from service_helper_sync import ServiceHelperSync
from azure.iot.device.iothub import IoTHubDeviceClient, IoTHubModuleClient

logger = logging.getLogger(__name__)
logger.setLevel(level=logging.INFO)


@pytest.fixture(scope="function")
def brand_new_client(
    device_identity, client_kwargs, service_helper, device_id, module_id
):
    service_helper.set_identity(device_id, module_id)

    client = create_client_object(
        device_identity, client_kwargs, IoTHubDeviceClient, IoTHubModuleClient
    )

    yield client

    client.shutdown()


@pytest.fixture(scope="function")
def client(brand_new_client):
    client = brand_new_client

    client.connect()

    yield client


@pytest.fixture(scope="module")
def service_helper():
    service_helper = ServiceHelperSync()
    time.sleep(3)
    yield service_helper
    service_helper.shutdown()
