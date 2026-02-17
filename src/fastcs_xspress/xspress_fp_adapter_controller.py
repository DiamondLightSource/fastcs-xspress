import logging

from fastcs.attributes import AttrR, AttrRW
from fastcs.datatypes import Int
from fastcs_odin.controllers import (
    FrameProcessorAdapterController,
)
from fastcs_odin.controllers.odin_subcontroller import OdinSubController
from fastcs_odin.io import ConfigFanAttributeIORef
from fastcs_odin.util import get_all_sub_controllers


class XspressFPAdapterController(FrameProcessorAdapterController):
    state = AttrR[str]
    chunk_total = AttrRW[int]

    async def initialise(self):
        await super().initialise()

        attr_list = []

        subcontrollers = get_all_sub_controllers(self)

        for sub_controller in subcontrollers:
            match sub_controller:
                case OdinSubController():
                    for parameter in sub_controller.parameters:
                        if ("chunks" in parameter.uri and "0" in parameter.uri) or (
                            "xspress" in parameter.uri and "chunks" in parameter.uri
                        ):
                            attr_list.append(sub_controller.attributes[parameter.name])

                case _:
                    logging.warning(
                        f"Subcontroller {sub_controller} not an OdinAdapterController"
                    )
        chunk_total = AttrRW(Int(), ConfigFanAttributeIORef(attr_list))
        self.add_attribute("TotalChunk", chunk_total)
