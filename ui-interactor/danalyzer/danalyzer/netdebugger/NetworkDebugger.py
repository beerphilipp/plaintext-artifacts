from aaem.Device import Device
import logging
import time

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

import posixpath

from threading import Thread
from time import sleep

class NetworkDebugger:
    
    def __init__(self, device: Device, package_name: str):
        self.network_log_entries = []
        self.package_name = package_name
        self.device = device
        self.network_file_name = f"netlog.json"
        self.app_directory = self.__get_app_directory()
        self.device_network_path = posixpath.join(
            self.app_directory, 'app_webview',
            self.network_file_name)
        
        print(f"Network log will be saved to: {self.device_network_path}")
        self.__close_app()
        time.sleep(1)
        self.__set_network_log_path()
        logger.info(f"Initialized NetworkDebugger for package {self.package_name} on device {self.device.serial}")
        time.sleep(2)
        
        self.runs = 0
        self.monitor_thread = Thread(target=self.__monitor_network_log, daemon=True)
        self.monitor_thread.start()
        self.running = False
        

    def __monitor_network_log(self):
        logger.info(f"Starting network log monitoring for package {self.package_name}")
        self.running = False
        while True:
            result = self.device.execute_command(["pidof", self.package_name])
            if result.returncode == 1 and self.running == True:
                self.running = False
                logger.info(f"App {self.package_name} is not running. Moving the network log file.")
                self.maybe_copy_network_log()
                self.runs += 1
            elif result.returncode == 1 and self.running == False:
                pass
            else:
                self.running = True
            time.sleep(0.2)
    
    def __delete_existing_log(self):
        self.__remove_network_log()
    
    def __get_app_directory(self):
        result = self.device.execute_command([
            f"dumpsys package {self.package_name} | grep 'dataDir=' | sed 's/^ *dataDir=//'"
        ])
        # get the stdout from the result
        location = result.stdout.strip().decode('utf-8')
        if result.returncode != 0:
            logger.error(f"Failed to get app directory for package {self.package_name}")
            raise Exception(f"Failed to get app directory for package {self.package_name}")
        return location

    def __set_network_log_path(self):
        FLAG_FILE="/data/local/tmp/webview-command-line"
        result = self.device.execute_command([f"echo '_ --log-net-log={self.device_network_path}' > {FLAG_FILE}"])
        if result.returncode != 0:
            logger.error(f"Failed to set network log path for package {self.package_name}")
            raise Exception(f"Failed to set network log path for package {self.package_name}")

    def get_network_log(self, host_path: str) -> bool:
        logger.info(f"Closing the app {self.package_name} to finalize network log")
        self.__close_app()
        time.sleep(2)
        success = True
        for i in range(self.runs):
            logger.info(f"Retrieving network log run {i+1}/{self.runs} for package {self.package_name}")
            run_host_path = f"{host_path}-{i}"
            if not self.__get_file(f"{self.device_network_path}-{i}", run_host_path):
                logger.error("Failed to get network log from device")
                success = False
            if not self.__remove_network_log(f"{self.device_network_path}-{i}"):
                logger.error("Failed to remove network log from device")
        
        self.monitor_thread.join(timeout=1)
        return success
    
    def maybe_copy_network_log(self) -> bool:
        self.device.execute_command(["su", "-c", f"mv {self.device_network_path} {self.device_network_path}-{self.runs}"])
    
    def __close_app(self):
        self.device.execute_command([f"am force-stop {self.package_name}"])

    def __get_file(self, network_log, host_path: str) -> bool:
        return self.device.get_file(network_log, host_path)

    def __remove_network_log(self, network_log: str) -> bool:
        return self.device.execute_command(["su", "-c", f"rm {network_log}"])