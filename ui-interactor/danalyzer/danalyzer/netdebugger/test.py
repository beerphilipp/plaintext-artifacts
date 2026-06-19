from aaem.Device import Device
from NetworkDebugger import NetworkDebugger

def main():
    with Device("*") as d:
        package_name = "com.snc.test.webview2"
        net_debugger = NetworkDebugger(d, package_name)


if __name__ == "__main__":
    main()