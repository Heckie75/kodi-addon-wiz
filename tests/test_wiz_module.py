import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "script.wiz" / "resources" / "lib"))

from wiz import Pilot, Power, WizDevice, WizDeviceCLI


def test_pilot_from_json_and_to_payload() -> None:
    pilot = Pilot.from_json({
        "state": True,
        "r": 255,
        "g": 128,
        "b": 0,
        "dimming": 55,
        "sceneId": 11,
        "speed": 2,
        "mac": "aa:bb:cc:dd:ee:ff"
    })

    assert pilot.state is True
    assert pilot.r == 255
    assert pilot.g == 128
    assert pilot.b == 0
    assert pilot.dimming == 55
    assert pilot.sceneId == 11
    assert pilot.speed == 2
    assert pilot.mac == "aa:bb:cc:dd:ee:ff"

    assert pilot.to_payload() == {
        "state": True,
        "r": 255,
        "g": 128,
        "b": 0,
        "dimming": 55,
        "sceneId": 11,
        "speed": 2
    }

    assert pilot.to_dict()["mac"] == "aa:bb:cc:dd:ee:ff"

    same_pilot = Pilot.from_json({"state": True})
    assert not pilot.equals(same_pilot)
    assert pilot.equals(pilot)


def test_pilot_color_str_and_scene_helpers() -> None:
    pilot = Pilot()
    pilot.state = True
    pilot.r = 255
    pilot.g = 0
    pilot.b = 0
    pilot.dimming = 30

    assert pilot.color_str() == "Red (very dim) rgb(255, 0, 0)"
    assert "warm white" in Pilot.scene_list()[0].lower()

    pilot.sceneId = 11
    pilot.speed = 5
    assert "warm white" in pilot.scene_str().lower()
    assert "11" in pilot.scene_str()
    assert "speed: 5" in pilot.scene_str()


def test_wiz_device_mac_formatting() -> None:
    assert WizDevice.formatted_mac("aabbccddeeff") == "AA:BB:CC:DD:EE:FF"
    assert WizDevice.formatted_mac("aa:bb:cc:dd:ee:ff") == "AA:BB:CC:DD:EE:FF"
    assert WizDevice.formatted_mac("invalid") == "n/a"
    assert WizDevice.formatted_mac("") == "n/a"


def test_parse_program_duration_valid_and_invalid() -> None:
    assert WizDeviceCLI.parse_program_duration("3") == 180
    assert WizDeviceCLI.parse_program_duration("01:30") == 5400
    assert WizDeviceCLI.parse_program_duration("24:00") == 86400

    with pytest.raises(ValueError):
        WizDeviceCLI.parse_program_duration("00:00")

    with pytest.raises(ValueError):
        WizDeviceCLI.parse_program_duration("25:00")


def test_power_from_json_and_to_dict() -> None:
    power = Power.from_json({"power": 123})

    assert power.power == 123
    assert power.to_dict() == {"power": 123}


def test_wiz_device_to_dict_with_no_subobjects() -> None:
    device = WizDevice(ip_address="192.168.0.10")
    data = device.to_dict()

    assert data["ip_address"] == "192.168.0.10"
    assert data["device_info"] is None
    assert data["pilot"] is None
    assert data["power"] is None
