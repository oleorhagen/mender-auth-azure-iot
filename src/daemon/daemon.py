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
import time
import os
import asyncio
from azure.iot.device.aio import IoTHubDeviceClient



async def send_message():
    # Fetch the connection string from an enviornment variable
    # TODO - get this from the configuration file
    conn_str = os.getenv("IOTHUB_DEVICE_CONNECTION_STRING")

    # Create instance of the device client using the authentication provider
    device_client = IoTHubDeviceClient.create_from_connection_string(conn_str)

    # Connect the device client.
    await device_client.connect()

    # Send a single message
    print("Sending message...")
    await device_client.send_message("This is a message that is being sent")
    print("Message successfully sent!")

    # finally, shut down the client
    await device_client.shutdown()

async def get_message():

    conn_str = os.getenv("IOTHUB_DEVICE_CONNECTION_STRING")
    device_client = IoTHubDeviceClient.create_from_connection_string(conn_str)

    # connect the client.
    device_client.connect()

    # get the twin
    twin = device_client.get_twin()
    print("Twin document:")
    print("{}".format(twin))

    # Finally, shut down the client
    device_client.shutdown()

async def main():

    while True:

        # TODO - get once an hour
        # TODO - get the device identity, and send it with the data

        get_message()

        send_message()

        time.sleep(10)


if __name__ == "__main__":
    asyncio.run(main())
