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


import random
import time
import pytest
import json

import re

from paho.mqtt import client as mqtt_client


class MQTTServer:

    broker = "localhost"
    port = 1883

    client_workers = []

    received_twins = []

    def __init__(self):
        pass

    def connect(self):
        def on_connect(client, userdata, flags, rc):
            if rc == 0:
                print("Connected to MQTT Broker!")
            else:
                print("Failed to connect, return code %d\n", rc)

        client_id = f"python-mqtt-server-client-{random.randint(0, 1000)}"
        client = mqtt_client.Client(client_id)
        client.on_connect = on_connect
        client.connect(self.broker, self.port)
        self.client_workers.append(client)
        return client

    def expected(self, uploads, replies):
        self.uploads = uploads
        self.replies = replies

    def reply_to_twin_patch(self):
        """1. A device must first subscribe to the $iothub/twin/res/# topic to receive
         the operation's responses from IoT Hub.

         2. A device sends a message that contains the device twin update to
         the $iothub/twin/PATCH/properties/reported/?$rid={request id} topic.
         This message includes a request ID value.

         3. The service then sends a response message that contains the new
         ETag value for the reported properties collection on topic
         $iothub/twin/res/{status}/?$rid={request id}. This response message
         uses the same request ID as the request.
        """

        client = self.connect()
        client.loop_start()

        def on_device_twin_update(client, userdata, msg):
            print("Received an update to the device twin")
            print(f"Received `{msg.payload.decode()}` from `{msg.topic}` topic")
            device_twin = json.loads(msg.payload.decode())
            self.received_twins.append(device_twin)
            # 2. Reply to the device with the status (204) for now
            status = 204
            m = re.search(r".*rid=(.*)", msg.topic)
            rid = m.group(1)
            client.publish(f"$iothub/twin/res/{status}/?$rid={rid}")

        topic = "$iothub/twin/PATCH/#"
        client.subscribe(topic)
        print(f"Subscribed to {topic}")
        client.on_message = on_device_twin_update

    def update_desired_device_twin(self):
        """1. Subscribe to $iothub/twin/GET/?$rid={request_id} from the device

         2. Respond with the device twin data on
         $iothub/twin/res/{status}/?$rid={request_id}

        """

        client = self.connect()
        client.loop_start()

        def send_desired_device_twin(client, userdata, msg):
            # Extract the request_id from the msg
            m = re.search(r".*rid=(.*)", msg.topic)
            rid = m.group(1)
            status = 200
            response_topic = f"$iothub/twin/res/{status}/?$rid={rid}"
            device_twin = self.replies
            data = json.dumps(device_twin)
            print(f"Sending the device twin:\n{data}")
            client.publish(response_topic, data)

        print("Listening to GET requests from the client...")
        listen_topic = "$iothub/twin/GET/#"
        client.subscribe(listen_topic)
        print(f"Subscribed to {listen_topic}")
        client.on_message = send_desired_device_twin

    def spin(self):

        # Handle patches to the device_twin
        self.reply_to_twin_patch()

        # Send the device_twin upon GET requests
        self.update_desired_device_twin()

        return self

    def teardown(self):
        for worker in self.client_workers:
            worker.on_disconnect = lambda a,b,c: print(f"Disconnected worker {worker} from the broker")
            worker.disconnect()


if __name__ == "__main__":
    MQTTServer().spin()
