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
import argparse
import logging
import logging.handlers
import time
import random
import os
import asyncio

from azure.iot.device import IoTHubDeviceClient

import daemon.identity as identity
import daemon.config as config

log = logging.getLogger()

DEVICE_UPDATE_INTERVAL = 10
JWT_TOKEN = ""
CACHED_TWIN_DATA = {}


def send_message(device_client, device_identity):
    # send new reported properties
    reported_properties = {
        "temperature": random.randint(320, 800) / 10,
        "device_id": device_identity,
    }
    log.info(
        "Setting reported temperature to {}".format(reported_properties["temperature"])
    )
    device_client.patch_twin_reported_properties(reported_properties)


def get_message(device_client):
    # get the twin
    twin = device_client.get_twin()
    log.info("Twin document:")
    log.info("{}".format(twin))
    return twin


def run_daemon(args):
    global JWT_TOKEN
    global CACHED_TWIN_DATA
    connection_string = config.load("azure.json").ConnectionString
    ca_cert = "tests/acceptance/broker/server.crt"
    certfile = open(ca_cert)
    root_ca_cert = certfile.read()
    device_client = IoTHubDeviceClient.create_from_connection_string(
        connection_string, server_verification_cert=root_ca_cert
    )
    device_identity = identity.aggregate("/home/olepor/testaggregation")
    log.info(f"Device ID: {device_identity}")
    device_client.connect()
    print("Connected to the IoT Hub")
    while True:
        log.info("Getting twin...")
        twin = get_message(device_client)
        log.info(f"JWT {JWT_TOKEN}")
        JWT_TOKEN = twin.get("JWT", "")
        # log.info(f"Cached data: {CACHED_TWIN_DATA}")
        # if CACHED_TWIN_DATA != twin:
        #     CACHED_TWIN_DATA = twin
        # log.info("Sending twin report...")
        # send_message(device_client, device_identity)
        # TODO - get once an hour
        time.sleep(DEVICE_UPDATE_INTERVAL)


def setup_logging(args):
    handlers = []
    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(
        logging.Formatter(
            datefmt="%Y-%m-%d %H:%M:%S",
            fmt="%(name)s %(asctime)s %(levelname)-8s %(message)s",
        )
    )
    handlers.append(stream_handler)
    level = {
        "debug": logging.DEBUG,
        "info": logging.INFO,
        "warning": logging.WARNING,
        "error": logging.ERROR,
        "critical": logging.CRITICAL,
    }.get(args.log_level, logging.INFO)
    syslogger = (
        logging.NullHandler() if args.no_syslog else logging.handlers.SysLogHandler()
    )
    handlers.append(syslogger)
    if args.log_file:
        handlers.append(logging.FileHandler(args.log_file))
    logging.handlers = handlers
    log.setLevel(level)
    for handler in handlers:
        log.addHandler(handler)
    log.info(f"Log level set to {logging.getLevelName(level)}")


def main(testargs=None):
    parser = argparse.ArgumentParser(
        prog="mender-auth-azure-iot",
        description="""mender-auth-azure-iot integrates the mender daemon with the Azure IoT Hub -
    tasks performed by the daemon (see list of COMMANDS below).""",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    #
    # Commands
    #
    subcommand_parser = parser.add_subparsers(title="COMMANDS")
    daemon_parser = subcommand_parser.add_parser(
        "daemon", help="Start the client as a background service."
    )
    daemon_parser.set_defaults(func=run_daemon)
    #
    # Options
    #
    global_options = parser.add_argument_group("Global Options")
    global_options.add_argument(
        "--log-file", "-L", help="FILE to log to.", metavar="FILE"
    )
    global_options.add_argument(
        "--log-level", "-l", help="Set logging to level.", default="info"
    )
    global_options.add_argument(
        "--no-syslog",
        help="Disble logging to syslog.",
        default=False,
        action="store_true",
    )
    global_options.add_argument(
        "--version", "-v", help="print the version", default=False, action="store_true"
    )
    args = parser.parse_args(testargs)
    setup_logging(args)
    if args.version:
        run_version(args)
        return
    if "func" not in vars(args):
        parser.print_usage()
        return
    if not testargs:
        args.func(args)


if __name__ == "__main__":
    main()
