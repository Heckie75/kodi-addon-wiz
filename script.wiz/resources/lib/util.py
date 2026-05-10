import xbmcaddon
import xbmc
import xbmcvfs
import os
import xbmcgui
import xbmcaddon
from resources.lib.wiz import WizDevice

MAX_DEVICES = 20
MAX_ROOMS = 10

_COLORS = ["off", "blue", "green", "cyan",
           "red", "magenta", "yellow", "white", "on"]


def getAddonDir() -> str:

    return xbmcvfs.translatePath(xbmcaddon.Addon().getAddonInfo('path'))


def getIconPath(icon: str) -> str:

    return os.path.join(getAddonDir(), "resources", "assets", f"icon_{icon}.png")


def createListItem(label: str, label2: str = None, icon: str = None, ipaddress: str = "", rank: int = 0, preselect=False, command: 'list[str]' = None) -> xbmcgui.ListItem:

    li = xbmcgui.ListItem(label=label, label2=label2)
    if icon:
        li.setArt({"thumb": getIconPath(icon=icon)})
    li.setProperty("rank", str(rank))
    li.setProperty("ipaddress", ipaddress)
    li.setProperty("preselect", str(preselect))
    if command:
        li.setProperty("command", "|".join(command))
    return li


def updateRooms(devices: list[WizDevice]) -> None:

    addon = xbmcaddon.Addon()

    knownRooms = getRooms()

    freeRooms = [i for i in range(
        MAX_ROOMS) if addon.getSetting(f"room_{i}_id") == ""]

    seenRooms = set(
        [d.system_config.room_id for d in devices if d.system_config])
    for seenRoom in seenRooms:
        if not freeRooms:
            break

        if seenRoom in knownRooms:
            continue

        i = freeRooms.pop(0)
        addon.setSetting(f"room_{i}_id", str(seenRoom))
        addon.setSetting(f"room_{i}_name", "")


def getRooms() -> dict[str, str]:

    addon = xbmcaddon.Addon()
    rooms = dict()
    for i in range(MAX_ROOMS):
        id = addon.getSetting(f"room_{i}_id")
        name = addon.getSetting(f"room_{i}_name")
        if id and name:
            rooms[id] = name

    return rooms


def getRoomById(id: int) -> str:

    rooms = getRooms()
    return rooms[str(id)] if str(id) in rooms else str(id)


def getTypeByModulename(moduleName: str) -> str:

    if "SOCKET" in moduleName:
        return "SOCKET"
    elif "RGV" in moduleName:
        return "SHRGBC"
    else:
        return "BULB"


def getLightName(color: dict) -> 'tuple[str, str, bool]':

    _color = (color["white"], color["red"], color["green"], color["blue"])

    if _color == (0, 0, 0, 0):
        return xbmcaddon.Addon().getLocalizedString(32121), "off", True
    elif _color[0] > 0:
        return f"{xbmcaddon.Addon().getLocalizedString(32129)} ({int(100 * _color[0]/255)})%", "on", True

    v = 0
    max_ = 0
    min_ = 255
    for i in range(1, 4):
        c = _color[4 - i]
        if c:
            v += 1 << (i - 1)
            min_ = min(c, min_)
            max_ = max(c, max_)

    return f"{xbmcaddon.Addon().getLocalizedString(32121 + v)} ({int(100 * max_/255)}%)", _COLORS[v],  v and 0.8 < (max_ / min_) < 1.2


def getDeviceIPsFromSettings() -> str:

    addon = xbmcaddon.Addon()
    return [addon.getSettingString(f"wiz_{i}_ipaddress") for i in range(MAX_DEVICES) if addon.getSettingBool(f"wiz_{i}_enable")]
