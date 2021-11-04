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
import json
import logging
from typing import Optional

log = logging.getLogger(__name__)


class NoConfigurationFileError(Exception):
    pass


class Config:
    """A dictionary for storing Mender configuration values"""

    ConnectionString = ""

    def __init__(self, local_conf: dict):
        vals = {**local_conf}
        log.debug("mender-auth-azure-iot configuration values:")
        for k, v in vals.items():
            if k == "ConnectionString":
                log.debug(f"ConnectionString: {v}")
                self.ConnectionString = v
            else:
                log.error(f"The key {k} is not recognized by the azure auth daemon")


def load(local_path: str) -> Optional[Config]:
    """Read and return the merged configuration from the config file"""
    log.info("Loading the configuration file...")
    log.debug(f"From path: {local_path}")
    local_conf = None
    try:
        with open(local_path, "r") as fh:
            local_conf = json.load(fh)
    except FileNotFoundError:
        log.info(f"Configuration file: '{local_path}' not found")
        raise NoConfigurationFileError
    return Config(local_conf=local_conf or {})
