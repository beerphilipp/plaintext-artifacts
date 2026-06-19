import os
import re
import tempfile
import time
import shutil
import subprocess

from aaem.UnresponsiveException import UnresponsiveException
from aaem import avd
from aaem.constants import ANDROID_ADB_BIN, ANDROID_USER_HOME
from aaem.constants import ANDROID_HOME
from aaem.constants import ANDROID_EMULATOR_BIN

import aaem.adb.adb as adb

import logging

logger = logging.getLogger(__name__)

def get_avds() -> list[str]:
    """
    Returns a list of AVDs on the device
    """
    result = subprocess.run([ANDROID_EMULATOR_BIN, "-list-avds"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    if result.returncode != 0:
        raise Exception(result.stderr.decode())

    avds = result.stdout.decode().split("\n")
    avds = list(filter(lambda x: x != "", avds))
    return avds

def stop_avd(avd_name) -> list[str]:
    """
    Stopping an AVD with the given name. If the name contains a wildcard (*), all AVDs with the given prefix will be stopped.
    :param avd_name: Name of the AVD to stop
    :return: The list of AVDs that were stopped
    """
    matching_avds = get_avds_matching_prefix(avd_name)

    running_avds = list(filter(lambda x: is_avd_running(x), matching_avds))
    
    stopped_avds = []
    for avd in running_avds:
        result = subprocess.run([ANDROID_ADB_BIN, "-s", get_serial_for_avd(avd), "emu", "kill"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        if result.returncode == 0:
            stopped_avds.append(avd)
    return stopped_avds

def start_avd_single(avd_name, timeout=60) -> bool:
    logger.debug(f"Starting AVD {avd_name}")
    started_avds = start_avd(avd_name, timeout)
    if len(started_avds) == 1 and started_avds[0] == avd_name:
        return True
    return False

def force_kill_avd(avd_name: str) -> None:
    """
    Force-kills an AVD with the given name.
    :param avd_name: Name of the AV
    """
    pgrep_result = subprocess.run(["pgrep", "-fl", "qemu-system"], capture_output=True, text=True, check=True)
    for line in pgrep_result.stdout.strip().split("\n"):
        if avd_name in line:
            pid = line.split(" ")[0]
            subprocess.run(["kill", "-9", pid], check=True)
            return


def start_avd(avd_name, timeout=60) -> list[str]:
    """
    Starts an AVD with the given name. If the name contains a wildcard (*), all AVDs with the given prefix will be started.
    Blocks until all AVDs are started.

    :param avd_name: Name of the AVD to start
    :param timeout: Timeout in seconds
    :return: The list of AVDs that were started
    """
    logger.debug(f"Starting AVD {avd_name}")
    avds_to_start = get_avds_matching_prefix(avd_name)
    avds_started = []

    for avd in avds_to_start:
        # check if this AVD is already running, but is not reachable
        if is_avd_running_low_level(avd) and not is_avd_running(avd):
            force_kill_avd(avd)

        subprocess.Popen([ANDROID_EMULATOR_BIN, "-avd", avd, "-no-snapshot-save"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    not_started = avds_to_start

    for i in range(timeout):
        not_started = list(filter(lambda x: not is_avd_running(x), not_started))
        avds_started = list(set(avds_to_start) - set(not_started))
        if len(not_started) == 0:
            break
        time.sleep(1)
    logger.debug(f"Started AVDs: {avds_started}")

    return avds_started


def is_avd_running(avd_name) -> bool:
    """
    Checks if an AVD with the given name is currently running
    :param avd_name: The name of the AVD to check
    :return: True if the AVD is running, False otherwise
    """
    logger.debug(f"Checking if AVD {avd_name} is running")
    serial = get_serial_for_avd(avd_name)
    if not serial is None:
        logger.debug(f"AVD {avd_name} is running with serial {serial}")
        return True
    
    logger.debug(f"AVD {avd_name} is not running/reachable")
    return False

def is_avd_running_low_level(avd_name: str) -> bool:
    logger.debug(f"Checking if AVD {avd_name} is running (low-level)")
    low_level_serial = get_serial_for_avd_low_level(avd_name)
    if not low_level_serial is None:
        logger.debug(f"AVD {avd_name} is running with serial {low_level_serial} (low-level)")
        return True
    
    logger.debug(f"AVD {avd_name} is not running/reachable (low-level)")
    return False


def get_serial_for_avd(avd_name) -> str:
    """
    Retrieves the the serial number of the emulator with the given AVD name.
    :param avd_name: The name of the AVD to retrieve the serial number for
    :return: The serial number of the emulator with the given AVD name or None if no emulator with the given AVD name is found
    """
    devices = adb.get_adb_devices()
    for device in devices:
        try:
            if adb.is_emulator(device):
                id = adb.get_emulator_id(device)
                if id == avd_name:
                    return device
        except UnresponsiveException:
            continue
    return None

def get_serial_for_avd_low_level(avd_name: str) -> str:
    # in case the device cannot be reached (i.e., the device is really not running or the emulator is not responding)
    # we use low-level commands to get the serial number of the device
    start_port_num = 5554
    end_port_num = 5584

    for port_num in range(start_port_num, end_port_num, 2):
        result = subprocess.run(["ps -fp $(lsof -t -i :5554)"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
        if result.returncode != 0:
            continue

        # example output:
        #   UID   PID  PPID   C STIME   TTY           TIME CMD
        # 508  4289     1   0 10:58am ttys001  1559:26.98 /Users/webview/Library/Android/sdk/emulator/qemu/darwin-aarch64/qemu-system-aarch64 -avd wvi_0 -no-snapshot-save

        # get the line that contains "-avd" and get the string after that
        lines = result.stdout.decode().split("\n")
        for line in lines:
            if "-avd " in line:
                second_part = line.split("-avd ")[1]
                current_avd_name = second_part.split(" ")[0]
                if (current_avd_name == avd_name):
                    return f"emulator-{port_num}"
                
        return None


def get_avds_matching_prefix(name) -> list[str]:
    """
    Retrieves all AVDs that match the given string (with wildcard support)
    :param name: The name of the AVD to match
    :return: A list of AVDs that match the given string
    """
    all_avds = get_avds()
    if "*" in name:
        prefix = name.split("*")[0]
        matching_avds = list(filter(lambda x: x.startswith(prefix), all_avds))
        return matching_avds
    else:
        if name in all_avds:
            return [name]
        else:
            return []

def duplicate_avd_single(base_avd_location: str, base_ini_location: str, base_avd_name: str, target_avd_name: str, force: bool):
    new_avd_location = os.path.join(ANDROID_USER_HOME, "avd", f"{target_avd_name}.avd")
    new_ini_location = os.path.join(ANDROID_USER_HOME, "avd", f"{target_avd_name}.ini")

    if os.path.exists(new_avd_location) or os.path.exists(new_ini_location):
        if force:
            shutil.rmtree(new_avd_location)
            os.remove(new_ini_location)
        else:
            print(f"AVD or INI file already exists for {target_avd_name}")
            return []

    if not os.path.exists(base_avd_location) or not os.path.exists(base_ini_location):
        print(f"Base AVD {base_avd_name} not found.")
        return []
        
    shutil.copytree(base_avd_location, new_avd_location)
    shutil.copy(base_ini_location, os.path.join(ANDROID_USER_HOME, "avd", new_ini_location))
        
    __modify_ini_file(new_ini_location, new_avd_location)
        
    config_ini_file = os.path.join(new_avd_location, "config.ini")
    __modify_config_ini_file(config_ini_file, f"{target_avd_name}")
        
    hardware_qemu_ini_file = os.path.join(new_avd_location, "hardware-qemu.ini")
    __modify_hardware_qemu_ini_file(hardware_qemu_ini_file, new_avd_location, f"{target_avd_name}")

    __delete_lock_files(new_avd_location)


def duplicate_avd(avd_name, target_name, amount: int, force: bool) -> list[str]:
    avds_location = os.path.join(ANDROID_USER_HOME, "avd")

    base_avd_location = os.path.join(avds_location, f"{avd_name}.avd")
    ini_location = os.path.join(avds_location, f"{avd_name}.ini")

    print(f"Creating {amount} AVDs with name {target_name} based on {base_avd_location}")

    for i in range(amount):
        duplicate_avd_single(base_avd_location, ini_location, avd_name, f"{target_name}_{i}", force)

    return [f"duplicated_avd_name{i}" for i in range(amount)]

def __modify_ini_file(file: str, new_avd_location: str) -> None:
    """
        Modifies the INI file to point to the new AVD location.

        :param file: The INI file to modify.
        :param new_avd_location: The new AVD location.
    """
    relative_path = os.path.relpath(new_avd_location, file)

    new_lines = []
    with open(file, 'r') as f:
        lines = f.readlines()
        for line in lines:
            if line.startswith("path="):
                new_lines.append(f"path={new_avd_location}\n")
            elif line.startswith("path.rel="):
                new_lines.append(f"path.rel={relative_path}\n")
            else:
                new_lines.append(line)
    with open(file, 'w') as f:
        f.writelines(new_lines)

def __modify_config_ini_file(file: str, new_avd_name: str) -> None:
    """
        Modifies the config INI file to include the new AVD name.

        :param file: The INI file to modify.
        :param new_avd_name: The new AVD name.
    """
    new_lines = []
    with open(file, 'r') as f:
        lines = f.readlines()
        for line in lines:
            if line.startswith("AvdId="):
                new_lines.append(f"AvdId={new_avd_name}\n")
            elif line.startswith("avd.ini.displayname="):
                new_lines.append(f"avd.ini.displayname={new_avd_name}\n")
            elif line.startswith("skin.path="):
                new_lines.append(f"skin.path={ANDROID_HOME}/skins/pixel_6_pro\n")
            else:
                new_lines.append(line)

    with open(file, 'w') as f:
        f.writelines(new_lines)

def __modify_hardware_qemu_ini_file(file: str, new_avd_location: str, new_avd_name: str) -> None:
    """
        Modifies the hardware-qemu INI file.

        :param file: The INI file to modify.
        :param new_avd_location: The new AVD location.
        :param new_avd_name: The new AVD name.
    """
    cache_partition = os.path.join(new_avd_location, "cache.img")
    kernel_path = os.path.join(ANDROID_HOME, "system-images", "android-33", "google_apis", "arm64-v8a", "kernel-ranchu")
    ramdisk_path = os.path.join(ANDROID_HOME, "system-images", "android-33", "google_apis", "arm64-v8a", "ramdisk.img")
    system_partition_init_path = os.path.join(ANDROID_HOME, "system-images", "android-33", "google_apis", "arm64-v8a", "system.img")
    vendor_parition_init_path = os.path.join(ANDROID_HOME, "system-images", "android-33", "google_apis", "arm64-v8a", "vendor.img")
    data_partition_path = os.path.join(new_avd_location, "userdata-qemu.img")
    encryption_key_partition_path = os.path.join(new_avd_location, "encryptionkey.img")

    new_lines = []
    with open(file, 'r') as f:
        lines = f.readlines()
        for line in lines:
            if line.startswith("disk.cachePartition.path ="):
                new_lines.append(f"disk.cachePartition.path = {cache_partition}\n")
            elif line.startswith("kernel.path ="):
                new_lines.append(f"kernel.path = {kernel_path}\n")
            elif line.startswith("disk.ramdisk.path ="):
                new_lines.append(f"disk.ramdisk.path = {ramdisk_path}\n")
            elif line.startswith("disk.systemPartition.initPath ="):
                new_lines.append(f"disk.systemPartition.initPath = {system_partition_init_path}\n")
            elif line.startswith("disk.vendorPartition.initPath ="):
                new_lines.append(f"disk.vendorPartition.initPath = {vendor_parition_init_path}\n")
            elif line.startswith("disk.dataPartition.path ="):
                new_lines.append(f"disk.dataPartition.path = {data_partition_path}\n")
            elif line.startswith("disk.encryptionKeyPartition.path ="):
                new_lines.append(f"disk.encryptionKeyPartition.path = {encryption_key_partition_path}\n")
            elif line.startswith("avd.name ="):
                new_lines.append(f"avd.name = {new_avd_name}\ ")
            elif line.startswith("avd.id"):
                new_lines.append(f"avd.id = {new_avd_name}\n")
            elif line.startswith("android.sdk.root ="):
                new_lines.append(f"android.sdk.root = {ANDROID_HOME}\n")
            elif line.startswith("android.avd.home ="):
                new_lines.append(f"android.avd.home = {ANDROID_USER_HOME}\n")
            else:
                new_lines.append(line)

    with open(file, 'w') as f:
        f.writelines(new_lines)

def __delete_lock_files(avd_location: str) -> None:
    """
        Deletes the lock files for the given AVD.

        :param avd_location: The location of the AVD.
    """
    lock_files = [f for f in os.listdir(avd_location) if f.endswith(".lock")]
    for lock_file in lock_files:
        os.remove(os.path.join(avd_location, lock_file))


def avd_has_snapshot(serial: str, snapshot_name: str) -> bool:
    """
    Checks if the given AVD has a snapshot with the given name

    :param serial: The serial number of the AVD
    :param snapshot_name: The name of the snapshot
    :return: True if the AVD has a snapshot with the given name, False otherwise
    """
    logger.debug(f"Checking if AVD {serial} has snapshot {snapshot_name}")
    result = subprocess.run([ANDROID_ADB_BIN, "-s", serial, "emu", "avd", "snapshot", "list"], stdout=subprocess.PIPE, text=True)
    if result.returncode:
        return False
    
    for line in result.stdout.split("\n"):
        if snapshot_name in line:
            return True
    return False


def reset_to_snapshot(serial: str, snapshot_name: str) -> bool:
    """
    Resets the AVD given by the serial number to a snapshot with the given name and waits until the AVD is ready to be used.

    :param serial: The serial number of the AVD
    :param snapshot_name: The name of the snapshot
    :return: True if the AVD was reset to the snapshot, False otherwise
    """
    logger.debug(f"Resetting AVD {serial} to snapshot {snapshot_name}")
    if not avd_has_snapshot(serial, snapshot_name):
        return False
    
    logger.debug(f"Loading snapshot {snapshot_name}")
    result = subprocess.run([ANDROID_ADB_BIN, "-s", serial, "emu", "avd", "snapshot", "load", snapshot_name], stdout=subprocess.PIPE, text=True)
    if result.returncode != 0:
        return False
    
    return adb.block_until_device_ready(serial)

def compress_avd(avd_name: str, out: str):
    """
    Compresses an AVD into a ZIP file.
    """
    avds_location = os.path.join(ANDROID_USER_HOME, "avd")
    base_avd_location = os.path.join(avds_location, f"{avd_name}.avd")
    ini_location = os.path.join(avds_location, f"{avd_name}.ini")
    with tempfile.TemporaryDirectory() as temp_dir:
        print("Copying AVD files...")
        shutil.copytree(base_avd_location, os.path.join(temp_dir, f"{avd_name}.avd"))
        print("Copying INI file...")
        shutil.copy(ini_location, os.path.join(temp_dir, f"{avd_name}.ini"))
        print("Compressing AVD...")
        shutil.make_archive(out, 'zip', temp_dir)
    print("Done!")

def decompress_avd(compressed_avd: str, new_adv_name: str) -> bool:
    """
    Decompresses an AVD from a ZIP file.
    """
    with tempfile.TemporaryDirectory() as temp_dir:
        shutil.unpack_archive(compressed_avd, temp_dir)
        # get all directories ending in .avd
        avd_dirs = [f for f in os.listdir(temp_dir) if f.endswith(".avd")]
        if len(avd_dirs) != 1:
            print(f"Found {len(avd_dirs)} AVD directories in ZIP file. Expected 1.")
            return False
        base_avd_name = os.path.basename(avd_dirs[0])[:-4]
        print(f"AVD name: {base_avd_name}")
        ini_files = [f for f in os.listdir(temp_dir) if f.endswith(".ini")]
        if len(ini_files) != 1:
            print(f"Found {len(ini_files)} INI files in ZIP file. Expected 1.")
            return False
        
        ini_file_name = os.path.basename(ini_files[0])[:-4]
        if (base_avd_name != ini_file_name):
            print(f"AVD name {base_avd_name} does not match INI file name {ini_file_name}. This is currently not supported.")
        
        base_avd_path = os.path.join(temp_dir, f"{base_avd_name}.avd")
        base_ini_path = os.path.join(temp_dir, f"{base_avd_name}.ini")

        duplicate_avd_single(
            base_avd_path,
            base_ini_path,
            base_avd_name,
            new_adv_name,
            force=False
        )

    # Now we have to figure out what kind of image and skin is used and has to be downloaded on the other machine

    # config.ini
    # skin.path
    # skin.name
    # image.sysdir.1
    