import sys
from urllib.parse import parse_qs

from resources.lib.scanner import Scanner
from resources.lib.settings_util import get_device_IPs_from_settings, transform_url_params_to_request, write_request
from resources.lib.wizard import Wizard
from resources.lib.favorites import FavoriteManager
import xbmcaddon

if __name__ == "__main__":

    # handle jsonrpc calls
    if len(sys.argv) == 2 and sys.argv[1].startswith("?"):
        params = parse_qs(sys.argv[1].lstrip("?"))
        request = transform_url_params_to_request(params)
        write_request(request)

    elif len(sys.argv) == 2 and sys.argv[1] == "scan":
        Scanner().scan()

    elif len(sys.argv) == 4 and sys.argv[1] == "pulse":
        Scanner().pulse(location=sys.argv[2], device=sys.argv[3])

    elif len(sys.argv) == 2 and sys.argv[1] == "add_fav":
        FavoriteManager().start_add_favorite()

    # handle calls by favorites
    elif len(sys.argv) >= 2 and sys.argv[0].startswith("plugin://"):
        if sys.argv[2].startswith("?"):
            params = parse_qs(sys.argv[2].lstrip("?"))
            cmd = params.get("cmd", [""])[0]
            request = params.get("request", [""])[0]

            if cmd == "run_fav":
                FavoriteManager().execute_favorite(request=request)

    # handle calls from addon's tile
    else:
        ip_addresses = get_device_IPs_from_settings()
        if not ip_addresses:
            xbmcaddon.Addon().openSettings()
        else:
            Wizard(ip_addresses=["255.255.255.255"]).control()
