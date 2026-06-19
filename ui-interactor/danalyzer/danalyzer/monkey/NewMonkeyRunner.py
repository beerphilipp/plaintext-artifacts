import json
import base64
import os
import subprocess
import threading
import time
import traceback
from datetime import datetime
from loguru import logger

from aaem.Device import Device
from aaem.adb.ADBLogger import ADBLogger
from danalyzer.netdebugger.NetworkDebugger import NetworkDebugger
from danalyzer.updater.AppUpdater import AppUpdater
from danalyzer.intentfuzzer.IntentFuzzer import IntentFuzzer

THROTTLE_MS = 500

class MonkeyRunner:

    def __init__(self, device: Device, package_name: str, out: str, duration: int, intent_fuzzing_file: str = None, shutdown_event=None):
        """
            Initialize the MonkeyRunner
            :param device: The device to run on
            :param package_name: The package name of the app to run
            :param out: The output directory
            :param timeout: The timeout in minutes
            :param shutdown_event: The shutdown event to signal when to stop
        """

        self.device = device
        self.package_name = package_name
        self.duration = duration
        self.shutdown_event = shutdown_event or threading.Event()
        self.intent_fuzzing = None
        
        if intent_fuzzing_file:
            self.intent_fuzzing = json.load(open(intent_fuzzing_file, 'r'))

        # Output paths
        self.out = os.path.join(out, self.package_name)
        self.out_data = os.path.join(self.out, "data")
        os.makedirs(self.out, exist_ok=True)

        self.result = {
            "run_info": {
                "device": device.serial,
                "time": time.time(),
                "package_name": package_name,
                "out": out,
                "duration": duration,
            },
            "start_time": None,
            "file_calls": [],
            "end_time": None,
            "error": "",
            "api_calls": [],
            "activities_seen": [],
        }

        self.is_error = False

        # Internal synchronization
        self.activity_thread_stop_event = threading.Event()
        self.monitor_thread_stop_event = threading.Event()
        self.lock = threading.Lock()

        # Threads
        self.activity_thread = None
        self.monitor_thread = None

        # Components
        self.api_logger = None
        self.network_debugger = None

        # Activity tracking
        self.activities = set()

        self.output_file = os.path.join(self.out, f"{self.package_name}.json")

    def start_on_device(self) -> int:
        """
            Run Monkey on the device.
            Returns 0 on success, 1 on failure.
        """
        
        logger.info(f"Starting Monkey on {self.device.serial} with app {self.package_name}")
        self.result["start_time"] = time.time()

        try:
            self.api_logger = ADBLogger(
                device=self.device,
                tag="33WV_API_CALL44",
                level="I",
                use_json=True,
                support_split=True,
                split_identifier="33filedump44-",
                package_name=self.package_name
            )
            
            self.network_debugger = NetworkDebugger(self.device, self.package_name)
            self.api_logger.start()
            self.monitor_thread = threading.Thread(target=self.monitor_api_calls, daemon=True)
            self.monitor_thread.start()
            self.start_activity_recorder()

            self.start()

        except Exception as e:
            logger.exception("Exception during Monkey execution")
            self.record_error(f"EXCEPTION_{str(e)}")
            self.is_error = True
        
        finally:
            self.finalize_execution()

        if self.is_error:
            exit(1)
        else:
            exit(0)

    # ------- Internal Lifecycle Methods -------
    
    def finalize_execution(self):

        self.result["end_time"] = time.time()

        logger.info("Stopping and cleaning up...")

        # Monkey Process
        try:
            self.maybe_kill_monkey()
        except Exception as e:
            pass

        # API Logger
        try:
            if self.api_logger:
                logger.info("Stopping API logger")
                self.api_logger.stop()
        except Exception as e:
            logger.error(f"Error stopping API logger: {str(e)}")
            traceback.print_exc()
            self.record_error(f"FINALLY_API_LOGGER_{str(e)}")

        # Network Debugger
        try:
            if self.network_debugger:
                logger.info("Retrieving network log")
                self.network_debugger.get_network_log(os.path.join(self.out, "net-log.json"))
        except Exception as e:
            logger.error(f"Error retrieving network log: {str(e)}")
            traceback.print_exc()
            self.record_error(f"FINALLY_NETWORK_DEBUGGER_{str(e)}")
        
        # Activity Recorder
        try:
            logger.info("Stopping activity recorder")
            self.stop_activity_recorder()
        except Exception as e:
            logger.error(f"Error stopping activity recorder: {str(e)}")
            traceback.print_exc()
            self.record_error(f"FINALLY_ACTIVITY_RECORDER_{str(e)}")

        # Monitor Thread
        try:
            logger.info("Stopping monitor thread")
            self.monitor_thread_stop_event.set()
            if self.monitor_thread:
                self.monitor_thread.join(timeout=3)
        except Exception as e:
            logger.error(f"Error stopping monitor thread: {str(e)}")
            traceback.print_exc()
            self.record_error(f"FINALLY_MONITOR_THREAD_{str(e)}")

        # Write output file
        try:
            self.write_output_to_file()
        except Exception as e:
            logger.error(f"Error writing output file: {str(e)}")
            traceback.print_exc()
            self.record_error(f"FINALLY_WRITE_OUTPUT_FILE_{str(e)}")


    # ------- Helper Methods -------
    
    def record_error(self, msg: str):
        with self.lock:
            self.result["error"] += f";{msg}"

    def write_output_to_file(self):
        with open(self.output_file, "w") as f:
            json.dump(self.result, f, indent=4, default=str)


    # ------- Activity Recorder Methods -------

    def start_activity_recorder(self):
        self.activity_thread = threading.Thread(target=self.record_activities, daemon=True)
        self.activity_thread.start()

    def stop_activity_recorder(self):
        if self.activity_thread:
            self.activity_thread_stop_event.set()
            self.activity_thread.join(timeout=3)

    def record_activities(self):
        while not self.activity_thread_stop_event.is_set():
            try:
                activity = self.device.get_current_activity()
                if activity and activity not in self.activities:
                    with self.lock:
                        self.activities.add(activity)
                        self.result["activities"] = list(self.activities)
                        self.result["activities_seen"].append({"activity": activity, "timestamp": time.time()})
                    logger.info(f"New activity: {activity}")
            except Exception as e:
                logger.error(f"Error recording activity: {str(e)}")
                traceback.print_exc()
                self.record_error(f"ACTIVITY_RECORDER_{str(e)}")
            time.sleep(1)

    # ------- API Monitoring Methods -------

    def monitor_api_calls(self):
        while not self.monitor_thread_stop_event.is_set():
            if not self.api_logger:
                break

            try:
                calls = self.api_logger.reset_logs()
                file_calls = [x for x in calls if "file_loaded" in x]
                api_calls = [x for x in calls if "file_saved" not in x]
                
                with self.lock:
                    self.result["file_calls"].extend(file_calls)
                
                self.get_files(file_calls)

                with self.lock:
                    self.result["api_calls"].extend(api_calls)

            except Exception as e:
                logger.error(f"Error monitoring API calls: {str(e)}")
                traceback.print_exc()
                self.record_error(f"MONITOR_API_CALLS_{str(e)}")
                break

            time.sleep(1)

    def get_files(self, calls):
        for call in calls:
            try:
                logger.info(f"Retrieving file from device: {call}")
                has_temporary_file = "temporary_file_path" in call and call["temporary_file_path"] != None
                package = call["package"]
                base64_url = call["base64"]
                if package != self.package_name:
                    logger.warning(f"Package name mismatch when retrieving file: expected {self.package_name}, got {package}")
                    continue
                
                if has_temporary_file:
                    # this is the case for resource files and asset files
                    file_on_device = f"/data/data/{package}/files/{call['temporary_file_path']}"
                else:
                    file = call["original_file_url"]
                    file_on_device = file.replace("file://///", "").replace("file:////", "").replace("file:///", "").replace("file://", "").replace("file:/", "").replace("file:", "")
                    if not file_on_device.startswith("/"):
                        file_on_device = "/" + file_on_device
                saved = self.device.get_file(file_on_device, os.path.join(self.out, base64_url))
                if not saved:
                    logger.error(f"Failed to retrieve file {file} from device")
                    self.record_error(f"GET_FILE_FAILED_{file}")
            except Exception as e:
                logger.error(f"Error retrieving file {file} from device: {str(e)}")
                traceback.print_exc()
                self.record_error(f"GET_FILE_{str(e)}")

    # ------- Monkey Execution Methods -------

    def is_monkey_running(self) -> bool:
        result = self.device.execute_command(["ps", "|", "grep", "com.android.commands.monkey"])
        output = result.stdout.decode('utf-8')
        stripped = output.strip()
        if stripped:
            return True
        return False



    def start_monkey(self):
        """
        Start Monkey on the device for the given duration.
        """
        THROTTLE = str(THROTTLE_MS)
        EVENTS_TO_SEND = str(int(self.duration * 60 * 2))  # 2 events per second

        start = datetime.now()

        while (datetime.now() - start).total_seconds() < self.duration * 60:

            if (not self.is_monkey_running()):
                logger.info("Monkey is not running, starting...")
                time.sleep(2)
                self.device.execute_command(["monkey", "-p", self.package_name, "--throttle", THROTTLE, EVENTS_TO_SEND])

            if self.shutdown_event.is_set():
                logger.info("Shutdown event set, stopping Monkey")
                return
            
            time.sleep(1)

    def maybe_kill_monkey(self):
        try:
            self.device.execute_command(["pkill", "monkey"])
        except Exception as e:
            pass

    
    def start(self):
        try:
            updated = AppUpdater(self.device, self.package_name).check_maybe_update_app()
            self.result["app_update"] = updated
        except Exception as e:
            logger.error(f"Error updating app: {str(e)}")
            traceback.print_exc()
            self.record_error(f"APP_UPDATER_{str(e)}")

        self.start_monkey()
        logger.info("Monkey run completed.")
        
        if self.intent_fuzzing:
            logger.info("Starting Intent Fuzzer...")
            intent_fuzzer = IntentFuzzer(device=self.device, package_name=self.package_name, intent_fuzzing=self.intent_fuzzing, shutdown_event=self.shutdown_event)
            intent_fuzzer.start()
        