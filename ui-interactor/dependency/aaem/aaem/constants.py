import os

ANDROID_HOME = os.getenv('ANDROID_HOME')
ANDROID_USER_HOME = os.getenv('ANDROID_USER_HOME')
ANDROID_EMULATOR_BIN = os.path.join(ANDROID_HOME, "emulator", "emulator")
ANDROID_ADB_BIN = os.path.join(ANDROID_HOME, "platform-tools", "adb")

def get_latest_build_tool_version(android_home: str = ANDROID_HOME) -> str:
    """
    Returns the highest build-tools version directory name in {ANDROID_HOME}/build-tools.
    
    :param android_home: Path to ANDROID_HOME.
    :return: The build-tools version (e.g., "30.0.2") or None if not found.
    """
    build_tools_dir = os.path.join(android_home, "build-tools")
    if not os.path.isdir(build_tools_dir):
        return None

    versions = []
    for d in os.listdir(build_tools_dir):
        d_path = os.path.join(build_tools_dir, d)
        if os.path.isdir(d_path):
            try:
                # Parse the version string into a tuple of integers.
                version_tuple = tuple(map(int, d.split('.')))
                versions.append((version_tuple, d))
            except ValueError:
                # Skip directories that don't have a version-like name.
                continue

    if not versions:
        return None

    # Get the directory with the highest version tuple.
    latest_version = max(versions, key=lambda x: x[0])[1]
    return latest_version

# get the newest appt binary

ANDROID_AAPT_BIN = os.path.join(ANDROID_HOME, "build-tools", get_latest_build_tool_version(), "aapt")