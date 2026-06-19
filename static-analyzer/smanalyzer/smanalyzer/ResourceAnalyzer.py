import os
import tempfile
import subprocess

import lxml.etree as ET

from pathlib import Path

from importlib.resources import files

from smanalyzer.models.ApplicationInfo import ApplicationInfo
from androguard.misc import AnalyzeAPK

# based on this directory
lib_dir = files("smanalyzer").joinpath("libs")
APKTOOL_JAR = os.path.join(lib_dir, "apktool_2.10.0.jar")

class ResourceAnalyzer:
    
    def __init__(self, application_info: ApplicationInfo, a):
        self.application_info = application_info
        self.a = a

    def analyze(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            cmd = ["java", "-jar", APKTOOL_JAR, "d", self.application_info.apk_path, "-s", "-o", temp_dir, "-f"]
            result = subprocess.run(cmd, stderr=subprocess.PIPE, stdout=subprocess.PIPE)


            if result.returncode != 0:
                raise Exception(f"Error decompiling APK with apktool: {result.stderr}")

            # search for all files ending with .xml and containing the string specified in the network_security_config attribute

            # find in temp_dir
            file_name = self.application_info.network_security_config
            if file_name.startswith("@"):
                file_hex_id = file_name[1:]
                file_decimal_id = int(file_hex_id, 16)
                file_name = self.get_correct_resource(file_decimal_id)
            else:
                raise Exception("Could not find network security config resource as it is not a reference")

        
            if Path(temp_dir).joinpath("res", "xml", f"{file_name}.xml").exists():
                self.application_info.network_security_config = Path(temp_dir).joinpath("res", "xml", f"{file_name}.xml").read_text()
            else:
                raise Exception(f"Could not find network security config file {file_name}.xml in the APK")

    def get_correct_resource(self, resource_id: int) -> str:
        res_name = self.a.get_android_resources().get_resource_xml_name(resource_id)
        resource_name = res_name.split(":")[1].split("/")[1]
        return resource_name

    def get_correct_network_config(self, matching_files):
        network_security_configs = []
        for file in matching_files:
            # attempt to parse the file as an xml
            root = ET.parse(file).getroot()
            # check if the root tag is the one we expect
            if root.tag == "network-security-config":
                network_security_configs.append(file)
        
        if len(network_security_configs) == 1:
            return network_security_configs[0]
        elif len(network_security_configs) == 0:
            raise Exception("Found no network security config files in the APK")
        elif len(network_security_configs) > 1:
            raise Exception("Found multiple network security config files in the APK")
