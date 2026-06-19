from aaem.UnresponsiveException import UnresponsiveException
from aaem.constants import ANDROID_ADB_BIN

import os
import time
import subprocess

import logging

logger = logging.getLogger(__name__)


def install_apk(serial: str, apk_path: str, timeout=90) -> bool:
    try:
        result = subprocess.run([ANDROID_ADB_BIN, "-s", serial, "install", "-g", apk_path], stdout=subprocess.PIPE,
                                    stderr=subprocess.PIPE, timeout=timeout)
        if result.returncode != 0:
            return False
        return True
    except subprocess.TimeoutExpired as e:
        raise UnresponsiveException(f"Device {serial} is unresponsive", e)
    
def get_current_activity(serial: str, timeout=90) -> str | None:
    try:
        result = subprocess.run([ANDROID_ADB_BIN, "-s", serial, "shell", "dumpsys", "activity", "activities"], stdout=subprocess.PIPE,
                                    stderr=subprocess.PIPE, timeout=timeout)
        if result.returncode != 0:
            return None
        for line in result.stdout.decode("utf-8").split("\n"):
            line = line.strip()
            if line.startswith("topResumedActivity="):
                activity = line.split("ActivityRecord{")[1].split(" ")[2]
                return activity
        return None
    except subprocess.TimeoutExpired as e:
        raise UnresponsiveException(f"Device {serial} is unresponsive", e)
    
def uninstall_app(serial: str, package_name: str, timeout=90) -> bool:
    try:
        result = subprocess.run([ANDROID_ADB_BIN, "-s", serial, "uninstall", package_name], stdout=subprocess.PIPE,
                                    stderr=subprocess.PIPE, timeout=timeout)
        if result.returncode != 0:
            return False
        return True
    except subprocess.TimeoutExpired as e:
        raise UnresponsiveException(f"Device {serial} is unresponsive", e)

def install_split_apk(serial: str, apk_paths: list[str], timeout=90) -> bool:
    try:
        result = subprocess.run([ANDROID_ADB_BIN, "-s", serial, "install-multiple", "-g"] + apk_paths, stdout=subprocess.PIPE,
                                    stderr=subprocess.PIPE, timeout=timeout)
        if result.returncode != 0:
            return False
        return True
    except subprocess.TimeoutExpired as e:
        raise UnresponsiveException(f"Device {serial} is unresponsive", e)
    
def get_adb_devices_query(query: str, timeout=5) -> list[str]:

    all_devices = get_adb_devices(timeout)
    
    if query.endswith("*"):
        query = query[:-1]
        return [device for device in all_devices if device.startswith(query)]
    else:
        return [device for device in all_devices if device == query]
    

def get_adb_devices(timeout=5) -> list[str]:
    """
        Returns a list of connected ADB devices.

        :return: A list of connected ADB devices.
    """
    try:
        result = subprocess.run([ANDROID_ADB_BIN, "devices"], stdout=subprocess.PIPE, text=True, timeout=timeout)
        if result.returncode:
            return []

        devices = []
        for line in result.stdout.split("\n"):
            if "List of devices" in line or not line:
                continue
            devices.append(line.split()[0])

        return devices
    except subprocess.TimeoutExpired as e:
        raise UnresponsiveException("ADB is unresponsive", e)

def is_emulator(serial: str, timeout=5) -> bool:
    """
    Checks if the given device is an emulator.

    :param serial: The serial number of the device to check.
    :timeout: The maximum time to wait for the device to respond.
    :return: True if the device is an emulator, False otherwise.
    """
    try:
        result = subprocess.run([ANDROID_ADB_BIN, "-s", serial, "emu"], stdout=subprocess.PIPE, text=True, timeout=timeout)
        if result.returncode:
            return False
        return True
    except subprocess.TimeoutExpired as e:
        raise UnresponsiveException(f"Device {serial} is unresponsive", e)

def get_emulator_id(serial: str, timeout=5) -> str:
    """
    Retrieves the ID of the emulator.

    :param serial: The serial number of the emulator.
    :return: The ID of the emulator.
    """
    if not is_emulator(serial):
        return None
    
    try:
        result = subprocess.run([ANDROID_ADB_BIN, "-s", serial, "emu", "avd", "id"], stdout=subprocess.PIPE, text=True, timeout=timeout)
        if result.returncode:
            return None
        id = result.stdout.split("\n")[0].strip()
        return id
    except subprocess.TimeoutExpired as e:
        raise UnresponsiveException(f"Device {serial} is unresponsive", e)

