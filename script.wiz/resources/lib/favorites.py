import base64
import json

import xbmc
import xbmcaddon
import xbmcgui

from resources.lib.util import getIconPath
from resources.lib.settings_util import write_request

from resources.lib import wiz
from resources.lib.wizard import Wizard

ICON_LABEL_IDS = {
    "bulb_on": 32510,
    "bulb_off": 32509,
    "bulb_red": 32511,
    "bulb_green": 32507,
    "bulb_blue": 32504,
    "bulb_cyan": 32505,
    "bulb_magenta": 32508,
    "bulb_yellow": 32514,
    "bulb_white": 32513,
    "bulb": 32201,
    "lamp": 32202,
    "hanginglamp": 32219,
    "spot": 32203,
    "livingroom": 32204,
    "bedroom": 32205,
    "kitchen": 32206,
    "hall": 32207,
    "bathroom": 32208,
    "globe": 32209,
    "candle": 32210,
    "socket": 32211,
    "tv": 32212,
    "radio": 32213,
    "coffee": 32214,
    "cooker": 32215,
    "computer": 32216,
    "printer": 32217,
    "server": 32218,
    "bulb_up": 32512,
    "bulb_down": 32506,
    "sleep": 32526,
    "wakeup": 32527,
    "doze": 32516,
    "ambient": 32501,
    "bgr": 32502,
    "rainbow": 32524,
    "disco": 32515,
    "blink": 32503,
    "pulse": 32523,
    "fade": 32518,
    "effect": 32517,
    "group": 32519,
    "group_all": 32520,
    "presets": 32521,
    "program": 32522,
    "random": 32525,
    "default": 32528,
}

FAVORITE_TITLE_ID = 32534
FAVORITE_NAME_LABEL_ID = 32535
FAVORITE_ICON_LABEL_ID = 32536
FAVORITE_CREATED_ID = 32538
FAVORITE_FAILED_ID = 32539
FAVORITE_NO_COMMAND_ID = 32540
FAVORITE_NO_DEVICES_ID = 32541
FAVORITE_PARSE_FAILED_ID = 32542
FAVORITE_ENTER_NAME_ID = 32530
FAVORITE_SELECT_ICON_ID = 32531


class FavoriteManager:

    def __init__(self):
        self.addon = xbmcaddon.Addon()
        self.dialog = xbmcgui.Dialog()

    def execute_favorite(self, request: str = None) -> None:

        if not request:
            return

        try:
            padded = request + "=" * (-len(request) % 4)
            decoded = base64.urlsafe_b64decode(padded.encode()).decode()
            request = json.loads(decoded)
            write_request(request=json.loads(decoded))
            if "pilot" in request:
                controller = wiz.WizDeviceController(
                    ip_addresses=request["ip_addresses"])
                controller.commands["setPilot"] = request["pilot"]
                controller.perform()

        except Exception:
            pass

    def start_add_favorite(self) -> None:

        wizard = Wizard(ip_addresses=["255.255.255.255"])
        wizard.sync()
        request = wizard.ask_request()

        if not request or ("pilot" not in request and "program" not in request):
            return

        name = self._ask_favorite_name()
        if not name:
            return

        icon = self._ask_favorite_icon()
        if not icon:
            return

        if not self._confirm_favorite(name, icon, ""):
            return

        if self._create_favorite(name, icon, request):
            self._notify(self.addon.getLocalizedString(
                FAVORITE_TITLE_ID), self.addon.getLocalizedString(FAVORITE_CREATED_ID))
        else:
            self._notify(self.addon.getLocalizedString(
                FAVORITE_TITLE_ID), self.addon.getLocalizedString(FAVORITE_FAILED_ID))

    def _ask_favorite_name(self) -> str:
        value = self.dialog.input(
            self.addon.getLocalizedString(FAVORITE_ENTER_NAME_ID),
            defaultt="",
            type=xbmcgui.INPUT_ALPHANUM)
        return value.strip() if value else ""

    def _ask_favorite_icon(self) -> str:
        listitems = []
        icons = []
        for icon_name in ICON_LABEL_IDS.keys():
            icons.append(icon_name)
            li = xbmcgui.ListItem(
                label=self.addon.getLocalizedString(ICON_LABEL_IDS[icon_name]))
            li.setArt({"thumb": getIconPath(icon=icon_name)})
            listitems.append(li)

        selected = self.dialog.select(
            self.addon.getLocalizedString(FAVORITE_SELECT_ICON_ID),
            listitems,
            useDetails=True,
        )
        if selected < 0:
            return ""

        return icons[selected]

    def _confirm_favorite(self, name: str, icon: str, command_summary: str) -> bool:
        return self.dialog.yesno(
            heading=self.addon.getLocalizedString(FAVORITE_TITLE_ID),
            message=f"{self.addon.getLocalizedString(FAVORITE_NAME_LABEL_ID) % name}\n{self.addon.getLocalizedString(FAVORITE_ICON_LABEL_ID) % self.addon.getLocalizedString(ICON_LABEL_IDS.get(icon, 32528))}",
            nolabel=self.addon.getLocalizedString(32544),
            yeslabel=self.addon.getLocalizedString(32543),
        )

    def _create_favorite(self, name: str, icon: str, request: dict) -> bool:

        icon_path = getIconPath(icon)
        encoded_request = base64.urlsafe_b64encode(
            json.dumps(request).encode()).decode()
        path = f"plugin://{self.addon.getAddonInfo("id")}/?cmd=run_fav&request={encoded_request}"

        payload = {
            "jsonrpc": "2.0",
            "method": "Favourites.AddFavourite",
            "params": {
                "title": name,
                "type": "media",
                "path": path,
                "thumbnail": icon_path,
            },
            "id": 1,
        }

        response = xbmc.executeJSONRPC(json.dumps(payload))
        try:
            result = json.loads(response)
            return not result.get("error")
        except (TypeError, ValueError):
            return False

    def _notify(self, heading: str, message: str, icon: str = "default") -> None:

        xbmcgui.Dialog().notification(
            heading,
            message,
            icon=getIconPath(icon if icon else "default"),
            time=5000,
        )
