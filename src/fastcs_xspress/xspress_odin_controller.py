from fastcs.attributes import AttrR, AttrRW
from fastcs.controllers import BaseController
from fastcs.datatypes import Bool, String
from fastcs_odin.controllers import OdinController
from fastcs_odin.controllers.odin_data.meta_writer import MetaWriterAdapterController
from fastcs_odin.http_connection import HTTPConnection
from fastcs_odin.io import StatusSummaryAttributeIORef
from fastcs_odin.io.config_fan_sender_attribute_io import ConfigFanAttributeIORef
from fastcs_odin.io.status_summary_attribute_io import (
    initialise_summary_attributes,
)
from fastcs_odin.util import (
    REQUEST_METADATA_HEADER,
    OdinParameter,
    create_odin_parameters,
)

from fastcs_xspress.xspress_fp_adapter_controller import XspressFPAdapterController


class XspressOdinController(OdinController):
    """A root ``Controller`` for an xspress control server."""

    FP: XspressFPAdapterController
    MW: MetaWriterAdapterController
    writing = AttrR(
        Bool(), io_ref=StatusSummaryAttributeIORef([("MW", "FP")], "writing", any)
    )

    async def initialise(self):
        self.connection.open()

        adapters_response = await self.connection.get(f"{self.API_PREFIX}/adapters")
        match adapters_response:
            case {"adapters": [*adapter_list]}:
                # Expecting to always have at least xspress as one of the adapters
                adapter_list.pop(adapter_list.index("xspress"))
                adapters = tuple(a for a in adapter_list if isinstance(a, str))
                if len(adapters) != len(adapter_list):
                    raise ValueError(f"Received invalid adapters list:\n{adapter_list}")
            case _:
                raise ValueError(
                    f"Did not find valid adapters in response:\n{adapters_response}"
                )

        for adapter in adapters:
            # Get full parameter tree and split into parameters at the root and under
            # an index where there are N identical trees for each underlying process
            response = await self.connection.get(
                f"{self.API_PREFIX}/{adapter}", headers=REQUEST_METADATA_HEADER
            )
            # Extract the module name of the adapter
            match response:
                case {"module": {"value": str() as module}}:
                    pass
                case _:
                    module = ""

            adapter_controller = self._create_adapter_controller(
                self.connection, create_odin_parameters(response), adapter, module
            )
            if len(adapter) < 3:
                adapter = adapter.upper()
            self.add_sub_controller(adapter, adapter_controller)
            await adapter_controller.initialise()

        initialise_summary_attributes(self)

        self.file_path = AttrRW(
            String(),
            io_ref=ConfigFanAttributeIORef([self.FP.file_path, self.MW.directory]),
        )
        self.file_prefix = AttrRW(
            String(),
            io_ref=ConfigFanAttributeIORef(
                [
                    self.FP.file_prefix,
                    self.MW.file_prefix,
                    self.FP.acquisition_id,
                    self.MW.acquisition_id,
                    self.FP.acq_id,
                ]
            ),
        )

    def _create_adapter_controller(
        self,
        connection: HTTPConnection,
        parameters: list[OdinParameter],
        adapter: str,
        module: str,
    ) -> BaseController:
        match module:
            case "FrameProcessorAdapter":
                return XspressFPAdapterController(
                    connection, parameters, f"{self.API_PREFIX}/{adapter}", self._ios
                )
            case _:
                return super()._create_adapter_controller(
                    connection, parameters, adapter, module
                )
