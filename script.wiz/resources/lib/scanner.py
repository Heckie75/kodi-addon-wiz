import xbmcaddon
import xbmcgui
from resources.lib.util import createListItem, getIconPath
from resources.lib.settings_util import get_locations, update_locations, get_free_device_prefixes_for_location, get_location_name, get_all_device_prefixes
from resources.lib.wiz import WizDeviceController, WizDevice, WiZListener, Features


class Scanner(WiZListener):

    def __init__(self):

        self.addon = xbmcaddon.Addon()
        self.progress = xbmcgui.DialogProgressBG()
        self.knownLocations = get_locations()

    def onMessageReceived(self, ip_address: str, message: str):

        self.progress.update(
            message=self.addon.getLocalizedString(32053), percent=90)

    def scan(self):

        def _createListItem(device: WizDevice) -> xbmcgui.ListItem:

            return createListItem(label=f"{Features.fromModuleName(device.system_config.module_name).getFeaturesDescription()}",
                                  label2=f"{self.knownLocations.get((device.system_config.room_id, device.system_config.group_id), self.addon.getLocalizedString(32052))} / {device.ip_address} / {WizDevice.formatted_mac(device.system_config.mac)}", icon="socket" if "SOCKET" in device.system_config.module_name else "bulb")

        def _get_idx_of_unknown_devs(devices: list[WizDevice]) -> list[int]:

            known_macs = [self.addon.getSetting(
                f"{prefix}_mac") for prefix in get_all_device_prefixes()]
            return [i for i, d in enumerate(devices) if WizDevice.formatted_mac(d.system_config.mac) not in known_macs]

        try:
            self.progress.create(heading=self.addon.getLocalizedString(32001),
                                 message=self.addon.getLocalizedString(32051))

            controller = WizDeviceController(
                ip_addresses=["255.255.255.255"], listener=self)
            controller.getSystemConfig().perform()

            devices: list[WizDevice] = [
                d for d in controller.devices if d.system_config]

        finally:
            self.progress.close()

        if not devices:
            xbmcgui.Dialog().ok(heading=self.addon.getLocalizedString(
                32001), message=self.addon.getLocalizedString(32054))

        else:
            update_locations(devices)

            options: 'list[xbmcgui.ListItem]' = [
                _createListItem(device) for device in devices if device.system_config]
            selection = xbmcgui.Dialog().multiselect(heading=self.addon.getLocalizedString(32055),
                                                     options=options, useDetails=True, preselect=_get_idx_of_unknown_devs(devices))

            if not selection:
                return

            for s in selection:
                room_id = devices[s].system_config.room_id
                group_id = devices[s].system_config.group_id
                free_prefixes = get_free_device_prefixes_for_location(
                    room_id, group_id)

                if not free_prefixes:
                    break

                features = Features.fromModuleName(
                    devices[s].system_config.module_name)

                prefix = free_prefixes.pop(0)
                self.addon.setSetting(
                    f"{prefix}_ipaddress", devices[s].ip_address)
                self.addon.setSetting(
                    f"{prefix}_mac", WizDevice.formatted_mac(devices[s].system_config.mac))
                self.addon.setSetting(
                    f"{prefix}_name", f"{devices[s].system_config.module_name} in {get_location_name(room_id, group_id)}")
                self.addon.setSettingBool(f"{prefix}_enable", True)
                self.addon.setSetting(
                    f"{prefix}_type", features.getFeaturesDescription())
                self.addon.setSetting(
                    f"{prefix}_icon", features.device_type.lower())
                self.addon.setSettingInt(f"{prefix}_order", 1)

            if selection:
                xbmcgui.Dialog().notification(heading=self.addon.getLocalizedString(32001),
                                              message=self.addon.getLocalizedString(32056) % len(selection), icon=getIconPath("default"), time=5000)