def root_adb(serial: str, timeout=5) -> bool:
    """
    Calls `adb root` on the device given by the serial number.

    :param serial: The serial number of the device to call `adb root` on.
    :return: True if the command was successful, False otherwise.
    """
    try:
        result = subprocess.run([ANDROID_ADB_BIN, "-s", serial, "root"], stdout=subprocess.PIPE, text=True, timeout=timeout)
        if result.returncode != 0:
            return False
        return True
    except subprocess.TimeoutExpired as e:
        raise UnresponsiveException(f"Device {serial} is unresponsive", e)

def push_file(serial: str, source: str, destination: str, timeout=5) -> bool:
    if not os.path.exists(source):
        logger.error(f"Source file {source} does not exist")
        return False
    try:
        result = subprocess.run([ANDROID_ADB_BIN, "-s", serial, "push", source, destination], stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE, timeout=timeout)
        if result.returncode != 0:
            return False
        return True
    except subprocess.TimeoutExpired as e:
        raise UnresponsiveException(f"Device {serial} is unresponsive", e)
    
def pull_file(serial: str, source_file: str, destination_file: str, timeout=5) -> bool:
    try:
        result = subprocess.run([ANDROID_ADB_BIN, "-s", serial, "pull", source_file, destination_file], stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE, timeout=timeout)
        if result.returncode != 0:
            return False
        return True
    except subprocess.TimeoutExpired as e:
        raise UnresponsiveException(f"Device {serial} is unresponsive", e)


def block_until_device_ready(serial: str, timeout: int = 60) -> bool:
    """
    Blocks until the device is ready to be used.

    :param serial: The serial number of the device to wait for.
    :param timeout: The maximum time to wait for the device to be ready.
    :return: True if the device is ready, False otherwise.
    """
    # first check if the ADB deamon is running on the device, wait up to 60 seconds
    start = time.time()
    result = subprocess.run([ANDROID_ADB_BIN, "-s", serial, "wait-for-device"], stdout=subprocess.PIPE, text=True, timeout=timeout)
    if result.returncode != 0 or time.time() - start >= timeout:
        return False

    # check if the boot is completed
    while not is_boot_completed(serial):
        if time.time() - start >= timeout:
            return False
        time.sleep(0.5)
    return True

def is_boot_completed(serial: str) -> bool:
    """
    Checks if the device has completed the boot process.

    :param serial: The serial number of the device to check.
    :return: True if the device has completed the boot process, False otherwise.
    """
    result = subprocess.run([ANDROID_ADB_BIN, "-s", serial, "shell", "getprop", "sys.boot_completed"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if result.returncode == 0 and result.stdout.decode("utf-8").strip() == "1":
        return True
    return False


def execute_command(serial: str, command: list[str], timeout: int = None) -> subprocess.CompletedProcess:
        logger.debug(f"Executing command on device {serial}: {' '.join(command)}")
        return subprocess.run(
            [ANDROID_ADB_BIN, "-s", serial, "shell"] + command,
            timeout=timeout,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )

def execute_command_nb(serial: str, command: list[str]) -> subprocess.Popen:
    """
    Executes a command on the device without blocking.

    :param serial: The serial number of the device to execute the command on.
    :param command: The command to execute.
    :return: A Popen object representing the running process.
    """
    logger.debug(f"Executing command on device {serial}: {' '.join(command)}")
    return subprocess.Popen(
        [ANDROID_ADB_BIN, "-s", serial, "shell"] + command,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )


def start_activity(serial: str, package_name: str, activity_name: str, data: str = None) -> bool:
    """
    Opens an activity on the device.

    :param serial: The serial number of the device.
    :param package_name: The package name of the app.
    :param activity_name: The name of the activity to open.
    :param data: Optional data to pass to the activity.
    :return: True if the activity was opened successfully, False otherwise.
    """
    if activity_name.startswith('.'):
        activity_name = package_name + activity_name
    command = [ANDROID_ADB_BIN, "-s", serial, "shell", "am", "start", "-n", f"{package_name}/{activity_name}"]
    if data:
        command += ["-d", data]
    
    result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if result.returncode != 0:
        return False
    return True