import os
import json
import lxml.etree as etree

from dataclasses import asdict

from smanalyzer.models.ApplicationInfo import ApplicationInfo
from smanalyzer.models.FastbotConfig import FastbotConfig

class ResultAggregator:
    """
    This class is responsible for writing the results of the analysis to a file.
    """

    def write_to_file(self, output_dir: str, application_info: ApplicationInfo, fastbot_config: FastbotConfig):
        """
        Writes the results of the analysis to a file.
        The file is named after the package name of the application.

        :param output_dir: The directory where the results should be written to.
        :param application_info: The results of the analysis.
        """
        # capitalization in package names matter. so if the file already exists, we add a _1 to the end of the file name.
        package_output_dir = os.path.join(output_dir, application_info.package_name)
        if os.path.exists(package_output_dir):
            cnt = 1
            while (os.path.exists(package_output_dir)):
                package_output_dir = os.path.join(output_dir, f"{application_info.package_name}_{cnt}")
                cnt += 1

        os.makedirs(package_output_dir, exist_ok=True)

        # remove manifest_xml from application_info

        with open(os.path.join(package_output_dir, f"{application_info.package_name}-manifest.xml"), "w") as f:
            f.write(etree.tostring(application_info.manifest_xml, pretty_print=True).decode("utf-8"))

        application_info.manifest_xml = None

        with open(os.path.join(package_output_dir, f"{application_info.package_name}-app-info.json"), "w") as f:
            json.dump(asdict(application_info), f, indent=4)

        with open(os.path.join(package_output_dir, f"{application_info.package_name}-fastbot-config.json"), "w") as f:
            json.dump(fastbot_config.config, f, default=lambda o: o.__dict__, indent=4)