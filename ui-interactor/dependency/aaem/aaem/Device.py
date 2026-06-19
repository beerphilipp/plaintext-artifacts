from multiprocessing import context
import subprocess
import time
import re
import os
from urllib.parse import non_hierarchical
from aaem.adb.ADBLogger import ADBLogger
import aaem.adb.adb as adb
import aaem.avd.avd as avd
import fcntl
import uuid
from aaem.constants import ANDROID_ADB_BIN
from contextlib import contextmanager

from typing import Union

import logging

logger = logging.getLogger(__name__)

class Device:

    query: str = None
    lock_file: str = None
    serial: str = None
    avd_name: str = None
    is_emulator: bool = False
    snapshot: str = None
    
    def __init__(self, query: str, snapshot: str = None) -> None:
        self.query = query

    def __enter__(self) -> None:
        """
        Aquire the device for exclusive use.
        """
        if (self.lock_file is not None):
            raise Exception("A device is already locked")
        
        matching_serials = []
        matching_avds = []
        if self.query is None:
            self.query = "*"
        separated_query = self.query.split(",")
        
        for part in separated_query:
            if part.startswith("avd-"):
                avd_name = part.split("avd-")[1].strip()
                avds = avd.get_avds_matching_prefix(avd_name)
                for a in avds:
                    serial = avd.get_serial_for_avd(a)
                    if serial:
                        matching_serials.append(serial)
                    else:
                        matching_avds.append("avd-" + a)
            else:
                serial = part.strip()
                serials = adb.get_adb_devices_query(serial)
                matching_serials.extend(serials)
        
        # Always prefer serials over AVD names as for serials we are sure that the device is running
        all_possible_devices = matching_serials + matching_avds
        all_possible_devices = list(set(all_possible_devices))  # Remove duplicates

        for device in all_possible_devices:
            lock_file = None
            if (device.startswith("emulator-") or device.startswith("avd-")):
                avd_name = None
                if device.startswith("avd-"):
                    avd_name = device.split("avd-")[1].strip()
                else:
                    # This is an emulator, so we have to get the AVD name behind it
                    avd_name = adb.get_emulator_id(device)
                
                cleaned_avd_name = re.sub(r'[^\w\.-]', '_', avd_name)
                lock_file_path = f"/tmp/aaem-{cleaned_avd_name}.lock"
                lock_file = open(lock_file_path, "w")
                try:
                    fcntl.flock(lock_file, fcntl.LOCK_EX | fcntl.LOCK_NB)
                    self.lock_file = lock_file
                    # We successfully locked the device
                    self.avd_name = avd_name
                    self.is_emulator = True
                    break
                except BlockingIOError:
                    continue
            else:
                # This is not an AVD, but a physical device
                lock_file_path = f"/tmp/aaem-{device}.lock"
                lock_file = open(lock_file_path, "w")
                try:
                    fcntl.flock(lock_file, fcntl.LOCK_EX | fcntl.LOCK_NB)
                    self.lock_file = lock_file
                    self.serial = device
                    self.is_emulator = False
                    break
                except BlockingIOError:
                    continue

        if (self.lock_file is None):
            raise Exception("Could not lock any device matching the query: " + self.query)    
        self.__prepare()
        return self

    def __exit__(self, exc_type, exc_value, traceback) -> None:
        """
        Release the device after use.
        """
        if (self.lock_file is None):
            return

        fcntl.flock(self.lock_file, fcntl.LOCK_UN)
        self.lock_file.close()
        os.remove(self.lock_file.name)
        return

    def __prepare(self) -> None:
        """
        Prepares the device for experiments

        :param snapshot: (optional) The name of the snapshot to restore
        :raises Exception: If the device could not be prepared
        """
        logger.debug(f"Preparing device {self.serial} for experiments")
        if not self.is_emulator:
            return True
        
        # Check if the emulator is already running. If it is not, start it.
        if not avd.is_avd_running(self.avd_name):
            logger.debug(f"AVD {self.avd_name} is not running. Starting it now.")
            started: bool = avd.start_avd_single(self.avd_name)
            if not started:
                logger.error(f"Could not start AVD {self.avd_name}")
                raise Exception(f"Could not start AVD {self.avd_name}")
            logger.debug(f"AVD {self.avd_name} started successfully. Serial: {self.serial}")
            

        if (self.serial is None):
            self.serial = avd.get_serial_for_avd(self.avd_name)

        if (self.serial is None):
            logger.error(f"Could not get serial for AVD {self.avd_name}")
            raise Exception(f"Could not get serial for AVD {self.avd_name}")
        
        if self.snapshot is not None:
            logger.debug(f"Restoring snapshot {self.snapshot} for AVD {self.avd_name}")
            # Restore the AVD to a previously defined snapshot
            reset = avd.reset_to_snapshot(self.serial, self.snapshot)
            if not reset:
                logger.error(f"Could not reset AVD {self.avd_name} to snapshot {self.snapshot}")
                raise Exception(f"Could not reset AVD {self.avd_name} to snapshot {self.snapshot}")

        device_ready = adb.block_until_device_ready(self.serial)
        if not device_ready:
            logger.error(f"Device {self.serial} is not ready")
            raise Exception(f"Device {self.serial} is not ready")
        
        if not adb.root_adb(self.serial):
            logger.error(f"Could not root device {self.serial}")
            raise Exception(f"Could not root device {self.serial}")
        
        return True
    
    def install_apk(self, apk: Union[str, list[str]]) -> bool:
        """
        Installs an APK or split APK on the device.
        
        :param apk: The path to the APK to install, or a list of APK paths for split APKs.
        :return: True if installation succeeded, False otherwise.
        """
        if isinstance(apk, str):
            return adb.install_apk(self.serial, apk)
        elif isinstance(apk, list):
            if len(apk) <= 1:
                return adb.install_apk(self.serial, apk[0])
            return adb.install_split_apk(self.serial, apk)
        else:
            raise ValueError("apk must be a string or a list of strings")

    def push_file(self, source: str, destination: str, timeout: int = 5) -> bool:
        """
        Pushes a file to the device
        :param source: The path to the file to push
        :param destination: The destination path on the device
        """
        return adb.start_activity(self.serial, source, destination, timeout)

    def pull_file(self, source: str, destination: str, timeout: int = 5) -> bool:
        """
        Pulls a file from the device
        :param source: The path to the file to pull
        :param destination: The destination path on the host
        """
        return adb.pull_file(self.serial, source, destination, timeout)
    
    def get_current_activity(self) -> str | None:
        """
        Returns the current foreground activity on the device
        :return: The current activity or None if it could not be determined
        """
        return adb.get_current_activity(self.serial)

    def execute_command(self, command: list[str], timeout: int = None) -> subprocess.CompletedProcess:
        return adb.execute_command(self.serial, command, timeout)
    
    def execute_command_nb(self, command: list[str]) -> subprocess.Popen:
        return adb.execute_command_nb(self.serial, command)
    
    def get_adb_logger(self, tag: str = None, level: str = None, use_json = True, support_split = True, split_identifier: str = None) -> ADBLogger:
        return ADBLogger(self.serial, tag, level, use_json, support_split, split_identifier)
    
    def get_private_file_content(self, package_name: str, file_name: str, retries=5) -> str | None:
        logger.info(f"Getting private file content for {package_name}/{file_name} on device {self.serial}")
        if self.is_emulator:
            result = subprocess.run(
                ["adb", "-s", self.serial, "exec-out", "cat", f"/data/data/{package_name}/files/{file_name}"],
                stdout=subprocess.PIPE, stderr=subprocess.PIPE
            )
        else:
            result = subprocess.run(
                ["adb", "-s", self.serial, "shell", "su", "-c", f"cat /data/data/{package_name}/files/{file_name}"],
                stdout=subprocess.PIPE, stderr=subprocess.PIPE
            )

        if result.returncode == 0:
            self.__remove_adb_file(package_name, file_name)
            return result.stdout.decode("utf-8", errors="replace")
        else:
            logger.warning(f"Could not get private file content for {package_name}/{file_name} on device {self.serial}: {result.stderr.decode('utf-8')}, retries left: {retries}")
            logger.warning(result.stderr.decode('utf-8'))
            if retries > 0:
                time.sleep(0.1)
                return self.get_private_file_content(package_name, file_name, retries - 1)
        
        logger.error(f"Failed to get private file content for {package_name}/{file_name} on device {self.serial} after retries")
        logger.error(result.stderr.decode('utf-8'))
        self.__remove_adb_file(package_name, file_name)
        return None
    
    def __remove_adb_file(self, package_name: str, file_name: str) -> bool:
        if self.is_emulator:
            result = subprocess.run(
                ["adb", "-s", self.serial, "shell", "rm", f"/data/data/{package_name}/files/{file_name}"],
                stdout=subprocess.PIPE, stderr=subprocess.PIPE
            )
        else:
            result = subprocess.run(
                ["adb", "-s", self.serial, "shell", "su", "-c", f"rm /data/data/{package_name}/files/{file_name}"],
                stdout=subprocess.PIPE, stderr=subprocess.PIPE
            )

        return result.returncode == 0
    
    def get_file(self, device_path: str, host_path: str) -> bool:
        if self.is_emulator:
            raise NotImplementedError("Pulling files from emulators is not implemented yet.")
        else:

            result = subprocess.run(
                ["adb", "-s", self.serial, "exec-out", "su", "-c", f"cat {device_path}"], stdout=subprocess.PIPE, check=True
            )
            if result.returncode == 0:
                with open(host_path, 'wb') as f:
                    f.write(result.stdout)
                return True
            else:
                logger.error(f"Could not pull file {device_path} from device {self.serial} using exec-out.")
                # get stderr for debugging
                logger.error(result.stderr.decode('utf-8'))
                return False

            # create a temporary uuid file on /sdcard to pull the file via adb
            temp_file = f"/sdcard/{uuid.uuid4()}.tmp"
            result = subprocess.run(
                ["adb", "-s", self.serial, "shell", "su", "-c", f"cat {device_path}", ">", temp_file],
                stdout=subprocess.PIPE, stderr=subprocess.PIPE
            )
            if result.returncode != 0:
                return False
            result = subprocess.run(
                ["adb", "-s", self.serial, "pull", temp_file, host_path],
                stdout=subprocess.PIPE, stderr=subprocess.PIPE
            )
            if result.returncode != 0:
                return False
            # remove the temporary file
            subprocess.run(
                ["adb", "-s", self.serial, "shell", "su", "-c", f"rm {temp_file}"],
                stdout=subprocess.PIPE, stderr=subprocess.PIPE
            )
            return True
    
    def start_activity(self, package_name: str, activity_name: str, data: str = None) -> bool:
        """
        Opens an activity on the device.

        :param package_name: The package name of the app.
        :param activity_name: The name of the activity to open.
        :param data: (optional) Data to pass to the activity.
        :return: True if the activity was opened successfully, False otherwise.
        """
        return adb.start_activity(self.serial, package_name, activity_name, data)

