import xbmc
import xbmcaddon
import xbmcgui
from resources.lib.util import MAX_DEVICES, createListItem, updateRooms, getRooms, getRoomById
from resources.lib.wiz import WizDeviceController, WizDevice, WiZListener, Features


class Scanner(WiZListener):

    def __init__(self):

        self.addon = xbmcaddon.Addon()
        self.progress = xbmcgui.DialogProgressBG()
        self.knownRooms = getRooms()

    def onDiscoverFound(self, device):

        self.progress.update(
            message=self.addon.getLocalizedString(32053), percent=90)

    def scan(self):

        def _createListItem(device: WizDevice) -> xbmcgui.ListItem:

            return createListItem(label=f"{Features.fromModuleName(device.system_config.module_name).getFeaturesDescription()}",
                                  label2=f"{self.knownRooms[str(device.system_config.room_id)] if str(device.system_config.room_id) in self.knownRooms else self.addon.getLocalizedString(32052)} / {device.ip_address} / {WizDevice.formatted_mac(device.system_config.mac)}", icon="socket" if "SOCKET" in device.system_config.module_name else "bulb")

        def _get_idx_of_unknown_devs(devices: list[WizDevice]) -> list[int]:

            known_macs = [self.addon.getSetting(
                f"wiz_{i}_mac") for i in range(MAX_DEVICES)]
            return [i for i, d in enumerate(devices) if WizDevice.formatted_mac(d.system_config.mac) not in known_macs]

        try:
            self.progress.create(heading=self.addon.getLocalizedString(32001),
                                 message=self.addon.getLocalizedString(32051))
            devices: list[WizDevice] = WizDeviceController.discover_wiz_devices(
                listener=self)

        finally:
            self.progress.close()

        if not devices:
            xbmcgui.Dialog().ok(heading=self.addon.getLocalizedString(
                32001), message=self.addon.getLocalizedString(32054))

        else:
            updateRooms(devices)

            options: 'list[xbmcgui.ListItem]' = [
                _createListItem(device) for device in devices]
            selection = xbmcgui.Dialog().multiselect(heading=self.addon.getLocalizedString(32055),
                                                     options=options, useDetails=True, preselect=_get_idx_of_unknown_devs(devices))

            xbmc.log(str(selection), xbmc.LOGINFO)

            if not selection:
                return

            freeDevices = [i for i in range(
                MAX_DEVICES) if "false" == self.addon.getSetting(f"wiz_{i}_enable")]

            for s in selection:
                xbmc.log(f"selection {str(s)}", xbmc.LOGINFO)
                if not freeDevices:
                    break

                features = Features.fromModuleName(
                    devices[s].system_config.module_name)

                i = freeDevices.pop(0)
                xbmc.log(f"i={i}", xbmc.LOGINFO)
                self.addon.setSetting(
                    f"wiz_{i}_ipaddress", devices[s].ip_address)
                self.addon.setSetting(
                    f"wiz_{i}_mac", WizDevice.formatted_mac(devices[s].system_config.mac))
                self.addon.setSetting(
                    f"wiz_{i}_name", f"{devices[s].system_config.module_name} in {getRoomById(devices[s].system_config.room_id)}")
                self.addon.setSettingBool(f"wiz_{i}_enable", True)
                self.addon.setSetting(
                    f"wiz_{i}_type", features.getFeaturesDescription())
                self.addon.setSetting(
                    f"wiz_{i}_icon", features.device_type.lower())
                self.addon.setSettingInt(f"wiz_{i}_order", 1)
