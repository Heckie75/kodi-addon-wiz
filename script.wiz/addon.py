import sys

from resources.lib.scanner import Scanner
from resources.lib.util import getDeviceIPsFromSettings
from resources.lib.wizard import Wizard
import xbmcaddon

if __name__ == "__main__":

    if len(sys.argv) == 2 and sys.argv[1] == "scan":
        Scanner().scan()

    else:
        ip_addresses = getDeviceIPsFromSettings()
        if not ip_addresses:
            xbmcaddon.Addon().openSettings()
        else:
            Wizard(ip_addresses=["255.255.255.255"]).start()
