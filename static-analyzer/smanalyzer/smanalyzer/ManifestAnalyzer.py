import logging

import lxml.etree as etree
import xml.etree.ElementTree as ET
import smanalyzer.XmlUtils as XmlUtils
from smanalyzer.models.ApplicationInfo import ApplicationInfo
from smanalyzer.models.ActivityInfo import ActivityInfo

from lxml import etree as ET

from androguard.core.apk import APK

class ManifestAnalyzer:
    """
    Analyzes the AndroidManifest.xml file of an APK and retrieves information about the application and its activities.
    """

    application_info: ApplicationInfo
    a: APK = None

    def __init__(self, application_info: ApplicationInfo, a: APK):
        self.application_info = application_info
        self.a = a


    def analyze(self):
        logging.info(f"Analyzing manifest for {self.application_info.package_name}")
        self.application_info.target_sdk = self.a.get_target_sdk_version()
        self.manifest_xml: etree.Element = self.a.get_android_manifest_xml()
        self.application_info.manifest_xml = self.a.get_android_manifest_xml()
        
        self.get_version_number()
        self.get_application_info()

    def get_version_number(self) -> None:
        """
            Retrieves the version number of the app from the <code>manifest</code> node in the AndroidManifest.xml file.
        """
        manifest_xml: etree.Element = self.a.get_android_manifest_xml()
        # in the main tag, get the versionName attribute
        version_name = self.a.get_androidversion_name()
        if version_name is not None:
            self.application_info.version_name = version_name

    
    def get_application_info(self) -> None:
        """
            Retrieves information from the <code>application</code> node in the AndroidManifest.xml file.
            This also transitively retrieves information about the activities in the app.
            See <a href="https://developer.android.com/guide/topics/manifest/application-element">this guide</a> for all tags that can be found in an <code>application</code> node.</p>
        """
        # Get the package name of the app
        self.application_info.package_name = self.a.get_package()
        if self.application_info.package_name is None or self.application_info.package_name == "":
            raise Exception("Could not find package name in manifest")

        # Get whether the app is enabled
        manifest_xml: etree.Element = self.a.get_android_manifest_xml()
        application_element: etree.Element = manifest_xml.find("application")
        if application_element is None:
            raise Exception("Could not find application element in manifest")
        
        # Get whether the app is enabled - if an app is not enabled it cannot be launched
        uses_cleartext_traffic = XmlUtils.get_attribute_ignore_namespace(application_element, "usesCleartextTraffic")
        if uses_cleartext_traffic is not None:
            self.application_info.uses_cleartext_traffic = uses_cleartext_traffic

        network_security_config = XmlUtils.get_attribute_ignore_namespace(application_element, "networkSecurityConfig")
        if network_security_config is not None:
            self.application_info.has_network_security_config = True
            self.application_info.network_security_config = network_security_config
        else:
            self.application_info.has_network_security_config = False

        # get the name of the specific id in the resources


    
        