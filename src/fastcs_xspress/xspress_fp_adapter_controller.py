import logging

from fastcs.attributes import AttrRW
from fastcs_odin.controllers import (
    FrameProcessorAdapterController,
)
from fastcs_odin.controllers.odin_subcontroller import OdinSubController
from fastcs_odin.util import get_all_sub_controllers


class XspressFPAdapterController(FrameProcessorAdapterController):
    chunks: AttrRW[int]

    async def initialise(self):
        await super().initialise()
        # self.chunks.enable_tracing()

        # Construct a list with all the MCA dataset chunks
        mca_list = []
        for sub_controller in get_all_sub_controllers(self):
            match sub_controller:
                case OdinSubController():
                    for parameter in sub_controller.parameters:
                        if "chunks" in parameter.uri and "0" in parameter.uri:
                            mca_list.append(sub_controller.attributes[parameter.name])

                case _:
                    logging.warning(
                        f"Subcontroller {sub_controller} not an OdinAdapterController"
                    )

        async def set_chunk_fp(value: int):
            for mca in mca_list:
                fp_num = mca.full_name.split(".")[1]
                num_num = mca.full_name.split(".")[-1].split("_")[1]
                await self.connection.put(
                    f"api/0.1/fp/{fp_num}/config/hdf/dataset/mca_{num_num}/chunks",
                    [value, 1, 4096],
                )

        self.chunks.add_on_update_callback(callback=set_chunk_fp)
