import base64
import json

import xbmc
import xbmcaddon
import xbmcgui

from .util import getIconPath, getNameByIP
from .wiz import WizDeviceController, Pilot

ADDON_ID = xbmcaddon.Addon().getAddonInfo("id")
ADDON = xbmcaddon.Addon()

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
FAVORITE_COMMAND_LABEL_ID = 32537
FAVORITE_CREATED_ID = 32538
FAVORITE_FAILED_ID = 32539
FAVORITE_NO_COMMAND_ID = 32540
FAVORITE_NO_DEVICES_ID = 32541
FAVORITE_PARSE_FAILED_ID = 32542
FAVORITE_ENTER_NAME_ID = 32530
FAVORITE_SELECT_ICON_ID = 32531


class FavoriteManager:

    def __init__(self):
        self.addon = ADDON
        self.dialog = xbmcgui.Dialog()

    def start_add_favorite(self) -> None:
        devices = self.addon.getSettingString("favs_latest_ip_addresses")
        command_json = self.addon.getSettingString("favs_latest_pilot")

        if not command_json:
            self._notify(self.addon.getLocalizedString(FAVORITE_TITLE_ID), self.addon.getLocalizedString(FAVORITE_NO_COMMAND_ID))
            return

        if not devices:
            self._notify(self.addon.getLocalizedString(FAVORITE_TITLE_ID), self.addon.getLocalizedString(FAVORITE_NO_DEVICES_ID))
            return

        try:
            pilot = Pilot.from_json(json.loads(command_json))
        except json.JSONDecodeError:
            self._notify(self.addon.getLocalizedString(FAVORITE_TITLE_ID), self.addon.getLocalizedString(FAVORITE_PARSE_FAILED_ID))
            return

        name = self._ask_favorite_name()
        if not name:
            return

        icon = self._ask_favorite_icon()
        if not icon:
            return

        if not self._confirm_favorite(name, icon, ""):
            return

        if self._create_favorite(name, icon, command_json, devices):
            self._notify(self.addon.getLocalizedString(FAVORITE_TITLE_ID), self.addon.getLocalizedString(FAVORITE_CREATED_ID))
        else:
            self._notify(self.addon.getLocalizedString(FAVORITE_TITLE_ID), self.addon.getLocalizedString(FAVORITE_FAILED_ID))

    def execute_favorite(self, favorite_data: str = None) -> None:

        pilot = None
        ip_addresses: list[str] = []

        # Decode favorite data from plugin URL
        if favorite_data:
            try:
                padded = favorite_data + "=" * (-len(favorite_data) % 4)
                decoded = base64.urlsafe_b64decode(padded.encode()).decode()
                xbmc.log(
                    f"Decoded favorite data: {decoded[:50]}...", xbmc.LOGINFO)
                favorite_info = json.loads(decoded)
                pilot = favorite_info.get("command")
                ip_addresses_str = favorite_info.get("devices", "")
                ip_addresses = [ip for ip in ip_addresses_str.split("|") if ip]
            except Exception:
                pass

        if not ip_addresses or not pilot:
            return

        device_names = [getNameByIP(ip_address) for ip_address in ip_addresses]

        self._notify(self.addon.getLocalizedString(32004), ", ".join(device_names), icon="default")

        controller = WizDeviceController(ip_addresses=ip_addresses)
        controller.setPilot(pilot).perform()

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
            message=f"{self.addon.getLocalizedString(FAVORITE_NAME_LABEL_ID) % name}\n{self.addon.getLocalizedString(FAVORITE_ICON_LABEL_ID) % self.addon.getLocalizedString(ICON_LABEL_IDS.get(icon, 32528))}\n{self.addon.getLocalizedString(FAVORITE_COMMAND_LABEL_ID) % command_summary}",
            nolabel=self.addon.getLocalizedString(32544),
            yeslabel=self.addon.getLocalizedString(32543),
        )

    def _create_favorite(self, name: str, icon: str, command_json: str, devices: str) -> bool:
        icon_path = getIconPath(icon)
        # Encode both command and devices
        favorite_info = json.dumps({
            "command": json.loads(command_json),
            "devices": devices
        })
        encoded_data = base64.urlsafe_b64encode(
            favorite_info.encode()).decode()
        path = f"plugin://{ADDON_ID}/?cmd=run_fav&data={encoded_data}"

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
