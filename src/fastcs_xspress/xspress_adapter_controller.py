from fastcs_odin.controllers.odin_adapter_controller import OdinAdapterController
from fastcs_odin.util import unpack_status_arrays

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

    async def initialise(self):
        self.parameters = unpack_status_arrays(
            parameters=self.parameters, uris=uri_list
        )

        await self._create_attributes()
