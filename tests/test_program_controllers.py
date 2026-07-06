import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "script.wiz" / "resources" / "lib"))

from wiz import Program, WizDeviceController


class FakeController:
    def __init__(self, ip_addresses: list[str]) -> None:
        self.ip_addresses = list(ip_addresses)
        self.reset_calls = 0
        self.perform_calls = 0
        self.payloads: list[dict] = []

    def resetCommands(self) -> None:
        self.reset_calls += 1

    def setPilot(self, payload: dict) -> "FakeController":
        self.payloads.append(payload)
        return self

    def perform(self) -> None:
        self.perform_calls += 1


def test_phase_shift_program_uses_one_controller_per_ip_address() -> None:
    controller = WizDeviceController(ip_addresses=["192.168.0.10", "192.168.0.11"])

    program = Program(
        controller,
        programID=Program.PROGRAM_FADE,
        duration=60,
        phase_shift=10,
    )

    assert len(program.controllers) == 2
    assert [ctrl.ip_addresses for ctrl in program.controllers] == [["192.168.0.10"], ["192.168.0.11"]]
    assert program.ip_addresses == ["192.168.0.10", "192.168.0.11"]


def test_non_phase_shift_program_keeps_single_controller_for_multiple_ips() -> None:
    controller = WizDeviceController(ip_addresses=["192.168.0.10", "192.168.0.11"])

    program = Program(
        controller,
        programID=Program.PROGRAM_FADE,
        duration=60,
        phase_shift=0,
    )

    assert len(program.controllers) == 1
    assert program.controllers[0].ip_addresses == ["192.168.0.10", "192.168.0.11"]
    assert program.ip_addresses == ["192.168.0.10", "192.168.0.11"]


def test_add_and_remove_ip_addresses_update_program_controllers() -> None:
    program = Program(
        WizDeviceController(ip_addresses=["192.168.0.10"]),
        programID=Program.PROGRAM_FADE,
        duration=60,
        phase_shift=0,
    )

    program.add_ip_addresses(["192.168.0.11"])
    assert program.ip_addresses == ["192.168.0.10", "192.168.0.11"]
    assert program.controllers[0].ip_addresses == ["192.168.0.10", "192.168.0.11"]

    program.remove_ip_address("192.168.0.10")
    assert program.ip_addresses == ["192.168.0.11"]
    assert program.controllers[0].ip_addresses == ["192.168.0.11"]


def test_perform_pilot_iterates_all_controllers() -> None:
    program = Program(
        WizDeviceController(ip_addresses=["192.168.0.10", "192.168.0.11"]),
        programID=Program.PROGRAM_FADE,
        duration=60,
        phase_shift=10,
    )

    controller_a = FakeController(["192.168.0.10"])
    controller_b = FakeController(["192.168.0.11"])
    program.controllers = [controller_a, controller_b]

    program.performPilot(elapsed=1)

    assert controller_a.perform_calls == 1
    assert controller_b.perform_calls == 1
    assert controller_a.reset_calls == 1
    assert controller_b.reset_calls == 1
    assert len(controller_a.payloads) == 1
    assert len(controller_b.payloads) == 1


def test_program_round_trip_serialization_preserves_controller_targets() -> None:
    program = Program(
        WizDeviceController(ip_addresses=["192.168.0.10", "192.168.0.11"]),
        programID=Program.PROGRAM_INFINITE,
        duration=120,
        phase_shift=10,
    )

    serialized = program.to_dict()
    restored = Program.from_json(serialized)

    assert restored.programID == program.programID
    assert restored.duration == program.duration
    assert restored.phase_shift == program.phase_shift
    assert restored.ip_addresses == ["192.168.0.10", "192.168.0.11"]
    assert len(restored.controllers) == 2


def test_infinite_program_wraps_elapsed_time() -> None:
    program = Program(
        WizDeviceController(ip_addresses=["192.168.0.10"]),
        programID=Program.PROGRAM_INFINITE,
        duration=20,
        phase_shift=0,
    )

    pilot_at_5 = program.get_pilot(5)
    pilot_at_25 = program.get_pilot(25)

    assert pilot_at_5.to_dict() == pilot_at_25.to_dict()


def test_sunrise_program_dimming_increases_between_intervals() -> None:
    program = Program(
        WizDeviceController(ip_addresses=["192.168.0.10"]),
        programID=Program.PROGRAM_SUNRISE,
        duration=120,
        phase_shift=0,
    )

    early = program.get_pilot(1)
    mid = program.get_pilot(30)
    later = program.get_pilot(50)

    assert early.dimming <= mid.dimming <= later.dimming
    assert early.r == 0 and early.g == 0 and early.b == 0
    assert mid.dimming >= 10
    assert later.dimming >= mid.dimming
