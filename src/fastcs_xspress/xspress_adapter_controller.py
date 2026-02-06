from fastcs_odin.controllers.odin_adapter_controller import OdinAdapterController
from fastcs_odin.controllers.odin_subcontroller import OdinSubController
from fastcs_odin.util import (
    OdinParameter,
    create_attribute,
    partition,
    unpack_status_arrays,
)

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


group_names = {
    "det": [
        "manufacturer",
        "model",
        "max_channels",
        "mca_channels",
        "max_spectra",
        "username",
        "endpoint",
        "error",
        "state",
    ],
}

group_det = [
    "manufacturer",
    "model",
    "max_channels",
    "mca_channels",
    "max_spectra",
    "username",
    "endpoint",
    "error",
    "state",
]


def get_group_name(parameter: OdinParameter) -> str:
    if parameter.name in group_det:
        return "Detector"
    return ""


class XspressAdapterController(OdinAdapterController):
    """SubController for an Xspress adapter in an odin control server."""

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

        scalar_parameters, self.parameters = partition(
            self.parameters,
            lambda p: (p.path[0].startswith("sca") or p.path[0].startswith("inp")),
        )

        dtc_parameters, self.parameters = partition(
            self.parameters, lambda p: p.path[0].startswith("dtc")
        )

        self.scalar_controller = OdinSubController(
            self.connection,
            scalar_parameters,
            f"{self._api_prefix}",
            self._ios,
        )

        self.dtc_controller = OdinSubController(
            self.connection,
            dtc_parameters,
            f"{self._api_prefix}",
            self._ios,
        )

        for parameter in self.parameters:
            self.add_attribute(
                parameter.name,
                create_attribute(
                    parameter=parameter,
                    api_prefix=self._api_prefix,
                    group=get_group_name(parameter=parameter),
                ),
            )

        await self.scalar_controller.initialise()
        await self.dtc_controller.initialise()
        await self._create_commands()
