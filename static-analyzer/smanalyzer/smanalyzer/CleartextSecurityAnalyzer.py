import xml.etree.ElementTree as ET

from loguru import logger

class CleartextSecurityAnalyzer:

    def __init__(self, application_info, security_config):
        self.application_info = application_info
        self.security_config = security_config

    def analyze(self):

        target_sdk = self.application_info.target_sdk
        # check if target_sdk is parsable to an integer
        try:
            target_sdk = int(target_sdk)
        except (ValueError, TypeError):
            # if it is not known, we assume the 'most restrictive SDK version', i.e., 36, but still log the issue
            target_sdk = 36
            logger.error(f"Could not parse target SDK version: {self.application_info.target_sdk} for app {self.application_info.package_name}, defaulting to {target_sdk}")
            #raise ValueError(f"Invalid target SDK version: {target_sdk} for app {self.application_info.package_name}")
        # if it is not known, we assume the 'most restrictive SDK version', i.e., 36

        if target_sdk == None or target_sdk < 1:
            raise ValueError(f"Invalid target SDK version: {target_sdk} for app {self.application_info.package_name}")

        manifest_allows_cleartext_traffic = False
        webview_allows_cleartext_traffic = False


        if target_sdk < 28 and self.application_info.uses_cleartext_traffic == None:
            manifest_allows_cleartext_traffic = True
        elif target_sdk < 28 and self.application_info.uses_cleartext_traffic == "true":
            manifest_allows_cleartext_traffic = True
        elif target_sdk >= 28 and self.application_info.uses_cleartext_traffic == "true":
            manifest_allows_cleartext_traffic = True

        if target_sdk < 26:
            webview_allows_cleartext_traffic = True
            # webview honors the attribute for apps targeting api level 26 and higher (https://developer.android.com/guide/topics/manifest/application-element#usesCleartextTraffic:~:text=Note%3A%20WebView%20honors%20this%20attribute%20for%20applications%20targeting%20API%20level%2026%20and%20higher.)
        elif target_sdk >= 26:
            webview_allows_cleartext_traffic = manifest_allows_cleartext_traffic

        has_network_security_config = self.application_info.has_network_security_config

        if (not has_network_security_config):
            # Then the manifest is the only thing that defines it!
            if webview_allows_cleartext_traffic:
                self.security_config.allowed_domains.append("*")
            else:
                self.security_config.disallowed_domains.append("*")
        
        else:
            # this overwrites the manifest_allows_cleartext_traffic
            network_security_config_string = self.application_info.network_security_config
            try:
                xml = ET.fromstring(network_security_config_string)
            except TypeError:
                logger.error(f"Network security config file is None for app {self.application_info.package_name} {network_security_config_string}" )
                return
            except ET.ParseError as e:
                logger.error(f"Failed to parse network security config for app {self.application_info.package_name}: {e}")
                logger.error(f"Network security config content: {network_security_config_string}")
                #raise e
                return

            # get the network-security-config tag
            if xml.tag != "network-security-config":
                logger.error(f"Root tag should be network-security-config but found {xml.tag} in app {self.application_info.package_name}")
                return
                #raise Exception(f"Root tag should be network-security-config but found {xml.tag} in app {self.application_info.package_name}")

            # first, get the base-config tag
            base_config = xml.find("base-config")
            if not base_config is None:
                clear_text_traffic_permitted = base_config.get("cleartextTrafficPermitted")
                if not clear_text_traffic_permitted is None:
                    if clear_text_traffic_permitted == "true":
                        self.security_config.allowed_domains.append("*")
                    elif clear_text_traffic_permitted.startswith("@"):
                        self.security_config.disallowed_domains.append("--@*")
                    elif clear_text_traffic_permitted.startswith("${"):
                        self.security_config.allowed_domains.append("--$*")
                    elif clear_text_traffic_permitted == "false" or clear_text_traffic_permitted == "0" or clear_text_traffic_permitted == "FALSE":
                        self.security_config.disallowed_domains.append("*")
                    else:
                        self.security_config.allowed_domains.append("--other*")
                else:
                    self.security_config.disallowed_domains.append("*")
            else:
                self.security_config.disallowed_domains.append("*")



            domain_configs = xml.findall("domain-config")

            for domain_config in domain_configs:
                # here we should check if WebView has other threshold, as is the case for the manifest attribute
                default_cleartext_permitted = "false"
                if target_sdk < 28:
                    default_cleartext_permitted = "true"

                self.__parse_domain_config(domain_config, default_cleartext_permitted)

        pass

    def __parse_domain_config(self, domain_config, parent_cleartext_permitted):
        clear_text_traffic_permitted = domain_config.get("cleartextTrafficPermitted")

        if clear_text_traffic_permitted is None:
            clear_text_traffic_permitted = parent_cleartext_permitted
            # we have to try this out if that is how this behaves, because the documentation is a bit contradictory

        for domain in domain_config.findall("domain"):
            domain_name = domain.text
            include_subdomains = domain.get("includeSubdomains")
            if include_subdomains is None:
                include_subdomains == "false"

            subdomain_domain_name = domain_name
            if include_subdomains == "true":
                subdomain_domain_name = "*." + domain_name

            if clear_text_traffic_permitted == "true":
                self.security_config.allowed_domains.append(subdomain_domain_name)
            elif clear_text_traffic_permitted == "false" or clear_text_traffic_permitted == "0" or clear_text_traffic_permitted == "FALSE":
                self.security_config.disallowed_domains.append(subdomain_domain_name)
            elif clear_text_traffic_permitted.startswith("@"):
                self.security_config.disallowed_domains.append("--@" + subdomain_domain_name)
            elif clear_text_traffic_permitted.startswith("${"):
                self.security_config.allowed_domains.append("--$" + subdomain_domain_name)
            else:
                self.security_config.allowed_domains.append("--other" + subdomain_domain_name)

            children_domain_configs = domain_config.findall("domain-config")
            for child_domain_config in children_domain_configs:
                self.__parse_domain_config(child_domain_config, clear_text_traffic_permitted)
