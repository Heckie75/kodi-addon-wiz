import json

from resources.lib import wiz
from resources.lib.util import MAX_DEVICES, createListItem
import xbmc
import xbmcgui
import xbmcaddon
from resources.lib.logger import MyLogger
from resources.lib import util


class WizardListener(wiz.WiZListener):

    def __init__(self, addon: xbmcaddon.Addon):

        self.addon = addon
        self.current: int = 0
        self.max_: int = 100
        self.last_command_summary: list[str] = ""

    def reset(self, max_) -> None:

        self.max_: int = max_
        self.current: int = 0

    def _update(self, ip_address: str, message: str) -> None:

        self.current += 1
        name = next((self.addon.getSettingString(f"wiz_{i}_name") for i in range(
            MAX_DEVICES) if self.addon.getSettingString(f"wiz_{i}_ipaddress") == ip_address), None)
        self.progress.update(message=name or ip_address,
                             percent=int(100 * self.current / self.max_))

    def onStart(self, ip_addresses: list[str], commands: dict[str, dict]) -> None:

        self.progress = xbmcgui.DialogProgressBG()
        self.progress.create(heading=self.addon.getLocalizedString(32001),
                             message=self.addon.getLocalizedString(32004))

        self.addon.setSettingString("favs_latest_ip_addresses", "|".join(
            [ip_address for ip_address in ip_addresses]))
        self.addon.setSettingString("favs_latest_pilot", json.dumps(
            commands["setPilot"]) if commands["setPilot"] else "")

        self.addon.setSettingString("favs_latest_devices", ", ".join(
            [util.getNameByIP(ip_address) for ip_address in ip_addresses]))
        self.addon.setSettingString(
            "favs_latest_command", ", ".join(self.last_command_summary))
        self.last_command_summary = []

    def onMessageReceived(self, ip_address: str, message: str):

        self._update(ip_address=ip_address, message=message)

    def onFinished(self, devices: list[wiz.WizDevice]):

        self.progress.close()


