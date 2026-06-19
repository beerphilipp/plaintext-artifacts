import json
import subprocess
import threading
import logging
import time

from aaem import Device
from aaem.adb import adb

logger = logging.getLogger(__name__)


class ADBLogger(threading.Thread):

    reactions: list = []

    def __init__(self, device: Device, tag: str, level: str, use_json: bool = True, support_split: bool = True, split_identifier: str = None, reactions: list = [], package_name: str = None):
        super(ADBLogger, self).__init__()
        self.device: Device = device
        self.tag = tag
        self.level = level
        self.use_json = use_json
        self.support_split = support_split
        self.split_identifier = split_identifier
        self.package_name = package_name

        self.reactions = reactions
        
        self.process = None
        self._stop_event = threading.Event()

        # create a lock for the results
        self.results_lock = threading.Lock()
        self.results = []

        self.reactions = []

        if self.use_json:
            reactions.extend([
                (lambda x: True, self.create_json)
            ])
        if self.package_name:
            reactions.extend([
                (lambda x: "package" in x and x["package"] != self.package_name, self.return_none)
            ])

        self.reactions.extend(reactions)


    def create_json(self, l):
        # check if l is a dict
        if isinstance(l, dict):
            l["timestamp"] = time.time()
            return l
        try:
            l = json.loads(l)
            l["timestamp"] = time.time()
        except json.JSONDecodeError as e:
            l = "!!JSON_DECODE_ERROR!!" + l
            logger.error(f"Failed to parse the JSON {e}")
        return l
    
    def return_none(self, l):
        return None

    def _get_thread_id(self):
        if hasattr(self, '_thread_id'):
            return self._thread_id
        for id, thread in threading._active.items():
            if thread is self:
                return id


    def reset_logs(self):
        with self.results_lock:
            old_results = self.results.copy()
            self.results = []
            return old_results


    def run(self):
        self._blocking_continuously_notify_log()

    def _blocking_continuously_notify_log(self) -> None:
        """
            Blocks the execution and continuously notifies the awaitable with new log messages of the given level and tag.
            Expects that the log messages are in JSON format.
            If not, the message is ignored.
            ATTENTION: THIS HAS TO BE FIXED IN A FUTURE VERSION, CALLING RUN WILL DELETE ALL LOGS

            :param device_serial: The device serial number
            :param awaitable: The awaitable to notify
            :param log_level: The log level
            :param log_tag: The log tag
        """
        self.clear_logs() # TODO we should fix this in the long-run

        if (self.tag is None):
            self.tag = "*"

        if (self.level is None):
            self.level = "V"

        self.process = subprocess.Popen(["adb", "-s", self.device.serial, "logcat", f"{self.tag}:{self.level}", "*:S", "-v", "raw"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, bufsize=1)

        while not self._stop_event.is_set():
            splits = {}
            for line in self.process.stdout:
                if not line:
                    # process has been terminated
                    break
                if line.startswith("--------- beginning of main"):
                    continue
                line = line.strip()

                if self.support_split:
                    if line.startswith("SPLIT "):
                        splitLine = line.split(" ")
                        id = splitLine[1]
                        chunk = int(splitLine[2])
                        totalChunk = int(splitLine[3])
                        content = "".join(splitLine[4:])

                        if chunk == 1:
                            splits[id] = []
                            splits[id].append(content)
                            continue

                        if chunk != totalChunk:
                            if len(splits[id]) != chunk - 1:
                                pass
                            splits[id].append(content)
                            continue

                        if chunk == totalChunk:
                            splits[id].append(content)
                            line = "".join(splits[id])
                            del splits[id]

                    if line.startswith(self.split_identifier):
                        # could look like 33filedump44-213-33file44-857d5e2c-7a12-48f0-8fef-8fe1db070af1_com.google.android.gm
                        file_total_id = str(line.split("_")[0])
                        file_name = "33file44-" + file_total_id.split("33file44-")[1]
                        api_id = file_total_id.split("33filedump44-")[1].split("-33file44-")[0]
                        log_package_name = str(line.split("_")[1])
                        if log_package_name != self.package_name:
                            logger.debug(f"Skipping log package name {log_package_name} since it does not match the expected package name {self.package_name}")
                            continue
                        line = self.device.get_private_file_content(log_package_name, file_name)
                        if line:
                            line = line.strip()
                        else:
                            line = "{\"api_id\":\"" + api_id + "\", \"error\":\"Could not retrieve file content\"}"
                    
                l = line

                for reaction_lambda, reaction_callback in self.reactions:
                    try:
                        if reaction_lambda(l):
                            l = reaction_callback(l)
                            if l == None:
                                break
                    except Exception as e:
                        logger.error(f"Failed to execute reaction {e}")
                
                with self.results_lock:
                    if l != None:
                        self.results.append(l)
                    
        if self.process:
            self.process.terminate()

    def stop(self):
        self._stop_event.set()
        if self.process:
            self.process.terminate()

    def clear_logs(self):
        result = self.device.execute_command(["logcat", "-c"])
        if result.returncode == 0:
            return True
        else:
            logger.error(f"Failed to clear logs {result.stderr.decode('utf-8')}")
            return False
