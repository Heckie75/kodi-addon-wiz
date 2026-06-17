import json
import os
import time
import xbmcaddon
import xbmcvfs

from resources.lib.wiz import WizDevice, WizDeviceController, Program

_ON_SETTING_CHANGE_EVENTS = "on_setting_change_events"
_SETTING_CHANGE_EVENTS_MAX_SECS = 5

MAX_LOCATIONS = 10
MAX_DEVICES_PER_LOCATION = 7
MAX_DEVICES = MAX_LOCATIONS * MAX_DEVICES_PER_LOCATION


def deactivate_on_settings_changed_events() -> None:

    addon = xbmcaddon.Addon()
    now = str(int(time.time()))
    addon.setSetting(_ON_SETTING_CHANGE_EVENTS, now)


def activate_on_settings_changed_events() -> None:

    addon = xbmcaddon.Addon()
    addon.setSetting(_ON_SETTING_CHANGE_EVENTS, "0")


def is_settings_changed_events() -> bool:

    addon = xbmcaddon.Addon()
    current = int("0%s" % addon.getSetting(_ON_SETTING_CHANGE_EVENTS))
    now = int(time.time())
    return now - current > _SETTING_CHANGE_EVENTS_MAX_SECS


def trigger_settings_changed_event() -> None:

    deactivate_on_settings_changed_events()
    activate_on_settings_changed_events()


def write_request(request: dict = None, silent: bool = False) -> None:

    deactivate_on_settings_changed_events()
    xbmcaddon.Addon().setSetting("request", json.dumps(request) if request else "")

    if not silent:
        trigger_settings_changed_event()


def reset_request() -> None:

    write_request(silent=True)


def set_preselection(ip_addresses: 'list[str]') -> None:

    deactivate_on_settings_changed_events()

    addon = xbmcaddon.Addon()
    addon.setSetting("preselect", "|".join(ip_addresses))


def get_preselection() -> list[str]:

    addon = xbmcaddon.Addon()
    return addon.getSetting("preselect").split("|")


def update_locations(devices: list[WizDevice]) -> None:

    addon = xbmcaddon.Addon()

    knownLocations = get_locations()
    freeLocations = [i for i in range(
        MAX_LOCATIONS) if addon.getSetting(f"room_{i}_id") == ""]

    seenLocations = set(
        [(d.system_config.room_id, d.system_config.group_id) for d in devices if d.system_config])
    for seenLocation in seenLocations:
        if not freeLocations:
            break

        if seenLocation in knownLocations:
            continue

        i = freeLocations.pop(0)
        addon.setSetting(f"room_{i}_id", str(seenLocation[0]))
        addon.setSetting(f"group_{i}_id", str(seenLocation[1]))
        addon.setSetting(f"location_{i}_name", "")


def get_locations() -> dict[tuple[int, int], str]:

    addon = xbmcaddon.Addon()
    locations = dict()
    for i in range(MAX_LOCATIONS):
        room_id = int(addon.getSetting(f"room_{i}_id") or -1)
        group_id = int(addon.getSetting(f"group_{i}_id") or -1)
        name = addon.getSetting(f"location_{i}_name")
        if room_id != -1:
            locations[(room_id, group_id)] = name

    return locations


def get_location_name(room_id: int, group_id: int) -> str:

    locations = get_locations()
    return locations[(room_id, group_id)] if (room_id, group_id) in locations else f"{room_id}_{group_id}"


def get_location_id(room_id: int, group_id: int) -> int | None:

    for i in range(MAX_LOCATIONS):
        if xbmcaddon.Addon().getSetting(f"room_{i}_id") == str(room_id) and xbmcaddon.Addon().getSetting(f"group_{i}_id") == str(group_id):
            return i

    return None


def get_location_wiz_prefix(location_id: int, device: int) -> str:

    return f"location_{location_id}_wiz_{device}"


def get_location_device_prefixes(room_id: int, group_id: int) -> list[str]:

    location_id = get_location_id(room_id, group_id)
    if location_id is None:
        return []

    prefixes: list[str] = []
    for device in range(MAX_DEVICES_PER_LOCATION):
        prefixes.append(get_location_wiz_prefix(location_id, device))

    return prefixes


def get_enabled_prefixes_for_location(location_id: int) -> list[str]:

    addon = xbmcaddon.Addon()
    prefixes: list[str] = []
    for device in range(MAX_DEVICES_PER_LOCATION):
        prefix = get_location_wiz_prefix(location_id, device)
        if addon.getSettingBool(f"{prefix}_enable"):
            prefixes.append(prefix)

    prefixes.sort(key=lambda key: addon.getSettingInt(f"{key}_order"))
    return prefixes