class DeviceAppInteractionContext(Device):
    """
    Extends Device to provide a context manager for app interactions.
    
    Settings:
    {
    "reset_third_party_apps": bool, # Whether to uninstall all 3rd party apps not in allowed_3rd_party_apps on enter and exit
    "allowed_3rd_party_apps": list[str], # List of package names that should not be uninstalled if reset_third_party_apps is True
    "connect_to_wifi": bool,
    "wifi": {
        "ssid": str, # SSID of the WiFi network to connect to
        "password": str, # Password of the WiFi network to connect to
        "security": str, # Security type of the WiFi network (currently, only wpa is supported)}
    }

    """

    package_name: str = None

    def __init__(self, query: str, snapshot: str = None, apks: Union[str, list[str]] = None, package_name = None, settings: dict = {}) -> None:
        super().__init__(query, snapshot)
        self.apks = apks
        self.package_name = package_name
        self.settings = settings

    def __get_installed_3rd_party_apps(self) -> list[str]:
        ##
        result = subprocess.run(
            ["adb", "-s", self.serial, "shell", "pm", "list", "packages", "-3"],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )
        if result.returncode != 0:
            return None
        packages = []
        for line in result.stdout.decode("utf-8").splitlines():
            line = line.strip()
            if line.startswith("package:"):
                package = line.split("package:")[1]
                packages.append(package)
        return packages
    
    def __connect_to_wifi(self, ssid: str, password: str, security: str = "wpa") -> bool:
        logger.info(f"Connecting to WiFi network {ssid} on device {self.serial}")

        result = subprocess.run(
            ["adb", "-s", self.serial, "shell", "svc", "wifi", "enable"],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )
        if result.returncode != 0:
            logger.error(f"Could not enable WiFi on device {self.serial}: {result.stderr.decode('utf-8')}")
            return False

        result = subprocess.run(
            ["adb", "-s", self.serial, "shell", "cmd", "wifi", "connect-network", ssid, security, password],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )
        if result.returncode != 0:
            logger.error(f"Could not connect to WiFi network {ssid} on device {self.serial}: {result.stderr.decode('utf-8')}")
            return False
        else:
            logger.info(f"Connected to WiFi network {ssid} on device {self.serial}")
            return True
        
    def __enter__(self):
        super().__enter__()

        # apply the settings

        if self.settings.get("connect_to_wifi", False):
            wifi_settings = self.settings.get("wifi", {})
            ssid = wifi_settings.get("ssid", None)
            password = wifi_settings.get("password", None)
            security = wifi_settings.get("security", "wpa")
            if ssid is not None and password is not None:
                self.__connect_to_wifi(ssid, password, security)
            else:
                logger.warning("WiFi settings are incomplete. Skipping WiFi connection.")

        if self.settings.get("reset_third_party_apps", False):
            allowed_third_party_apps = self.settings.get("allowed_3rd_party_apps", None)
            if not allowed_third_party_apps is None:
                installed_third_party_apps = self.__get_installed_3rd_party_apps()
                for app in installed_third_party_apps:
                    if app not in allowed_third_party_apps:
                        adb.uninstall_app(self.serial, app)
            else:
                logger.warning("No allowed_3rd_party_apps specified, but reset_third_party_apps is True. Skipping uninstallation of 3rd party apps.")

        # go to home
        if self.apks:
            logger.info(f"Installing APK(s) {self.apks} on device {self.serial}")
            if isinstance(self.apks, str):
                self.install_apk(self.apks)
                logger.info("Single APK installed")
            elif isinstance(self.apks, list):
                self.install_apk(self.apks)
                logger.info("Split APKs installed")
            else:
                raise ValueError("apks must be a string or a list of strings")
        adb.execute_command(self.serial, ["input", "keyevent", "KEYCODE_HOME"])
        adb.execute_command(self.serial, ["settings", "put", "system", "screen_off_timeout", "2147483647"])
        return self
    
    def __exit__(self, exc_type, exc_value, traceback):
        super().__exit__(exc_type, exc_value, traceback)
        if (self.package_name):
            adb.uninstall_app(self.serial, self.package_name)

        adb.execute_command(self.serial, ["input", "keyevent", "KEYCODE_HOME"])

