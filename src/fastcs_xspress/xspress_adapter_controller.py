from fastcs_odin.controllers.odin_adapter_controller import OdinAdapterController
from fastcs_odin.controllers.odin_subcontroller import OdinSubController
from fastcs_odin.util import partition, unpack_status_arrays

uri_list = [
    ["status", "scalar_0"],
    ["status", "scalar_1"],
    ["status", "scalar_2"],
    ["status", "scalar_3"],
    ["status", "scalar_4"],
    ["status", "scalar_5"],
    ["status", "scalar_6"],
    ["status", "scalar_7"],
    ["status", "scalar_8"],
    ["status", "dtc"],
    ["status", "inp_est"],
]


class XspressAdapterController(OdinAdapterController):
    """SubController for an Xspress adapter in an odin control server."""

    _subcontroller_cls: type[OdinSubController] = OdinSubController

    async def initialise(self):
        # Unpack all the status parameters
        self.parameters = unpack_status_arrays(
            parameters=self.parameters, uris=uri_list
        )

        # Change path for all status and config parameters
        for parameter in self.parameters:
            # Remove 0 index and status/config
            match parameter.uri:
                case ["status" | "config", *_]:
                    parameter.set_path(parameter.path[1:])

        status_parameters, self.parameters = partition(
            self.parameters, lambda p: "status" in p.uri
        )

        config_parameters, self.parameters = partition(
            self.parameters, lambda p: "config" in p.uri
        )

        self.status_controller = self._subcontroller_cls(
            self.connection,
            status_parameters,
            f"{self._api_prefix}",
            self._ios,
        )

        self.config_controller = self._subcontroller_cls(
            self.connection,
            config_parameters,
            f"{self._api_prefix}",
            self._ios,
        )

        await self.status_controller.initialise()
        await self.config_controller.initialise()
        await self._create_attributes()
        await self._create_commands()
