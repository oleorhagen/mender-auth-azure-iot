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

import re

from paho.mqtt import client as mqtt_client


broker = "localhost"
port = 1883
topic = "$iothub/twin/PATCH/#"
# generate client ID with pub prefix randomly
client_id = f"python-mqtt-{random.randint(0, 1000)}"
# username = 'emqx'
# password = 'public'


def connect_mqtt():
    def on_connect(client, userdata, flags, rc):
        if rc == 0:
            print("Connected to MQTT Broker!")
        else:
            print("Failed to connect, return code %d\n", rc)

    client = mqtt_client.Client(client_id)
    # client.username_pw_set(username, password)
    client.on_connect = on_connect
    client.connect(broker, port)
    return client


def publish(client):
    msg_count = 0
    while True:
        time.sleep(1)
        msg = f"messages: {msg_count}"
        result = client.publish(topic, msg)
        # result: [0, 1]
        status = result[0]
        if status == 0:
            print(f"Send `{msg}` to topic `{topic}`")
        else:
            print(f"Failed to send message to topic {topic}")
        msg_count += 1


def subscribe(client: mqtt_client):
    def on_message(client, userdata, msg):
        print(f"Received `{msg.payload.decode()}` from `{msg.topic}` topic")

    client.subscribe(topic)
    client.on_message = on_message


def reply_to_twin_patch(client: mqtt_client):
    # 1. A device must first subscribe to the $iothub/twin/res/# topic to receive the operation's responses from IoT Hub.
    #
    # 2. A device sends a message that contains the device twin update to the $iothub/twin/PATCH/properties/reported/?$rid={request id} topic. This message includes a request ID value.
    #
    # 3. The service then sends a response message that contains the new ETag value for the reported properties collection on topic $iothub/twin/res/{status}/?$rid={request id}. This response message uses the same request ID as the request.
    #

    def on_device_twin_update(client, userdata, msg):
        print("in_device_twin_update...")
        print(f"Received `{msg.payload.decode()}` from `{msg.topic}` topic")
        # 2. Reply to the device with the status (204) for now
        status = 204
        m = re.search(r".*rid=(.*)", msg.topic)
        rid = m.group(1)
        client.publish(f"$iothub/twin/res/{status}/?$rid={rid}")

    topic = "$iothub/twin/PATCH/#"
    print(f"Subscribing to {topic}")
    client.subscribe(topic)
    client.on_message = on_device_twin_update
    #

    # result = client.publish(topic, msg)


def update_desired_device_twin(client: mqtt_client):
    # 1. Subscribe to $iothub/twin/GET/?$rid={request_id} from the device
    #
    # 2. Respond with the device twin data on $iothub/twin/res/{status}/?$rid={request_id}
    #
    def send_desired_device_twin(client, userdata, msg):
        print("Sending the device twin...")
        # Extract the request_id from the msg
        m = re.search(r".*rid=(.*)", msg.topic)
        rid = m.group(1)
        status = 200
        response_topic = f"$iothub/twin/res/{status}/?$rid={rid}"
        device_twin = {
            "desired": {"telemetrySendFrequency": "5m", "$version": 12},
            "reported": {
                "telemetrySendFrequency": "5m",
                "batteryLevel": 55,
                "$version": 123,
            },
        }
        import json
        data=json.dumps(device_twin)
        client.publish(response_topic, data)

    print("Listening to GET requests from the client...")
    listen_topic = "$iothub/twin/GET/#"
    client.subscribe(listen_topic)
    client.on_message = send_desired_device_twin


def run():
    client = connect_mqtt()
    client.loop_start()
    # subscribe(client)
    # publish(client)
    # reply_to_twin_patch(client)

    update_desired_device_twin(client)
    while True:
        time.sleep(5)


if __name__ == "__main__":
    run()
