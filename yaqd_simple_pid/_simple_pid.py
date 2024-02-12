__all__ = ["SimplePid"]

import asyncio
from typing import Dict, Any, List
import yaqc  # type: ignore

from simple_pid import PID

from yaqd_core import HasDependents, HasPosition, IsDaemon


class SimplePid(HasDependents, HasPosition, IsDaemon):
    _kind = "simple-pid"

    def __init__(self, name, config, config_filepath):
        super().__init__(name, config, config_filepath)
        self._pid = PID(
            Kp=self._config["kp"],
            Ki=self._config["ki"],
            Kd=self._config["kd"],
            proportional_on_measurement=self._config["proportional_on_measurement"],
        )
        self._sensor_daemon = yaqc.Client(
            host=self._config["sensor_daemon"]["host"], port=self._config["sensor_daemon"]["port"]
        )
        self._control_daemon = yaqc.Client(
            host=self._config["control_daemon"]["host"],
            port=self._config["control_daemon"]["port"],
        )

    def get_dependent_hardware(self) -> Dict:
        out = dict()
        out["sensor_daemon"] = f"{self._sensor_daemon._host}:{self._sensor_daemon._port}"
        out["control_daemon"] = f"{self._control_daemon._host}:{self._control_daemon._port}"
        return out

    def get_output(self) -> float:
        return self._state["output"]

    def reset(self):
        self_pid.reset()

    def _set_position(self, position):
        self._pid.setpoint = position

    async def update_state(self):
        while True:
            self._busy = False
            self._state["position"] = self._sensor_daemon.get_measured()[
                self._config["sensor_daemon"]["channel"]
            ]
            self._state["output"] = self._pid(self._state["position"])
            print(self._state["output"])
            self._control_daemon.set_position(self._state["output"])
            await asyncio.sleep(1)
