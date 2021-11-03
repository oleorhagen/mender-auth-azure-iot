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
    print("Testing the daemon...")
    with pytest.raises(SystemExit):
        daemon.main([""])
    print("Running the daemon")
    print(f"Server: {spinup_mqtt_iot_hub_mock_server}")
    threading.Thread(target=daemon.run_daemon, args=[""], daemon=True).start()
    print("Started the daemon")
    import time
    time.sleep(10)
