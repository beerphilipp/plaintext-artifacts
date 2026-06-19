import time
import logging

from aaem.Device import Device

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class IntentFuzzer:
    def __init__(self, device: Device, package_name: str, intent_fuzzing: list[dict], shutdown_event=None):
        self.intent_fuzzing = intent_fuzzing
        self.package_name = package_name
        self.device = device
        self.shutdown_event = shutdown_event
        
    def start(self):
        new_intent_fuzzing = []
        for element in self.intent_fuzzing:
            new_intent_fuzzing.append(element)
            data = element.get("data", "")
            if "https://www.example.com?fuzz=true" in data:
                modified_element = element.copy()
                modified_element["data"] = data.replace("https://", "http://")
                new_intent_fuzzing.append(modified_element)
        
        self.intent_fuzzing = new_intent_fuzzing
            
        for element in self.intent_fuzzing:
            if self.shutdown_event and self.shutdown_event.is_set():
                logger.info("Shutdown event set, stopping Intent Fuzzer.")
                break
            activity_name = element.get("activityName", "")
            data = element.get("data", "")
            
            logger.info(f"Force stopping app {self.package_name} before launching intent.")
            self.device.execute_command(["am", "force-stop", self.package_name])
            time.sleep(6)
            logger.info(f"Launching intent: {activity_name} with data: {data}")
            self.device.start_activity(self.package_name, activity_name, data)
            time.sleep(8)
            
            
            