def get_location_ip_addresses(location_id: int) -> list[str]:

    addon = xbmcaddon.Addon()
    ip_addresses: list[str] = []
    for prefix in get_enabled_prefixes_for_location(location_id):
        ip_address = addon.getSettingString(f"{prefix}_ipaddress")
        if ip_address:
            ip_addresses.append(ip_address)

    return list(dict.fromkeys(ip_addresses))


def get_enabled_location_ids() -> list[int]:

    addon = xbmcaddon.Addon()
    location_ids: list[int] = []
    for location_id in range(MAX_LOCATIONS):
        if addon.getSetting(f"room_{location_id}_id") == "":
            continue
        if not addon.getSettingBool(f"location_{location_id}_show_as_location"):
            continue
        if get_location_ip_addresses(location_id):
            location_ids.append(location_id)

    location_ids.sort(key=lambda key: addon.getSettingInt(
        f"location_{key}_order"))
    return location_ids


def get_all_device_prefixes() -> list[str]:

    prefixes: list[str] = []
    for location_id in range(MAX_LOCATIONS):
        for device in range(MAX_DEVICES_PER_LOCATION):
            prefixes.append(get_location_wiz_prefix(location_id, device))

    return prefixes


def get_enabled_device_prefixes() -> list[str]:

    addon = xbmcaddon.Addon()

    locations = [i for i in range(MAX_LOCATIONS)
                 if addon.getSetting(f"room_{i}_id") != ""]
    locations.sort(key=lambda key: addon.getSettingInt(
        f"location_{key}_order"))

    prefixes: list[str] = []
    for location in locations:
        location_prefixes: list[str] = []
        for device in range(MAX_DEVICES_PER_LOCATION):
            if addon.getSettingBool(f"location_{location}_wiz_{device}_enable"):
                location_prefixes.append(f"location_{location}_wiz_{device}")

        location_prefixes.sort(
            key=lambda key: addon.getSettingInt(f"{key}_order"))
        prefixes.extend(location_prefixes)

    return prefixes


def get_free_device_prefixes_for_location(room_id: int, group_id: int) -> list[str]:

    addon = xbmcaddon.Addon()
    free_prefixes: list[str] = []
    for prefix in get_location_device_prefixes(room_id, group_id):
        if not addon.getSettingBool(f"{prefix}_enable"):
            free_prefixes.append(prefix)

    return free_prefixes


def get_device_IPs_from_settings() -> list[str]:

    addon = xbmcaddon.Addon()
    device_ips: list[str] = []
    for prefix in get_enabled_device_prefixes():
        ip_address = addon.getSettingString(f"{prefix}_ipaddress")
        if ip_address:
            device_ips.append(ip_address)

    return list(dict.fromkeys(device_ips))


def get_name_by_IP(ip_address: str) -> str:

    addon = xbmcaddon.Addon()
    for prefix in get_all_device_prefixes():
        if addon.getSettingString(f"{prefix}_ipaddress") == ip_address:
            return addon.getSettingString(f"{prefix}_name")

    return ip_address


def _get_storage_path() -> str:

    addon = xbmcaddon.Addon()
    profile_path = xbmcvfs.translatePath(addon.getAddonInfo('profile'))
    return os.path.join(profile_path, "running_programs.json")


def save_running_programs(programs: list[Program]) -> None:

    path = _get_storage_path()
    with xbmcvfs.File(path, "w") as file:
        file.write(json.dumps([program.to_dict() for program in programs]))


def load_running_programs() -> list[Program]:

    programs = []
    path = _get_storage_path()

    if not xbmcvfs.exists(path=path):
        return programs

    with open(path, "r") as file:
        json_ = json.loads("\n".join(file.readlines()))
        for j in json_:
            programs.append(Program.from_json(json_=j))

    return programs


def delete_running_programs() -> None:

    path = _get_storage_path()
    if xbmcvfs.exists(path):
        xbmcvfs.delete(path)


def transform_url_params_to_request(params: dict) -> dict:

    if "pilot" in params:
        pass

    elif "program" in params:

        program = {
            "program": params["program"][0]
        }

        if "dimming" in params:
            program["dimming"] = int(params["dimming"][0])
        if "duration" in params:
            program["duration"] = int(params["duration"][0])
        if "phase_shift" in params:
            program["phase_shift"] = int(params["phase_shift"][0])
        if "offset" in params:
            program["offset"] = int(params["offset"][0])

        request = {
            "ip_addresses": params["ip_addresses"][0].split(";"),
            "program": program
        }
        return request

    return {}
