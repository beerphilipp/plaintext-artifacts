import click
import sys
import os
import signal
import threading

shutdown_event = threading.Event()

from danalyzer.monkey.NewMonkeyRunner import MonkeyRunner
from danalyzer.manual.ManualRunner import ManualRunner
from aaem.Device import DeviceAppInteractionContext

from loguru import logger

logger.add(sys.stderr, level="ERROR")
logger.add(sys.stdout, level="INFO")

ALLOWED_3RD_PARTY_APPS = [
    "com.google.android.safetycore",
    "com.google.android.webview.dev",
    "com.google.android.contactkeys",
    "com.topjohnwu.magisk",
    "com.google.android.apps.credentialmanager",
    "com.google.android.webview.beta",
    "com.android.adbkeyboard"
]


def handle_sigterm(signum, frame):
    print("Received SIGTERM, shutting down gracefully...")
    shutdown_event.set()

signal.signal(signal.SIGTERM, handle_sigterm)
signal.signal(signal.SIGINT, handle_sigterm)

@click.group()
def cli():
    logger.info("Starting CLI for danalyzer")
    pass

def common_options(f):
    """Decorator to add common options to the command."""
    f = click.option("-d", "--device", help="The device to run the test on. This can be (1) a single device ID, (2) a comma-separated list of device IDs, or (3) an AVD prefix (e.g., 'avd-*').")(f)
    f = click.option("--snapshot", help="NOT SUPPORTED RIGHT NOW. The name of the snapshot to restore before running the test if an AVD is used.")(f)
    f = click.option("-a", "--app", help="The path to the app to test. If the app is part of a split APK, provide the folder containing all APKs.", required=True)(f)
    f = click.option("-o", "--out", help="The directory to store the output", required=True)(f)
    return f

@cli.command("monkey", help="Run with Monkey")
@common_options
@click.option("-t", "--duration", help="The duration of the test run in seconds", required=True, type=int)
@click.option("-c", "--config-dir", help="The directory containing the intent configuration files", default=None)
def monkey(device, snapshot, app, out, duration, config_dir):
    click.echo(f"Running Monkey on device {device}")
    click.echo(f"   Snapshot: {snapshot}")
    click.echo(f"   Duration: {duration}")
    click.echo(f"   App: {app}")
    click.echo(f"   Output: {out}")
    apks = __get_apks(app)
    base_apk = __get_base_apk(apks)
    package_name = __get_package_name(base_apk)

    settings = {
        "reset_third_party_apps": True,
        "allowed_3rd_party_apps": ALLOWED_3RD_PARTY_APPS,
        "connect_to_wifi": True,
        "wifi": {
            "ssid": "",
            "password": "",
            "security": ""
        }
    }
    
    package_dir = os.path.join(config_dir, package_name)
    intent_fuzzing_file = os.path.join(package_dir, f"{package_name}-fastbot-config.json")
    if not os.path.exists(intent_fuzzing_file):
        logger.error(f"Intent fuzzing file not found: {intent_fuzzing_file}")
        raise Exception(f"Intent fuzzing file not found: {intent_fuzzing_file}")

    with DeviceAppInteractionContext(device, apks=apks, package_name=package_name, settings=settings) as d:
        logger.info(f"Running Monkey on device {d.serial} with snapshot {snapshot}, duration {duration}, app {app}, output {out}")
        MonkeyRunner(device=d, package_name=package_name, out=out, duration=duration, shutdown_event=shutdown_event, intent_fuzzing_file=intent_fuzzing_file).start_on_device()

@cli.command("manual", help="Run manually")
@common_options
@click.option("-t", "--duration", help="The duration of the test run in seconds", required=True, type=int)
def manual(device, snapshot, app, out, duration):
    click.echo(f"Running manual on device {device}")
    click.echo(f"   Snapshot: {snapshot}")
    click.echo(f"   Duration: {duration}")
    click.echo(f"   App: {app}")
    click.echo(f"   Output: {out}")
    apks = __get_apks(app)
    base_apk = __get_base_apk(apks)
    package_name = __get_package_name(base_apk)

    settings = {
        "reset_third_party_apps": True,
        "allowed_3rd_party_apps": ALLOWED_3RD_PARTY_APPS,
        "connect_to_wifi": True,
        "wifi": {
            "ssid": "",
            "password": "",
            "security": ""
        }
    }

    with DeviceAppInteractionContext(device, apks=apks, package_name=package_name, settings=settings) as d:
        logger.info(f"Running Monkey on device {d.serial} with snapshot {snapshot}, duration {duration}, app {app}, output {out}")
        ManualRunner(device=d, package_name=package_name, out=out, duration=duration, shutdown_event=shutdown_event).start_on_device()

def __get_apks(app_path: str) -> list[str]:
    if os.path.isdir(app_path):
        apk_paths = [os.path.join(app_path, f) for f in os.listdir(app_path) if f.endswith(".apk")]
        if not apk_paths:
            raise Exception(f"No APKs found in {app_path}")
        return apk_paths
    elif os.path.isfile(app_path) and app_path.endswith(".apk"):
        return [app_path]

def __get_package_name(apk_path: str):
    file_name = os.path.basename(apk_path)
    first_part = file_name.split(".apk")[0]
    if (first_part.endswith("_merged")):
        return first_part.split("_merged")[0]
    return first_part

def __get_base_apk(apk_paths: list[str]):
    apk_paths.sort(key=len)
    return apk_paths[0]

if __name__ == "__main__":
    cli()