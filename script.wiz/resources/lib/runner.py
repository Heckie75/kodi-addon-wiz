import json
import threading
import time

import xbmc
import xbmcaddon
import xbmcgui

from resources.lib import wiz
from resources.lib.settings_util import is_settings_changed_events, reset_request, get_name_by_IP, save_running_programs, delete_running_programs
from resources.lib.util import getIconPath


class WizRunner(xbmc.Monitor):

    def __init__(self):

        xbmc.Monitor.__init__(self)
        self.addon = xbmcaddon.Addon()
        self._programs: list[wiz.Program] = []
        self.lock = threading.Lock()
        reset_request()

    def _is_broadcast(self, ip_address: str) -> bool:

        return ip_address.endswith(".255")

    def _update_programs(self, ip_addresses: list[str], halt: bool, dimming: int | None) -> None:

        for program in self._programs[:]:
            for ip_address in ip_addresses:
                if program.has_ip_address(ip_address):
                    if dimming:
                        program.dimming = dimming
                        xbmc.log(
                            f"Set dimming for {ip_address} from running program {program}", xbmc.LOGINFO)
                    else:
                        program.remove_ip_address(ip_address)
                        xbmc.log(
                            f"Removed IP {ip_address} from running program {program}", xbmc.LOGINFO)

                    if halt:
                        halt_program = wiz.Program(wizController=wiz.WizDeviceController(ip_addresses=[
                                                   ip_address]), programID=program.programID, duration=program.duration, dimming=program.dimming, phase_shift=program.phase_shift)
                        self.stopProgram(program=halt_program)
                        xbmc.log(
                            f"[script.wiz] halted program {halt_program} for IP {ip_address}", xbmc.LOGINFO)

                    if not program.controllers:
                        xbmc.log(
                            f"[script.wiz] no more target IPs for program {program}, stopping it", xbmc.LOGINFO)
                        self._programs.remove(program)
                        break
                elif self._is_broadcast(ip_address):
                    self.stopProgram(program=program)
                    self._programs.remove(program)
                    xbmc.log(
                        f"[script.wiz] halted program {program}", xbmc.LOGINFO)
                    break

    def _join_program(self, request: dict) -> bool:

        for program in self._programs:

            if request["program"]["ip_address"] in program.ip_addresses:
                program.add_ip_addresses(request["ip_addresses"])
                return True

        return False

    def stopProgram(self, program: wiz.Program) -> None:

        with self.lock:
            try:
                program.end()
            except Exception as ex:
                xbmc.log(f"{ex}", xbmc.LOGWARNING)

    def onSettingsChanged(self):

        if not is_settings_changed_events():
            return

        request_str = self.addon.getSetting("request")

        if not request_str:
            return

        request = json.loads(request_str)

        ip_addresses = request.get("ip_addresses", [])
        device_names = ", ".join([get_name_by_IP(ip) for ip in ip_addresses])

        program = request.get("program", None)
        pilot = request.get("pilot", None)

        halt = program and program["program"] == "halt"
        is_only_dimming = pilot and pilot.keys() == {"dimming"}
        self._update_programs(ip_addresses=ip_addresses, halt=halt,
                              dimming=pilot["dimming"] if is_only_dimming else None)

        controller = wiz.WizDeviceController(ip_addresses=ip_addresses)

        if program and program["program"] == "join":
            self._join_program(request)

        elif halt:
            xbmcgui.Dialog().notification(heading=self.addon.getLocalizedString(
                32547), message=device_names, icon=getIconPath("halt"), time=5000)

        elif program:
            new_program = wiz.Program(controller, programID=program.get(
                "program", ""), duration=program.get("duration", 60), dimming=program.get("dimming", None), phase_shift=program.get("phase_shift", 0))
            new_program.initialize(offset=program.get("offset", 0))
            self._programs.append(new_program)
            xbmcgui.Dialog().notification(heading=self.addon.getLocalizedString(
                32545), message=device_names, icon=getIconPath("program"), time=5000)
            xbmc.log(
                f"[script.wiz] added new program {new_program}", xbmc.LOGINFO)


        elif pilot:
            # controller.commands["setPilot"] = pilot
            # controller.perform()
            pass

        save_running_programs(self._programs)
        reset_request()

    def start(self):

        while not self.abortRequested():

            longest_running = 0
            before_perform = time.time()
            with self.lock:
                longest_running = 0
                for program in self._programs[:]:

                    elapsed = int(time.time() - program.start_time)
                    if program.programID == wiz.Program.PROGRAM_INFINITE:
                        elapsed = elapsed % program.duration

                    try:
                        program.performPilot(elapsed=elapsed)
                    except Exception as ex:
                        xbmc.log(f"[script.wiz] {ex}", xbmc.LOGWARNING)

                    if elapsed >= program.duration:
                        self._programs.remove(program)
                        save_running_programs(self._programs)
                        xbmc.log(
                            f"[script.wiz] program {program} has run out, stopping it", xbmc.LOGINFO)
                    else:
                        longest_running = max(
                            program.start_time + program.duration, longest_running)

            if self.waitForAbort(max(.1, 1 - (time.time() - before_perform)) + (0 if self._programs else 4)):
                break

        for program in self._programs:
            xbmc.log(
                f"[script.wiz] finalize program on exit: {program}", xbmc.LOGINFO)
            self.stopProgram(program=program)

        delete_running_programs()