class Wizard():

    def __init__(self, ip_addresses: list[str]) -> None:

        wiz.LOGGER = MyLogger(xbmc.LOGINFO)
        self.addon = xbmcaddon.Addon()
        self.listener: WizardListener = WizardListener(self.addon)
        self.controller: wiz.WizDeviceController = wiz.WizDeviceController(
            ip_addresses=ip_addresses, listener=self.listener)

    def sync(self) -> None:

        self.listener.reset(MAX_DEVICES * 2)
        self.controller.getSystemConfig().getPilot().perform()

    def pilotForCurrent(self) -> wiz.Pilot:

        for d in self.controller.devices:

            if d.pilot:
                return d.pilot

        return None

    def selectDevices(self) -> 'list[xbmcgui.ListItem]':

        def _createListItemsForDevices() -> 'list[xbmcgui.ListItem]':

            listitems: list[xbmcgui.ListItem] = list()
            for i in range(MAX_DEVICES):
                if not self.addon.getSettingBool(f"wiz_{i}_enable"):
                    continue

                ipaddress = self.addon.getSettingString(f"wiz_{i}_ipaddress")
                device = next(
                    (d for d in self.controller.devices if d.ip_address == ipaddress), None)
                label = self.addon.getSetting(f"wiz_{i}_name")
                label2 = f"{device.pilot.color_str()}" if device and device.pilot else self.addon.getLocalizedString(
                    32005)
                icon = self.addon.getSetting(f"wiz_{i}_icon")
                listitems.append(createListItem(label=label, label2=label2, icon=icon, ipaddress=ipaddress, rank=self.addon.getSettingInt(
                    f"wiz_{i}_order"), preselect=self.addon.getSettingBool(f"wiz_{i}_preselect")))

            listitems.sort(key=lambda _li: (
                int(_li.getProperty("rank")), _li.getLabel()))
            return listitems

        options = _createListItemsForDevices()
        preselection = [i for i in range(
            len(options)) if options[i].getProperty("preselect") == str(True)]
        selection = xbmcgui.Dialog().multiselect(heading=self.addon.getLocalizedString(
            32401), options=options, useDetails=True, preselect=preselection)
        if selection:
            selectedOptions = [option for i,
                               option in enumerate(options) if i in selection]
            return selectedOptions
        else:
            return []

    def deviceMenu(self, listItemsForDevices: 'list[xbmcgui.ListItem]') -> 'xbmcgui.ListItem':

        def getTurnOnListItem() -> xbmcgui.ListItem:
            label = self.addon.getLocalizedString(32403)
            if len(listItemsForDevices) == 1:
                label2 = self.addon.getLocalizedString(
                    32404) % listItemsForDevices[0].getLabel()
            else:
                label2 = self.addon.getLocalizedString(
                    32405) % len(listItemsForDevices)

            icon = "bulb_on"
            return createListItem(label=label, label2=label2,
                                  icon=icon, command=["ON"])

        def getTurnOffListItem() -> xbmcgui.ListItem:
            label = self.addon.getLocalizedString(32406)
            if len(listItemsForDevices) == 1:
                label2 = self.addon.getLocalizedString(
                    32407) % listItemsForDevices[0].getLabel()
            else:
                label2 = self.addon.getLocalizedString(
                    32408) % len(listItemsForDevices)

            icon = "bulb_off"
            return createListItem(label=label, label2=label2,
                                  icon=icon, command=["OFF"])

        def getDimmingListItem() -> xbmcgui.ListItem:
            label = self.addon.getLocalizedString(32409)
            label2 = self.addon.getLocalizedString(32410)
            return createListItem(label=label, label2=label2,
                                  icon="wakeup", command=["DIMMING"])

        def getTemperatureListItem() -> xbmcgui.ListItem:
            label = self.addon.getLocalizedString(32411)
            label2 = self.addon.getLocalizedString(32412)
            return createListItem(label=label, label2=label2,
                                  icon="bulb_yellow", command=["TEMPERATURE"])

        def getColorListItem() -> xbmcgui.ListItem:
            label = self.addon.getLocalizedString(32413)
            label2 = self.addon.getLocalizedString(32414)
            return createListItem(label=label, label2=label2,
                                  icon="presets", command=["COLOR"])

        def getSceneListItem() -> xbmcgui.ListItem:
            label = self.addon.getLocalizedString(32417)
            label2 = self.addon.getLocalizedString(32418)
            return createListItem(label=label, label2=label2,
                                  icon="effect", command=["SCENE"])

        def getPulseListItem() -> xbmcgui.ListItem:
            label = self.addon.getLocalizedString(32421)
            label2 = self.addon.getLocalizedString(32422)
            return createListItem(label=label, label2=label2,
                                  icon="pulse", command=["PULSE"])

        listitems: 'list[xbmcgui.ListItem]' = list()
        heading = " | ".join([item.getLabel() for item in listItemsForDevices])

        def isAllBulbs() -> bool:

            for device in self.controller.devices:

                if device.ip_address not in self.controller.ip_addresses or not device.system_config:
                    continue

                feature = wiz.Features.fromModuleName(
                    device.system_config.module_name)
                if feature.device_type not in [wiz.Features.DEVICE_BULB, wiz.Features.DEVICE_STRIP]:
                    return False

            return True

        listitems.append(getTurnOnListItem())
        listitems.append(getTurnOffListItem())

        if isAllBulbs():
            listitems.append(getTemperatureListItem())
            listitems.append(getColorListItem())
            listitems.append(getDimmingListItem())
            listitems.append(getSceneListItem())
            listitems.append(getPulseListItem())

        selection = xbmcgui.Dialog().select(
            heading=heading, list=listitems, useDetails=True)
        if selection == -1:
            return None
        else:
            return listitems[selection]

    def dimmingMenu(self) -> bool:

        pilot = self.pilotForCurrent()
        current = pilot.dimming if pilot else 10
        preselect = 0

        heading = self.addon.getLocalizedString(32409)
        options: 'list[xbmcgui.ListItem]' = list()
        for i, level in enumerate(range(10, 110, 10)):
            if level <= current:
                preselect = i

            options.append(createListItem(
                label=f"{level}%"))

        selection = xbmcgui.Dialog().select(
            heading=heading, list=options, preselect=preselect)

        if selection == -1:
            return False

        level = 10 + 10 * selection
        self.controller.withDimming(level)
        self.listener.last_command_summary.append(f"Dimming {level}%")
        return True

    def temperatureMenu(self) -> bool:

        pilot = self.pilotForCurrent()
        current = pilot.temp if pilot else 0
        preselect = 0

        heading = self.addon.getLocalizedString(32411)
        options: 'list[xbmcgui.ListItem]' = list()
        for i, level in enumerate(range(2200, 7000, 500)):

            if level <= current:
                preselect = i

            options.append(createListItem(
                label=f"{level}K"))

        selection = xbmcgui.Dialog().select(
            heading=heading, list=options, preselect=preselect)

        if selection == -1:
            return False

        temp = 2200 + 500 * selection
        self.controller.withTemp(temp)
        self.listener.last_command_summary.append(f"Temperature {temp}K")
        return True

    def colorMenu(self, pure: bool = False) -> bool:

        def _hex(f: float) -> str:

            return f"0{hex(int(min(255, max(0, f)))).replace('0x', '')}"[-2:]

        def _transform(s: str) -> 'tuple[int,int,int,int]':

            color = int(s, 16)
            red = color >> 16 & 0xff
            green = color >> 8 & 0xff
            blue = color & 0xff
            if red == green == blue:
                return (red, 0, 0, 0)
            else:
                return (0, red, green, blue)

        colorlist: 'list[xbmcgui.ListItem]' = list()
        if pure:
            colorlist.append(xbmcgui.ListItem(
                label=self.addon.getLocalizedString(32125), label2="ffff0000"))
            colorlist.append(xbmcgui.ListItem(
                label=self.addon.getLocalizedString(32127), label2="ffffff00"))
            colorlist.append(xbmcgui.ListItem(
                label=self.addon.getLocalizedString(32123), label2="ff00ff00"))
            colorlist.append(xbmcgui.ListItem(
                label=self.addon.getLocalizedString(32124), label2="ff00ffff"))
            colorlist.append(xbmcgui.ListItem(
                label=self.addon.getLocalizedString(32122), label2="ff0000ff"))
            colorlist.append(xbmcgui.ListItem(
                label=self.addon.getLocalizedString(32126), label2="ffff00ff"))
            colorlist.append(xbmcgui.ListItem(
                label=self.addon.getLocalizedString(32128), label2="ffffffff"))
        else:
            colorlist.extend([xbmcgui.ListItem(
                label=f"{self.addon.getLocalizedString(32128 if i > 0 else 32121)} ({int(i*5100/255)}%)", label2=f"ff{_hex(i * 51) * 3}") for i in range(5, -1, -1)])
            colorlist.extend([xbmcgui.ListItem(
                label=f"{self.addon.getLocalizedString(32130)} ({int(i*5100/255)}%)", label2=f"ff{_hex(1 + i * 51)}{_hex(1 + i * 10)}00") for i in range(5, -1, -1)])
            colorlist.extend([xbmcgui.ListItem(
                label=f"{self.addon.getLocalizedString(32125)} ({int(i*5100/255)}%)", label2=f"ff{_hex(1 + i * 51)}0000") for i in range(5, -1, -1)])
            colorlist.extend([xbmcgui.ListItem(
                label=f"{self.addon.getLocalizedString(32127)} ({int(i*5100/255)}%)", label2=f"ff{_hex(1 + i * 51) * 2}00") for i in range(5, -1, -1)])
            colorlist.extend([xbmcgui.ListItem(
                label=f"{self.addon.getLocalizedString(32131)} ({int(i*5100/255)}%)", label2=f"ff{_hex(1 + i * 10)}{_hex(1 + i * 51)}00") for i in range(5, -1, -1)])
            colorlist.extend([xbmcgui.ListItem(
                label=f"{self.addon.getLocalizedString(32123)} ({int(i*5100/255)}%)", label2=f"ff00{_hex(1 + i * 51)}00") for i in range(5, -1, -1)])
            colorlist.extend([xbmcgui.ListItem(
                label=f"{self.addon.getLocalizedString(32132)} ({int(i*5100/255)}%)", label2=f"ff00{_hex(1 + i * 51)}{_hex(1 + i * 10)}") for i in range(5, -1, -1)])
            colorlist.extend([xbmcgui.ListItem(
                label=f"{self.addon.getLocalizedString(32124)} ({int(i*5100/255)}%)", label2=f"ff00{_hex(1 + i * 51) * 2}") for i in range(5, -1, -1)])
            colorlist.extend([xbmcgui.ListItem(
                label=f"{self.addon.getLocalizedString(32122)} ({int(i*5100/255)}%)", label2=f"ff0000{_hex(1 + i * 51)}") for i in range(5, -1, -1)])
            colorlist.extend([xbmcgui.ListItem(
                label=f"{self.addon.getLocalizedString(32133)} ({int(i*5100/255)}%)", label2=f"ff{_hex(1 + i * 10)}00{_hex(1 + i * 51)}") for i in range(5, -1, -1)])
            colorlist.extend([xbmcgui.ListItem(
                label=f"{self.addon.getLocalizedString(32126)} ({int(i*5100/255)}%)", label2=f"ff{_hex(1 + i * 51)}00{_hex(1 + i * 51)}") for i in range(5, -1, -1)])
            colorlist.append(xbmcgui.ListItem(
                label=self.addon.getLocalizedString(32415), label2="00ffffff"))

        hexstr = xbmcgui.Dialog().colorpicker(
            heading=self.addon.getLocalizedString(32416), colorlist=colorlist)

        if not hexstr:
            return False

        if hexstr == "00ffffff":
            ip = xbmcgui.Dialog().input(heading=self.addon.getLocalizedString(32415),
                                        type=xbmcgui.INPUT_IPADDRESS)
            selectedcolor = tuple([int(s) for s in ip.split(".")])
        else:
            selectedcolor = _transform(hexstr)

        r, g, b = selectedcolor[1], selectedcolor[2], selectedcolor[3]
        self.controller.withColor(
            red=r, green=g, blue=b, white=selectedcolor[0])
        try:
            hexcol = f"#{r:02x}{g:02x}{b:02x}"
        except Exception:
            hexcol = str((r, g, b))

        self.listener.last_command_summary.append(
            f"Color {hexcol} ({r},{g},{b})")
        return True

    def sceneMenu(self) -> bool:

        pilot = self.pilotForCurrent()
        current = pilot.sceneId if pilot else 0
        preselect = 0

        heading = self.addon.getLocalizedString(32419)
        options: 'list[xbmcgui.ListItem]' = list()
        for i, level in enumerate(wiz.Pilot.SCENES_LIST):

            preselect = i if wiz.Pilot.index_to_sceneId(
                i) == current else preselect
            options.append(createListItem(
                label=self.addon.getLocalizedString(32330 + i)))

        selection = xbmcgui.Dialog().select(
            heading=heading, list=options, preselect=preselect)

        if selection == -1:
            return False

        selectedScene = wiz.Pilot.index_to_sceneId(selection)
        if selectedScene:
            self.controller.withScene(scene=str(selectedScene))
        # build a human-readable scene summary
        scene_name = None
        try:
            scene_name = wiz.Pilot.SCENES_LIST[selection]
        except Exception:
            scene_name = str(selectedScene)

        speed_used = None
        if selectedScene in wiz.Pilot.SCENE_HAS_SPEED:
            while True:
                speed = xbmcgui.Dialog().input(
                    heading=self.addon.getLocalizedString(32420), type=xbmcgui.INPUT_NUMERIC, defaultt=str(max(10, self.controller.devices[0].pilot.speed)) if self.controller.devices[0].pilot else "10")

                if not speed:
                    break

                elif 10 <= int(speed) <= 200:
                    speed_used = int(speed)
                    self.controller.withSpeed(speed=speed_used)
                    break

                else:
                    continue

        if selectedScene in wiz.Pilot.SCENE_HAS_RGB:
            if not self.colorMenu():
                return False

        if selectedScene in wiz.Pilot.SCENE_HAS_DIMMING:
            if not self.dimmingMenu():
                return False

        # final summary: scene name plus optional speed
        if speed_used:
            self.listener.last_command_summary.append(
                f"Scene {scene_name}, speed {speed_used}")
        else:
            self.listener.last_command_summary.append(f"Scene {scene_name}")

        return True

    def pulseMenu(self) -> bool:

        delta = 10
        while True:
            s_delta = xbmcgui.Dialog().input(
                heading=self.addon.getLocalizedString(32423), type=xbmcgui.INPUT_NUMERIC, defaultt=str(delta))

            if not s_delta:
                return False

            delta = int(s_delta)
            if 10 <= int(delta) <= 100:
                break

            else:
                continue

        duration = 2
        while True:
            s_duration = xbmcgui.Dialog().input(
                heading=self.addon.getLocalizedString(32424), type=xbmcgui.INPUT_NUMERIC, defaultt=str(duration))

            if not s_duration:
                return False

            duration = int(s_duration)
            if 2 <= int(duration) <= 60:
                break

            else:
                continue

        self.controller.pulse(delta=delta, duration=duration * 60000)
        self.listener.last_command_summary.append(
            f"Pulse with delta {delta} and duration {duration} minutes")
        return True

    def start(self) -> None:

        def rememberSelection(ip_addresses: 'list[str]') -> None:

            for i in range(MAX_DEVICES):
                ipaddress = self.addon.getSetting(f"wiz_{i}_ipaddress")
                self.addon.setSettingBool(
                    f"wiz_{i}_preselect", ipaddress in ip_addresses)

        self.sync()

        while True:
            selectedListItems = self.selectDevices()
            if not selectedListItems:
                return

            self.controller.ip_addresses = [item.getProperty("ipaddress")
                                            for item in selectedListItems]
            rememberSelection(ip_addresses=self.controller.ip_addresses)

            li = self.deviceMenu(selectedListItems)
            if not li:
                return

            self.listener.reset(len(self.controller.devices) * 2)

            command = li.getProperty("command")
            if command == "ON":
                self.listener.last_command_summary = ["Turn On"]
                self.controller.withState(True).getPilot().perform()

            elif command == "OFF":
                self.listener.last_command_summary = ["Turn Off"]
                self.controller.withState(False).getPilot().perform()

            elif command == "DIMMING":
                if self.dimmingMenu():
                    self.controller.getPilot().perform()

            elif command == "TEMPERATURE":
                if self.temperatureMenu():
                    if self.dimmingMenu():
                        self.controller.getPilot().perform()

            elif command == "COLOR":
                if self.colorMenu():
                    if self.dimmingMenu():
                        self.controller.getPilot().perform()

            elif command == "SCENE":
                if self.sceneMenu():
                    self.controller.getPilot().perform()

            elif command == "PULSE":
                if self.pulseMenu():
                    self.controller.getPilot().perform()
