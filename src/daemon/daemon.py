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
import sys
import time
from logging.handlers import SysLogHandler

from azure.iot.device import IoTHubDeviceClient  # type: ignore

from daemon._version import __version__ as package_version
from daemon.config import config
from daemon.config.config import NoConfigurationFileError
from daemon.scripts import identity
from daemon.settings.settings import PATHS as Config

log = logging.getLogger()

DEVICE_UPDATE_INTERVAL = 60 * 60


def send_message(device_client, reported_properties):
    device_client.patch_twin_reported_properties(reported_properties)


def get_message(device_client):
    twin = device_client.get_twin()
    log.info("Twin document:")
    log.info(f"{twin}")
    return twin


def run_version(_):
    print(f"version: {package_version}")


def run_daemon(args):
    jwt_token = ""
    try:
        connection_string = config.load(Config.conf_file).ConnectionString
    except NoConfigurationFileError as e:
        log.error(e)
        return 1
    if Config.server_cert != "":
        server_cert = Config.server_cert
        try:
            certfile = open(server_cert)
        except FileNotFoundError as e:
            log.error(e)
            return 1
        server_cert_raw = certfile.read()
        device_client = IoTHubDeviceClient.create_from_connection_string(
            connection_string, server_verification_cert=server_cert_raw
        )
    else:
        device_client = IoTHubDeviceClient.create_from_connection_string(
            connection_string, server_verification_cert=""
        )
    try:
        open(Config.identity_scripts)
    except FileNotFoundError as e:
        log.error(e)
        return 1
    device_identity = identity.aggregate(Config.identity_scripts)
    log.info(f"Device ID: {device_identity}")
    device_client.connect()
    log.info("Connected to the IoT Hub")
    while True:
        log.info("Getting twin...")
        twin = get_message(device_client)
        desired = twin.get("desired", None)
        if not desired:
            log.error("desired data not present in the response")
            return 1
        log.info("Sending twin report...")
        if jwt_token != desired.get("JWT", ""):
            log.info(
                "The JWT Token, or the device identity has changed in the desired vs reported state"
            )
            log.info("Resending")
            jwt_token = desired.get("JWT", "")
            send_message(
                device_client,
                reported_properties={"device_id": device_identity, "JWT": jwt_token,},
            )
        if args.stop:
            return 1
        log.info(f"Going to sleep for {DEVICE_UPDATE_INTERVAL} seconds...")
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
    syslogger = logging.NullHandler() if args.no_syslog else SysLogHandler()
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
    args.stop = False
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
    sys.exit(main())
