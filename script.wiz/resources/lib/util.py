import os
import xbmcaddon
import xbmcgui
import xbmcvfs

_COLORS = ["off", "blue", "green", "cyan",
           "red", "magenta", "yellow", "white", "on"]

def getAddonDir() -> str:

    return xbmcvfs.translatePath(xbmcaddon.Addon().getAddonInfo('path'))


def getIconPath(icon: str) -> str:

    if icon == "default":
        return os.path.join(getAddonDir(), "resources", "assets", "icon.png")

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
