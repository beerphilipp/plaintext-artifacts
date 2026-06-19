from smanalyzer.models.ApplicationInfo import ApplicationInfo
from smanalyzer.models.FastbotConfig import FastbotConfig

import os
import re
import sys

import lxml.etree as etree
from itertools import product
from xml.etree.ElementTree import TreeBuilder

from lxml import etree as ET

DEFAULT_URL = "https://www.example.com?fuzz=true"

class FastbotConfigCreator:


    def __init__(self, application_info: ApplicationInfo, fastbot_config: FastbotConfig):
        self.application_info = application_info
        self.fastbot_config = fastbot_config


    def analyze(self):
        root = self.application_info.manifest_xml
        #root = tree.getroot()
            
            # get all <activity> tags
                    # get all <activity> tags
        ns = {'android': 'http://schemas.android.com/apk/res/android'}

            # get the target sdk
        uses_sdk = root.xpath(".//uses-sdk", namespaces=ns)
        target_sdk = uses_sdk[0].xpath("@android:targetSdkVersion", namespaces=ns)
        if (len(target_sdk) > 0):
            target_sdk = int(target_sdk[0])
        else:
            target_sdk = 35 # we assume 35 if not set


        activities = root.xpath(".//activity", namespaces=ns)
            
        result = []
        try:
            amount_exported_activities = 0
            for activity in activities:
                prio = 0
                    # print the activity tag
                    #print(ET.tostring(activity, pretty_print=True).decode("utf-8"))
                    # get the name tag
                names = activity.xpath("@android:name", namespaces=ns)
                if (len(names) == 0):
                        # no name tag found, we skip this activity
                    continue
                activity_name = activity.xpath("@android:name", namespaces=ns)[0]

                    # what about aliases?

                    # get the exported tag
                exported = None
                exported_list = activity.xpath("@android:exported", namespaces=ns)
                if (len(exported_list) > 0):
                    exported = exported_list[0]
                    
                if (exported == "true"):
                    exported = True
                elif (exported == None):
                    if target_sdk >= 31:
                            # if target sdk is 31 or higher, we assume it is exported
                        exported = False
                    else:
                        exported = TreeBuilder
                elif (exported == "false"):
                    exported = False
                else:
                        # if exported is not None and not exported in ["true", "false"], then we conservatively assume it is exported
                    exported = True
                    
                if not exported:
                    continue

                amount_exported_activities += 1

                datas = []

                if ("web" in activity_name or "browser" in activity_name):
                        if prio < 9:
                            prio = 9

                    # get the intent-filter tags
                intent_filters = activity.xpath(".//intent-filter", namespaces=ns)
                    
                if (len(intent_filters) == 0):
                        # no intent filters found for the activity. We nevertheless add is to the result because we can open it
                    datas.append((DEFAULT_URL, prio))
                    
                for intent_filter in intent_filters:
                    filter_actions = []
                    filter_categories = []
                    actions = intent_filter.xpath(".//action", namespaces=ns)
                    for action in actions:
                        action_names = action.xpath("@android:name", namespaces=ns)
                        filter_actions.extend(action_names)
                        # get the categories
                    categories = intent_filter.xpath(".//category", namespaces=ns)
                    for category in categories:
                        category_names = category.xpath("@android:name", namespaces=ns)
                        filter_categories.extend(category_names)
                            #all_categories.append(category_name)

                    if ("android.intent.category.BROWSABLE" in filter_categories):
                        if prio < 3:
                            prio = 3

                    if ("android.intent.category.APP_BROWSER" in filter_categories):
                        if prio < 5:
                            prio = 5
                        
                    if ("android.intent.category.LAUNCHER" in filter_categories):
                        if prio < 10:
                            prio = 10
                        
                        # get the data
                        #datas = intent_filter.xpath(".//data", namespaces=ns)
                        # see https://developer.android.com/guide/topics/manifest/data-element
                        
                        # get all {http://schemas.android.com/apk/res/android}attributes in the data tags in the current intent filter
                    schemes = list(set(intent_filter.xpath(".//data/@android:scheme", namespaces={'android': 'http://schemas.android.com/apk/res/android'})))
                    hosts = list(set(intent_filter.xpath(".//data/@android:host", namespaces={'android': 'http://schemas.android.com/apk/res/android'})))
                    ports = list(set(intent_filter.xpath(".//data/@android:port", namespaces={'android': 'http://schemas.android.com/apk/res/android'})))
                    paths = list(set(intent_filter.xpath(".//data/@android:path", namespaces={'android': 'http://schemas.android.com/apk/res/android'})))
                    path_prefixes = list(set(intent_filter.xpath(".//data/@android:pathPrefix", namespaces={'android': 'http://schemas.android.com/apk/res/android'})))
                    path_patterns = list(set(intent_filter.xpath(".//data/@android:pathPattern", namespaces={'android': 'http://schemas.android.com/apk/res/android'})))
                    path_suffixes = list(set(intent_filter.xpath(".//data/@android:pathSuffix", namespaces={'android': 'http://schemas.android.com/apk/res/android'})))
                    path_advanced_patterns = list(set(intent_filter.xpath(".//data/@android:pathAdvancedPattern", namespaces={'android': 'http://schemas.android.com/apk/res/android'})))
                    mime_types = list(set(intent_filter.xpath(".//data/@android:mimeType", namespaces={'android': 'http://schemas.android.com/apk/res/android'})))

                    if (len(schemes) == 0):
                        # special handling
                        datas.append((DEFAULT_URL, prio))
                        pass
                    else:
                        regex = ""

                        if schemes:
                            regex += "(?P<scheme>" + "|".join(schemes) + ")://"   
                        else:
                            regex += "(?P<scheme>.*)://"

                        if hosts:
                            processed_hosts = ["." + host if host.startswith("*") else host for host in hosts]
                            regex += "(?P<host>" + "|".join(processed_hosts) + ")" 
                        else:
                            regex += "(?P<host>.*)"

                            #if ports:
                            #    if (len(ports) == 1):
                            #        # if there is only one port, we can use it directly
                            #        regex += ":" + ports[0]
                            #    else:
                            #        regex += "(:(" + "|".join(ports) + "))?"
                            #else:
                            #    regex += "(:.*?)?"
                            # ATTENTION: WE IGNORE PORTS FOR NOW

                        general_path_regexes = []

                        path_regex = ""
                        if paths:
                            path_regex += "(?P<path>" + "|".join(paths) + ")"
                            general_path_regexes.append(path_regex)
                            
                            
                        path_prefix_regex = ""
                        if path_prefixes:
                            processed_prefixes = [ prefix + ".*" for prefix in path_prefixes]
                            path_prefix_regex += "(?P<path_prefix>" + "|".join(processed_prefixes) + ")"
                            general_path_regexes.append(path_prefix_regex)
                            
                            
                            #if path_patterns:
                            #    if (len(path_patterns) == 1):
                            #        # if there is only one path pattern, we can use it directly
                            #        regex += "/" + path_patterns[0]
                            #    else:
                            #        # if there are multiple path patterns, we can use a regex
                            #        regex += "/(" + "|".join(path_patterns) + ")"
                            # ATTENTION: WE IGNORE PATH PATTERNS FOR NOW
                            
                        path_suffix_regex = ""
                        if path_suffixes:
                            path_suffix_regex += "(?P<path_suffix>" + "|".join([".*" + suffix for suffix in path_suffixes]) + ")"
                            general_path_regexes.append(path_suffix_regex)
                            
                            #if path_advanced_patterns:
                            #    path_parts.append("(" + "|".join(path_advanced_patterns) + ")")
                            # ATTENTION WE DO NOT SUPPORT PATH ADVANCED PATTERNS FOR NOW
                        

                        if len(general_path_regexes) > 0:
                            # if there are multiple path regexes, we can use a regex
                            if (len(general_path_regexes) == 1):
                                # if there is only one path regex, we can use it directly
                                regex += "(?P<p>" + general_path_regexes[0] + ")"
                            else:
                                regex += "(?P<p>" + "|".join(general_path_regexes) + ")" 
                        else:
                            regex += "(?P<p>.*)"

                        for s in set(self.create_string_for_regex(regex)):
                            datas.append((s, prio))




                            


                        # query and fragment ignored for now!
                        
                        
                    uri_relative_filter_groups = intent_filter.xpath(".//uri-relative-filter-group", namespaces=ns)
                    if (len(uri_relative_filter_groups) > 0):
                        print("##################")
                        print("Found uri-relative-filter-group tag")
                        print("##################")

                    #print(activity_name + " " + str(prio) + " " + str(datas))
                for data, prio in datas:
                    existing = next((item for item in result if item["activityName"] == str(activity_name) and item["data"] == data), None)
                    if existing:
                        if prio < existing["priority"]:
                            result.remove(existing)
                            result.append({"activityName": str(activity_name), "data": data, "priority": prio})
                    else:
                        result.append({"activityName": str(activity_name), "data": data, "priority": prio})
            
        except Exception as e:
            print(f"Error processing manifest: {e}")
                

            # sava the result to a file
            # sort the result by priority
        result = sorted(result, key=lambda x: x["priority"], reverse=True)
        print(result)
        self.fastbot_config.config = result
        


                

                    
        
        #print(f"Found {len(all_categories)} categories:")
        #for category in all_categories:
        #    print(f"  {category}")

        #print(f"Found {len(all_actions)} actions:")
        #for action in all_actions:
        #    print(f"  {action}")

                    
    def create_string_for_regex(self, regex_string):
        regex = r"{}".format(regex_string)
        predefined_examples = {
            "scheme": ["http", "https"],
            "host": ["somehost"]
        }

        pattern = re.compile(regex)
        group_patterns = pattern.groupindex.keys()


        schemes = []
        hosts = []
        ps = []
        for name in group_patterns:
            group_pattern = re.search(rf"\(\?P<{name}>(.*?)\)", regex).group(1)
            if name == "scheme":
                schemes = self.create_schemes(group_pattern)
            if name == "host":
                hosts = self.create_hosts(group_pattern)
            if name == "p":
                ps = self.create_p(group_pattern)

        
        # create all combinations of schemes, hosts and paths
        all_combinations = list(product(schemes, hosts, ps))
        uri_combinations = []
        for scheme, host, path in all_combinations:
            uri = f"{scheme}://{host}{path}"
            uri_combinations.append(uri)
        return uri_combinations




    def create_schemes(self, scheme_regex):
        if "scheme_regex" == ".*":
            return ["http", "https"]
        elif "|" in scheme_regex:
            return scheme_regex.split("|")
        else:
            return [scheme_regex]
        
    def create_hosts(self, host_regex):
        if host_regex == ".*":
            return ["somehost"]
        elif "|" in host_regex:
            return host_regex.split("|")
        else:
            return [host_regex]
        
    def create_p(self, p_regex):
        if p_regex.startswith("(") and not p_regex.endswith(")"):
            # if the regex starts with ( and does not end with ), we need to add a ). dirty hack
            p_regex += ")"
        
        pattern = re.compile(p_regex)
        group_patterns = pattern.groupindex.keys()

        if (len(group_patterns) == 0):
            # there are not groups.
            if (p_regex == ".*"):
                return ["/"]
            else:
                raise Exception("No groups found in regex: {}".format(p_regex))

        all_ps = []
        for name in group_patterns:
            group_pattern = re.search(rf"\(\?P<{name}>(.*?)\)", p_regex).group(1)
            if name == "path":
                all_ps.extend(self.create_path(group_pattern))
            if name == "path_prefix":
                all_ps.extend(self.create_path_prefix(group_pattern))
            if name == "path_suffix":
                all_ps.extend(self.create_path_suffix(group_pattern))
        return all_ps

    def create_path(self, path_regex):
        if path_regex == ".*":
            return ["/"]
        elif "|" in path_regex:
            return path_regex.split("|")
        else:
            return [path_regex]
        
    def create_path_prefix(self, path_prefix_regex):
        # simply remove the .* at the end of the path prefix
        if path_prefix_regex == ".*":
            return ["/"]
        elif "|" in path_prefix_regex:
            path_prefixes = path_prefix_regex.split("|")
            # remove the .* at the end of each path prefix
            path_prefixes = [prefix.replace(".*", "") for prefix in path_prefixes]
            return path_prefixes
        else:
            new_path_regex = path_prefix_regex.replace(".*", "")
            return [new_path_regex]

    def create_path_suffix(self, path_suffix_regex):
        # simply remove the .* at the beginning of the path suffix
        if path_suffix_regex == ".*":
            return ["/"]
        elif "|" in path_suffix_regex:
            path_suffixes = path_suffix_regex.split("|")
            # remove the .* at the beginning of each path suffix
            path_suffixes = [suffix.replace(".*", "") for suffix in path_suffixes]
            return path_suffixes
        else:
            new_path_regex = path_suffix_regex.replace(".*", "")
            return [new_path_regex]
