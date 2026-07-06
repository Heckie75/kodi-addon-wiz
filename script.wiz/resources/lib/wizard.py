import time
from datetime import datetime

import xbmc
import xbmcgui
import xbmcaddon

from resources.lib import settings_util, util, wiz


class WizardListener(wiz.WiZListener):

    def __init__(self, addon: xbmcaddon.Addon):

        self.addon = addon
        self.current: int = 0
        self.max_: int = settings_util.MAX_DEVICES * 2
        self.progress = xbmcgui.DialogProgress()

    def initialize(self, max_) -> None:

        self.max_: int = max_
        self.current: int = 0
        self.progress.create(heading=self.addon.getLocalizedString(32001),
                             message=self.addon.getLocalizedString(32004))

    def _update(self, ip_address: str, message: str) -> None:

        self.current += 1
        name = settings_util.get_name_by_IP(ip_address)
        self.progress.update(message=name or ip_address,
                             percent=int(100 * self.current / self.max_))

    def onMessageReceived(self, ip_address: str, message: str):

        self._update(ip_address=ip_address, message=message)

    def onFinished(self, devices: list[wiz.WizDevice]):

        self.progress.close()


class Wizard():

    SCENE_ICONS = {
        11: "warmwhite",  # warm white
        17: "",  # true colors
        12: "daylight",  # daylight
        13: "bulb_white",  # cool white
        30: "",  # golden white
        15: "",  # focus
        16: "",  # relax
        2: "romance",  # romance
        6: "cozy",  # cozy
        26: "",  # club
        29: "",  # candlelight
        5: "fireplace",  # fireplace
        18: "tvtime",  # tv time
        10: "bedtime",  # bedtime
        14: "nightlight",  # night light
        3: "sunset",  # sunset
        9: "wakeup_scene",  # wakeup
        20: "spring",  # spring
        21: "summer",  # summer
        22: "fall",  # fall
        36: "",  # snowy sky
        23: "",  # deep dive
        1: "ocean",  # ocean
        7: "forest",  # forest
        24: "",  # jungle
        25: "",  # mojito
        19: "plantgrowth",  # plant growth
        28: "halloween",  # halloween
        27: "xmas",  # christmas
        4: "party",  # party
        8: "pastel",  # pastel Colors
        32: "",  # steampunk
        33: "",  # diwali
        35: "",  # light alarm
        31: "",  # pulse
        0: "",  # colors
        40: "",  # dim to warm
        34: "",  # (unknown)
        249: "",  # pulse
        1000: ""  # rhythm
    }

    PROGRAM_ICONS = {
        wiz.Program.PROGRAM_INTERVAL: "sleep",
        wiz.Program.PROGRAM_FADE: "fade",
        wiz.Program.PROGRAM_WAKEUP: "wakeup",
        wiz.Program.PROGRAM_DOZE: "doze",
        wiz.Program.PROGRAM_AMBIENT: "ambient",
        wiz.Program.PROGRAM_RGB: "rgb",
        wiz.Program.PROGRAM_GBR: "gbr",
        wiz.Program.PROGRAM_BRG: "brg",
        wiz.Program.PROGRAM_BGR: "bgr",
        wiz.Program.PROGRAM_RBG: "rbg",
        wiz.Program.PROGRAM_GRB: "grb",
        wiz.Program.PROGRAM_RANDOM: "random",
        wiz.Program.PROGRAM_INFINITE: "infinite",
        wiz.Program.PROGRAM_WARM_TO_COLD: "bulb_up",
        wiz.Program.PROGRAM_COLD_TO_WARM: "bulb_down",
        wiz.Program.PROGRAM_SUNRISE: "wakeup",
        wiz.Program.PROGRAM_SUNSET: "doze",
        wiz.Program.PROGRAM_SUNRISE_SUNSET: "wakeup"
    }

    def __init__(self, ip_addresses: list[str]) -> None:

        self.addon = xbmcaddon.Addon()
        self.listener: WizardListener = WizardListener(self.addon)
        self.controller: wiz.WizDeviceController = wiz.WizDeviceController(
            ip_addresses=ip_addresses, listener=self.listener)

    def sync(self) -> None:

        for i in range(3):
            try:
                self.listener.initialize(
                    max_=len(settings_util.get_enabled_device_prefixes())*2)
                self.controller.getSystemConfig().getPilot().perform()
                break
            except:
                time.sleep(.9 * (i + 1))

        self.listener.onFinished(self.controller.devices)

    def perform(self, request: dict) -> None:

        self.controller.ip_addresses = request["ip_addresses"]

        try:
            self.listener.initialize(len(self.controller.devices))
            self.controller.getPilot().perform()

        except Exception as ex:
            xbmc.log(f"{ex}", xbmc.LOGERROR)

        finally:
            self.listener.onFinished(self.controller.devices)

    def pilotForCurrent(self) -> wiz.Pilot:

        for d in self.controller.devices:

            if d.pilot:
                return d.pilot

        return None

    def selectDevices(self) -> 'list[xbmcgui.ListItem]':

        def _createListItemsForDevices() -> 'list[xbmcgui.ListItem]':

            listitems: list[xbmcgui.ListItem] = list()
            preselected_ip_addresses = settings_util.get_preselection()
            addon = self.addon

            locations = [i for i in range(settings_util.MAX_LOCATIONS)
                         if addon.getSetting(f"room_{i}_id") != ""]
            locations.sort(key=lambda key: addon.getSettingInt(
                f"location_{key}_order"))

            for location in locations:
                show_as_location = addon.getSettingBool(
                    f"location_{location}_show_as_location")
                if show_as_location:
                    ip_addresses = settings_util.get_location_ip_addresses(
                        location)
                    if not ip_addresses:
                        continue

                    label = addon.getSetting(f"location_{location}_name")
                    if not label:
                        label = addon.getLocalizedString(32151 + location)

                    label2 = f"{len(ip_addresses)} %s: %s" % (
                        addon.getLocalizedString(32001), "")
                    icon = addon.getSetting(f"location_{location}_icon")
                    listitems.append(util.createListItem(
                        label=label,
                        label2=label2,
                        icon=icon,
                        ipaddresses=settings_util.get_location_ip_addresses(
                            location),
                        rank=addon.getSettingInt(f"location_{location}_order"),
                        preselect=any(
                            ip in preselected_ip_addresses for ip in ip_addresses)
                    ))
                    continue

                for prefix in settings_util.get_enabled_prefixes_for_location(location):
                    ipaddress = addon.getSettingString(f"{prefix}_ipaddress")
                    device = next(
                        (d for d in self.controller.devices if d.ip_address == ipaddress), None)
                    label = addon.getSetting(f"{prefix}_name")
                    label2 = f"{device.pilot.color_str()}" if device and device.pilot else addon.getLocalizedString(
                        32005)
                    icon = addon.getSetting(f"{prefix}_icon")
                    listitems.append(util.createListItem(label=label, label2=label2, icon=icon, ipaddresses=[ipaddress], rank=addon.getSettingInt(
                        f"{prefix}_order"), preselect=ipaddress in preselected_ip_addresses))

            listitems.append(util.createListItem(label=self.addon.getLocalizedString(
                32040), label2=self.addon.getLocalizedString(32041), icon="group_all", ipaddresses=["255.255.255.255"], rank=9999))

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

    def isAllBulbs(self, ip_addresses: list[str]) -> bool:

        for device in self.controller.devices:

            if device.ip_address not in ip_addresses or not device.system_config:
                continue

            feature = wiz.Features.fromModuleName(
                device.system_config.module_name)
            if feature.device_type not in [wiz.Features.DEVICE_BULB, wiz.Features.DEVICE_STRIP]:
                return False

        return True

    def deviceMenu(self, listItemsForDevices: 'list[xbmcgui.ListItem]', allBulbs: bool) -> 'xbmcgui.ListItem':

        def getTurnOnListItem() -> xbmcgui.ListItem:
            label = self.addon.getLocalizedString(32403)
            if len(listItemsForDevices) == 1:
                label2 = self.addon.getLocalizedString(
                    32404) % listItemsForDevices[0].getLabel()
            else:
                label2 = self.addon.getLocalizedString(
                    32405) % len(listItemsForDevices)

            icon = "bulb_on"
            return util.createListItem(label=label, label2=label2,
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
            return util.createListItem(label=label, label2=label2,
                                       icon=icon, command=["OFF"])

        def getDimmingListItem() -> xbmcgui.ListItem:
            label = self.addon.getLocalizedString(32409)
            label2 = self.addon.getLocalizedString(32410)
            return util.createListItem(label=label, label2=label2,
                                       icon="wakeup", command=["DIMMING"])

        def getTemperatureListItem() -> xbmcgui.ListItem:
            label = self.addon.getLocalizedString(32411)
            label2 = self.addon.getLocalizedString(32412)
            return util.createListItem(label=label, label2=label2,
                                       icon="bulb_yellow", command=["TEMPERATURE"])

        def getColorListItem() -> xbmcgui.ListItem:
            label = self.addon.getLocalizedString(32413)
            label2 = self.addon.getLocalizedString(32414)
            return util.createListItem(label=label, label2=label2,
                                       icon="presets", command=["COLOR"])

        def getSceneListItem() -> xbmcgui.ListItem:
            label = self.addon.getLocalizedString(32417)
            label2 = self.addon.getLocalizedString(32418)
            return util.createListItem(label=label, label2=label2,
                                       icon="effect", command=["SCENE"])

        def getPulseListItem() -> xbmcgui.ListItem:
            label = self.addon.getLocalizedString(32421)
            label2 = self.addon.getLocalizedString(32422)
            return util.createListItem(label=label, label2=label2,
                                       icon="pulse", command=["PULSE"])

        def getProgramListItem() -> xbmcgui.ListItem:
            label = self.addon.getLocalizedString(32522)
            label2 = self.addon.getLocalizedString(32545)
            return util.createListItem(label=label, label2=label2,
                                       icon="program", command=["PROGRAM"])

        listitems: 'list[xbmcgui.ListItem]' = list()
        heading = " | ".join([item.getLabel() for item in listItemsForDevices])

        listitems.append(getTurnOnListItem())
        listitems.append(getTurnOffListItem())

        if allBulbs:
            listitems.append(getDimmingListItem())
            listitems.append(getSceneListItem())

        listitems.append(getProgramListItem())

        if allBulbs:
            listitems.append(getTemperatureListItem())
            listitems.append(getColorListItem())
            listitems.append(getPulseListItem())

        selection = xbmcgui.Dialog().select(
            heading=heading, list=listitems, useDetails=True)
        if selection == -1:
            return None
        else:
            return listitems[selection]

    def _ask_dimming_level(self, current: int | None = None) -> int | None:

        preselect = 0
        heading = self.addon.getLocalizedString(32409)
        options: 'list[xbmcgui.ListItem]' = list()
        for i, level in enumerate(range(100, 0, -10)):
            if current is not None and current <= level:
                preselect = i

            options.append(util.createListItem(
                label=f"{level}%"))

        selection = xbmcgui.Dialog().select(
            heading=heading, list=options, preselect=preselect)

        if selection == -1:
            return None

        return 100 - 10 * selection

    def dimmingMenu(self) -> bool:

        pilot = self.pilotForCurrent()
        current = pilot.dimming if pilot else 10

        level = self._ask_dimming_level(current=current)
        if level is None:
            return False

        self.controller.withDimming(level)
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

            options.append(util.createListItem(
                label=f"{level}K"))

        selection = xbmcgui.Dialog().select(
            heading=heading, list=options, preselect=preselect)

        if selection == -1:
            return False

        temp = 2200 + 500 * selection
        self.controller.withTemp(temp)
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

        return True

    def sceneMenu(self) -> bool:

        pilot = self.pilotForCurrent()
        current = pilot.sceneId if pilot else 0
        xbmc.log(f"current scene {current}", xbmc.LOGINFO)
        preselect = 0

        heading = self.addon.getLocalizedString(32419)
        options: 'list[xbmcgui.ListItem]' = list()
        for i, sceneId in enumerate(wiz.Pilot.SCENES):

            preselect = i if sceneId == current else preselect
            options.append(util.createListItem(
                label=self.addon.getLocalizedString(32330 + i), icon=Wizard.SCENE_ICONS[sceneId] or "effect", command=[str(sceneId)]))

        selection = xbmcgui.Dialog().select(
            heading=heading, list=options, preselect=preselect, useDetails=True)

        if selection == -1:
            return False

        selectedScene = int(options[selection].getProperty("command"))
        if selectedScene:
            self.controller.withScene(scene=str(selectedScene))

        speed_used = None
        if wiz.Pilot.SCENES.get(selectedScene).get("speed"):
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

        if wiz.Pilot.SCENES.get(selectedScene).get("rgb"):
            if not self.colorMenu():
                return False

        if wiz.Pilot.SCENES.get(selectedScene).get("dimming"):
            if not self.dimmingMenu():
                return False

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
        return True

    def _ask_program_duration(self) -> int | None:

        while True:

            duration = xbmcgui.Dialog().numeric(
                2, self.addon.getLocalizedString(32546), "00:30")
            if duration in ["", "0:00", "00:00"]:
                return None

            try:
                return wiz.WizDeviceCLI.parse_program_duration(duration.strip())
            except Exception:
                continue

    def _ask_join_program(self, programs: list[wiz.Program]) -> dict:

        options: 'list[xbmcgui.ListItem]' = list()

        now = time.time()

        for program in programs:

            elapsed = int((now - program.start_time) / program.duration * 100)

            options.append(util.createListItem(
                label=", ".join([settings_util.get_name_by_IP(ip)
                                for ip in program.ip_addresses]),
                label2=f"{program.programID}, {datetime.fromtimestamp(program.start_time).strftime("%H:%M")}, {program.duration // 60}m, {elapsed}%",
                icon=Wizard.PROGRAM_ICONS[program.programID],
                command=[program.ip_addresses[0]] if program.ip_addresses else []))

        selection = xbmcgui.Dialog().select(
            heading=self.addon.getLocalizedString(32548), list=options, useDetails=True)
        if selection == -1:
            return None

        return {
            "program": "join",
            "ip_address": options[selection].getProperty("command")
        }

    def programMenu(self, allBulbs: bool, ip_addresses: list[str]) -> dict:

        def _is_intersect(programs: list[wiz.Program], ip_addresses: list[str]) -> bool:

            for program in programs:
                if not set(ip_addresses).isdisjoint(program.ip_addresses):
                    return True

            return False

        running_programs = settings_util.load_running_programs()

        options: 'list[xbmcgui.ListItem]' = list()

        _intersect = _is_intersect(
            programs=running_programs, ip_addresses=ip_addresses)

        if _intersect:
            options.append(util.createListItem(
                label=self.addon.getLocalizedString(32550), label2=self.addon.getLocalizedString(32551), icon="halt", command=["halt"]))

        if running_programs and not _intersect:
            options.append(util.createListItem(
                label=self.addon.getLocalizedString(32548), label2=self.addon.getLocalizedString(32549) % len(running_programs), icon="combine", command=["join"]))

        for i, program in enumerate(wiz.Program.PROGRAMS):
            options.append(util.createListItem(
                label=self.addon.getLocalizedString(32552 + i * 2), label2=self.addon.getLocalizedString(32553 + i * 2), icon=Wizard.PROGRAM_ICONS[program], command=[program]))
            if not allBulbs:
                break

        selection = xbmcgui.Dialog().select(
            heading=self.addon.getLocalizedString(32545), list=options, useDetails=True)
        if selection == -1:
            return None

        command = options[selection].getProperty("command")
        if not command:
            return None

        if command == "halt":
            return {
                "program": "halt"
            }

        elif command == "join":
            return self._ask_join_program(running_programs)

        if command not in wiz.Program.PROGRAMS:
            return None

        duration = self._ask_program_duration()
        if duration is None:
            return None

        if allBulbs:
            dimming = self._ask_dimming_level()
        else:
            dimming = None

        phase_shift = 0
        if command == wiz.Program.PROGRAM_INFINITE and allBulbs and len(ip_addresses) > 1:
            _shift = int(duration / len(ip_addresses))
            if xbmcgui.Dialog().yesno(
                heading=self.addon.getLocalizedString(32617),
                message=self.addon.getLocalizedString(32616) % _shift,
                nolabel=self.addon.getLocalizedString(32544),
                yeslabel=self.addon.getLocalizedString(32543),
            ):
                phase_shift = _shift

        return {
            "program": command,
            "duration": duration,
            "dimming": dimming,
            "phase_shift": phase_shift
        }

    def ask_request(self) -> dict:

        selectedListItems = self.selectDevices()
        if not selectedListItems:
            return None

        ip_addresses: list[str] = []
        for item in selectedListItems:
            ip_addresses.extend(item.getProperty("ipaddresses").split("|"))

        ip_addresses = list(dict.fromkeys(ip_addresses))
        allBulbs = self.isAllBulbs(ip_addresses=ip_addresses)
        request = {
            "ip_addresses": ip_addresses
        }

        li = self.deviceMenu(selectedListItems, allBulbs)
        if not li:
            return None

        command = li.getProperty("command")
        if command == "PROGRAM":
            request["program"] = self.programMenu(allBulbs, ip_addresses)

        else:
            if command == "ON":
                self.controller.withState(True)

            elif command == "OFF":
                self.controller.withState(False)

            elif command == "DIMMING":
                self.dimmingMenu()

            elif command == "TEMPERATURE":
                self.temperatureMenu() and self.dimmingMenu()

            elif command == "COLOR":
                self.colorMenu() and self.dimmingMenu()

            elif command == "SCENE":
                self.sceneMenu()

            elif command == "PULSE":
                self.pulseMenu()

            pilot = self.controller.commands.get("setPilot", None)
            if pilot:
                request["pilot"] = pilot

        return request

    def control(self) -> None:

        self.sync()

        while True:
            request = self.ask_request()

            if not request or (not request.get("pilot", None) and not request.get("program", None)):
                break

            settings_util.set_preselection(
                ip_addresses=request.get("ip_addresses", []))

            settings_util.write_request(request=request)
            if "pilot" in request:
                self.perform(request=request)
