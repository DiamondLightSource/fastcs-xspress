from fastcs.connections.ip_connection import IPConnectionSettings
from fastcs.controller import Controller
from fastcs.datatypes import Bool, Float, Int, String
from fastcs_odin.http_connection import HTTPConnection
from fastcs_odin.util import create_odin_parameters

from fastcs_xspress.xspress_adapter_controller import XspressAdapterController

types = {"float": Float(), "int": Int(), "bool": Bool(), "str": String()}

REQUEST_METADATA_HEADER = {"Accept": "application/json;metadata=true"}


class AdapterResponseError(Exception): ...


class XspressController(Controller):
    """A root ``Controller`` for an xspress control server."""

    API_PREFIX = "api/0.1"

    def __init__(self, settings: IPConnectionSettings) -> None:
        super().__init__()

        self.connection = HTTPConnection(settings.ip, settings.port)

    async def initialise(self) -> None:
        self.connection.open()

        response = await self.connection.get(
            f"{self.API_PREFIX}/xspress", headers=REQUEST_METADATA_HEADER
        )

        adapter_controller = XspressAdapterController(
            self.connection,
            create_odin_parameters(response),
            f"{self.API_PREFIX}/xspress",
        )

        self.register_sub_controller("XSPRESS", adapter_controller)
        await adapter_controller.initialise()

        await self.connection.close()

    async def connect(self) -> None:
        self.connection.open()
