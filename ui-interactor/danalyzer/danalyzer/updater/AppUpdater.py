import time
import uiautomator2 as u2
import logging

from aaem.Device import Device

logger = logging.getLogger(__name__)

PLAY_STORE_PACKAGE = "com.android.vending"
UPDATE_APP_TEXT = "Update from Play"

class AppUpdater:
    """
        Class that checks if an app can only be launched when updated via the Play Store and performs the update if necessary.
    """

    def __init__(self, device: Device, package_name: str):
        self.device = device
        self.package_name = package_name

    def __initialize_device(self):
        try:
            self.u2_device = u2.connect(self.device.serial)
        except Exception as e:
            logger.error(f"Failed to initialize device: {e}")
            raise

    def __release_device(self):
        self.u2_device.press("home")
        try:
            self.u2_device.stop_uiautomator()

        except Exception as e:
            logger.error(f"Failed to release device: {e}")

    def __open_app(self, package_name: str) -> bool:
        """Open app by package name"""
        try:
            self.u2_device.app_start(package_name, stop=True)
            time.sleep(2)
            logger.info(f"Opened app: {package_name}")
            return True
        except Exception as e:
            logger.error(f"Failed to open app: {e}")
            return False
        
    def __handle_app_flow(self):
        pass

    def __handle_game_flow(self):
        pass

    def __check_maybe_update_app_internal(self):
        logger.info(f"Checking for app updates for {self.package_name}")
        self.__open_app(self.package_name)
        time.sleep(3)
        current_package = self.u2_device.app_current().get("package")

        if current_package == PLAY_STORE_PACKAGE:
            logger.info(f"App {self.package_name} requires update via Play Store")

            if self.u2_device(text="Get app").wait(timeout=5):
                self.u2_device(text="Get app").click()

            if self.u2_device(text=UPDATE_APP_TEXT).wait(timeout=5):
                self.u2_device(text=UPDATE_APP_TEXT).click()

            if self.u2_device(text="Update this app from Play?").wait(timeout=2):
                if self.u2_device(text=UPDATE_APP_TEXT).wait(timeout=5):
                    self.u2_device(text=UPDATE_APP_TEXT).click()
            
            logger.info("App update started, waiting for completion...")
            if self.u2_device(text="Cancel").wait_gone(timeout=60*3):
                logger.info("App update completed.")
                return True

            logger.warning("App update did not complete in time.")
            return False
        
        else:
            logger.info(f"No update needed for app {self.package_name}")
            return None


    def check_maybe_update_app(self):
        """
        Check if the app needs to be updated via the Play Store and perform the update if necessary.
         :return: True if the app was updated, False if the updated failed, None if no update was needed.
        """
        try:
            self.__initialize_device()
            result = self.__check_maybe_update_app_internal()
        finally:
            self.__release_device()
        
