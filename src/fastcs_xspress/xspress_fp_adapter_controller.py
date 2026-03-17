import logging

from fastcs.attributes import AttrRW
from fastcs_odin.controllers import (
    FrameProcessorAdapterController,
)
from fastcs_odin.controllers.odin_subcontroller import OdinSubController
from fastcs_odin.util import get_all_sub_controllers


class XspressFPAdapterController(FrameProcessorAdapterController):
    chunks: AttrRW[int]
    acq_id: AttrRW[str]

    async def initialise(self):
        await super().initialise()

        # Construct a list with all the MCA dataset chunks
        mca_list = []
        for sub_controller in get_all_sub_controllers(self):
            match sub_controller:
                case OdinSubController():
                    for parameter in sub_controller.parameters:
                        if "chunks" in parameter.uri and "0" in parameter.uri:
                            # mca_list.append(sub_controller.attributes[parameter.name])
                            mca_list.append(
                                (sub_controller.path[1], parameter.name.split("_")[1])
                            )
                case _:
                    logging.warning(
                        f"Subcontroller {sub_controller} not an OdinAdapterController"
                    )

        async def set_chunk_fp(value: int):
            for sub_controller, mca_num in mca_list:
                await self.connection.put(
                    f"api/0.1/fp/{sub_controller}/config/hdf/dataset/mca_{mca_num}/chunks",
                    [value, 1, 4096],  # pyright: ignore[reportArgumentType]
                )

        self.chunks.add_on_update_callback(callback=set_chunk_fp)
