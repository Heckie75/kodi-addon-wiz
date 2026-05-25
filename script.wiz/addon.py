import sys
from urllib.parse import parse_qs

from resources.lib.scanner import Scanner
from resources.lib.util import getDeviceIPsFromSettings
from resources.lib.wizard import Wizard
from resources.lib.favorites import FavoriteManager
import xbmcaddon
import xbmc

if __name__ == "__main__":

    xbmc.log(f"Script started with arguments: {sys.argv}", xbmc.LOGINFO)

    if len(sys.argv) == 2 and sys.argv[1] == "scan":
        Scanner().scan()

    elif len(sys.argv) == 2 and sys.argv[1] == "add_fav":
        xbmc.log("Adding favorite", xbmc.LOGINFO)
        FavoriteManager().start_add_favorite()

    elif len(sys.argv) >= 2 and sys.argv[0].startswith("plugin://"):
        if sys.argv[2].startswith("?"):
            params = parse_qs(sys.argv[2].lstrip("?"))
            cmd = params.get("cmd", [""])[0]
            data = params.get("data", [""])[0]

            if cmd == "run_fav":
                FavoriteManager().execute_favorite(favorite_data=data)

    else:
        ip_addresses = getDeviceIPsFromSettings()
        if not ip_addresses:
            xbmcaddon.Addon().openSettings()
        else:
            Wizard(ip_addresses=["255.255.255.255"]).start()
