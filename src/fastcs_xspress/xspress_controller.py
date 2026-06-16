from fastcs.attributes import AttrR, AttrRW
from fastcs.controllers import BaseController
from fastcs.datatypes import Bool, String
from fastcs_odin.controllers import OdinController
from fastcs_odin.controllers.odin_data.meta_writer import MetaWriterAdapterController
from fastcs_odin.http_connection import HTTPConnection
from fastcs_odin.io import StatusSummaryAttributeIORef
from fastcs_odin.io.config_fan_sender_attribute_io import ConfigFanAttributeIORef
from fastcs_odin.util import OdinParameter

from fastcs_xspress.xspress_adapter_controller import XspressAdapterController
from fastcs_xspress.xspress_fp_adapter_controller import XspressFPAdapterController


class XspressController(OdinController):
    """A root ``Controller`` for an xspress control server."""

    FP: XspressFPAdapterController
    MW: MetaWriterAdapterController
    writing = AttrR(
        Bool(), io_ref=StatusSummaryAttributeIORef([("MW", "FP")], "writing", any)
    )

    async def initialise(self):
        await super().initialise()
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
            case "XspressAdapter":
                return XspressAdapterController(
                    connection, parameters, f"{self.API_PREFIX}/{adapter}", self._ios
                )
            case "FrameProcessorAdapter":
                return XspressFPAdapterController(
                    connection, parameters, f"{self.API_PREFIX}/{adapter}", self._ios
                )

        return super()._create_adapter_controller(
            connection, parameters, adapter, module
        )
