import asyncio

from fastcs.connections.ip_connection import IPConnectionSettings
from fastcs.controllers import BaseController, Controller
from fastcs_odin.controllers import OdinController
from fastcs_odin.http_connection import HTTPConnection
from fastcs_odin.io.status_summary_attribute_io import (
    initialise_summary_attributes,
)
from fastcs_odin.util import (
    OdinParameter,
    create_odin_parameters,
)

from fastcs_xspress.xspress_adapter_controller import XspressAdapterController
from fastcs_xspress.xspress_odin_controller import XspressOdinController


class XspressController(OdinController):
    """A root ``Controller`` for an xspress control server."""

    def __init__(self, settings: IPConnectionSettings):
        super().__init__(settings)
        self.OD = XspressOdinController(settings)

    async def initialise(self):
        self.connection.open()
        response = await self.connection.get(f"{self.API_PREFIX}/xspress")
        xsp_adapter_controller = XspressAdapterController(
            self.connection,
            create_odin_parameters(response),
            f"{self.API_PREFIX}/xspress",
            self._ios,
        )
        self.add_sub_controller("xspress", xsp_adapter_controller)
        await asyncio.gather(self.OD.initialise(), xsp_adapter_controller.initialise())
