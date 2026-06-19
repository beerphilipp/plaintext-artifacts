import lxml.etree as etree

def get_attribute_ignore_namespace(xml: etree.Element, attribute_name: str):
    """
    Returns the value of the attribute with the given name in the given XML element without considering the namespace.
    
    :param xml: The XML element.
    :param attribute_name: The name of the attribute without the namespace.
    :return: The value of the attribute or None if the attribute does not exist.
    """
    for key, value in xml.attrib.items():
        key_without_namespace = key
        split = key.split("}")
        if len(split) > 1:
            key_without_namespace = split[1]
        if key_without_namespace == attribute_name:
            return value
    return None

