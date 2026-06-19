import sys
import os
import time
import tqdm
import json
import click
import logging
from androguard.misc import AnalyzeAPK
from smanalyzer.ResourceAnalyzer import ResourceAnalyzer
from loguru import logger

import smanalyzer.XmlUtils as XmlUtils

from smanalyzer.models.ApplicationInfo import ApplicationInfo
from smanalyzer.models.FastbotConfig import FastbotConfig
from smanalyzer.models.SecurityConfig import SecurityConfig

from smanalyzer.ManifestAnalyzer import ManifestAnalyzer
from smanalyzer.CodeAnalyzer import CodeAnalyzer
from smanalyzer.ResultAggregator import ResultAggregator
from smanalyzer.FastbotConfigCreator import FastbotConfigCreator
from smanalyzer.CleartextSecurityAnalyzer import CleartextSecurityAnalyzer

from lxml import etree



logger.remove()
logger.add(sys.stderr, level="WARNING")

def filter_androguard(record):
    # record["name"] is the logger name (usually the module)
    return not record["name"].startswith("androguard")

logger.add(sys.stdout, level="INFO", filter=filter_androguard)

@click.group()
def cli():
    pass

@cli.command("analyze")
@click.option("--app", help="Path to the APK file", required=True)
@click.option("--out", help="Output directory", required=True)
def analyze(app: str, out: str):
    logger.info(f"Analyzing {app}")
    apk = get_apk(app)

    fastbot_config: FastbotConfig = FastbotConfig()
    application_info: ApplicationInfo = ApplicationInfo(apk_path=apk)
    application_info.start_time = time.time()
    
    try:
        logger.info(f"Decompiling {apk} with Androguard")
        a, _, dx = AnalyzeAPK(apk)
        logger.info(f"Decompiled {apk} with Androguard")

        logger.info(f"Analyzing Manifest")
        ManifestAnalyzer(application_info, a).analyze()
        logger.info(f"Analyzed Manifest")

        
        if application_info.has_network_security_config:
            logger.info(f"Analyzing Resources")
            ResourceAnalyzer(application_info, a).analyze()
            logger.info(f"Analyzed Resources")

        logger.info(f"Creating Fastbot Config")
        FastbotConfigCreator(application_info, fastbot_config).analyze()
        logger.info(f"Created Fastbot Config")
        
    except Exception as e:
        logging.error(f"Error during analysis: {e}")
        application_info.end_time = time.time()
        application_info.exception = True
        ResultAggregator().write_to_file(out, application_info, fastbot_config)
        raise e

    application_info.end_time = time.time()
    ResultAggregator().write_to_file(out, application_info, fastbot_config)
    logging.info(f"Analysis successfully finished in {application_info.end_time - application_info.start_time} seconds")

def get_apk(app: str) -> str:
    # app may be a directory if we are dealing with split APKs. For now, use the base apk of the app.
    if os.path.isfile(app):
        return app
    elif os.path.isdir(app):
        apks = [os.path.join(app, f) for f in os.listdir(app) if f.endswith(".apk")]
        # get the shortest one
        return min(apks, key=len) if apks else None
    return None


@cli.command("cleartext")
@click.option("--out", help="Output directory", required=True)
def analyze_cleartext_config(out: str):
    # get all the directories in out (not recursively)
    dirs = [d for d in os.listdir(out) if os.path.isdir(os.path.join(out, d))]
    for dir in tqdm.tqdm(dirs):
        # get the file in the directory that starts with "-app-info.json"

        dir_path = os.path.join(out, dir)
        files = os.listdir(dir_path)

        # get the file that ends with -app-info.json
        app_info_file = next((os.path.join(dir_path, f) for f in files if f.endswith("-app-info.json")), None)
        if app_info_file is None:
            logging.warning(f"No app info file found in {dir}, skipping")
            continue

        # this is a json file, parse into applicationinfo
        application_info: ApplicationInfo = None
        with open(app_info_file, "r") as f:
            j = json.load(f)
            application_info = ApplicationInfo(**j)

        if application_info is None:
            raise ValueError("Failed to parse application info")

        security_config = SecurityConfig()
        CleartextSecurityAnalyzer(application_info, security_config).analyze()

        with open(os.path.join(dir_path, f"{application_info.package_name}-cleartext-config.json"), "w") as f:
            json.dump(security_config, f, default=lambda o: o.__dict__, indent=4)

@cli.command("version")
@click.option("--out", help="Output directory", required=True)
def version(out: str):
    """Only temporary command to get the version of the apk. Do not use at a later point.
    """
    dirs = [d for d in os.listdir(out) if os.path.isdir(os.path.join(out, d))]
    for dir in tqdm.tqdm(dirs):
        # get the file in the directory that starts with "-app-info.json"

        dir_path = os.path.join(out, dir)
        files = os.listdir(dir_path)

        app_info_file = next((os.path.join(dir_path, f) for f in files if f.endswith("-app-info.json")), None)
        if app_info_file is None:
            logging.warning(f"No app info file found in {dir}, skipping")
            continue

        manifest_file = next((os.path.join(dir_path, f) for f in files if f.endswith("-manifest.xml")), None)
        if manifest_file is None:
            logging.warning(f"No manifest file found in {dir}, skipping")
            continue

        version = None
        with open(manifest_file, "r") as f:
            manifest_xml = f.read()
            
            manifest_tree = etree.fromstring(manifest_xml.encode())
            version_name = XmlUtils.get_attribute_ignore_namespace(manifest_tree, "versionName")
            if version_name is not None:
                version = version_name

        j = None
        with open(app_info_file, "r") as f:
            j = json.load(f)
            j["version_name"] = version
        
        with open(app_info_file, "w") as f:
            json.dump(j, f, default=lambda o: o.__dict__, indent=4)


if __name__ == "__main__":
    cli(standalone_mode=False)