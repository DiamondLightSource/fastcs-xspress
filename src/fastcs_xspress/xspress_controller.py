from fastcs.controllers import BaseController
from fastcs_odin.controllers import OdinController
from fastcs_odin.http_connection import HTTPConnection
from fastcs_odin.util import OdinParameter

from fastcs_xspress.xspress_adapter_controller import XspressAdapterController


class XspressController(OdinController):
    """A root ``Controller`` for an xspress control server."""

    def _create_adapter_controller(
        self,
        connection: HTTPConnection,
        parameters: list[OdinParameter],
        adapter: str,
        module: str,
    ) -> BaseController:
        match module:
            case "XspressAdapter":
                return XspressAdapterController(
                    connection, parameters, adapter, self._ios
                )

        return super()._create_adapter_controller(
            connection, parameters, adapter, module
        )
