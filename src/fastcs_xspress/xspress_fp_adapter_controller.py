import logging

from fastcs.attributes import AttrR, AttrRW
from fastcs.datatypes import Int, String
from fastcs_odin.controllers import (
    FrameProcessorAdapterController,
)
from fastcs_odin.controllers.odin_subcontroller import OdinSubController
from fastcs_odin.io import StatusSummaryAttributeIORef
from fastcs_odin.io.config_fan_sender_attribute_io import ConfigFanAttributeIORef
from fastcs_odin.util import get_all_sub_controllers


class XspressFPAdapterController(FrameProcessorAdapterController):
    chunks: AttrRW[int]
    acq_id: AttrRW[str]
    count: AttrR[int]

    async def initialise(self):
        await super().initialise()

        # Construct a list with all the MCA dataset chunks
        mca_list = []
        for sub_controller in get_all_sub_controllers(self):
            match sub_controller:
                case OdinSubController():
                    for parameter in sub_controller.parameters:
                        if "chunks" in parameter.uri and "0" in parameter.uri:
                            # Parameter name will be in the form of mca_X_chunks_0
                            # sub_controller path will be in the form of
                            # [..., "FP", "X",...]
                            mca_list.append(
                                (
                                    sub_controller.path[
                                        sub_controller.path.index("FP") + 1
                                    ],
                                    parameter.name.split("_")[1],
                                )
                            )
                case _:
                    logging.warning(
                        f"Subcontroller {sub_controller} not an OdinAdapterController"
                    )

        self.data_dims_0 = AttrRW(
            Int(),
            io_ref=ConfigFanAttributeIORef(
                [attr for name, attr in self.attributes.items() if "dims_0" in name]  # pyright: ignore[reportArgumentType]
            ),
            group="Data",
        )
        self.data_dims_1 = AttrRW(
            Int(),
            io_ref=ConfigFanAttributeIORef(
                [attr for name, attr in self.attributes.items() if "dims_1" in name]  # pyright: ignore[reportArgumentType]
            ),
            group="Data",
        )
        self.data_chunks_0 = AttrRW(
            Int(),
            io_ref=ConfigFanAttributeIORef(
                [attr for name, attr in self.attributes.items() if "chunks_0" in name]  # pyright: ignore[reportArgumentType]
            ),
            group="Data",
        )
        self.data_chunks_1 = AttrRW(
            Int(),
            io_ref=ConfigFanAttributeIORef(
                [attr for name, attr in self.attributes.items() if "chunks_1" in name]  # pyright: ignore[reportArgumentType]
            ),
            group="Data",
        )
        self.data_chunks_2 = AttrRW(
            Int(),
            io_ref=ConfigFanAttributeIORef(
                [attr for name, attr in self.attributes.items() if "chunks_2" in name]  # pyright: ignore[reportArgumentType]
            ),
            group="Data",
        )
        self.data_datatype = AttrRW(
            String(),
            io_ref=ConfigFanAttributeIORef(
                [attr for name, attr in self.attributes.items() if "datatype" in name]  # pyright: ignore[reportArgumentType]
            ),
            group="Data",
        )
        self.data_compression = AttrRW(
            String(),
            io_ref=ConfigFanAttributeIORef(
                [
                    attr
                    for name, attr in self.attributes.items()
                    if "compression" in name
                ]  # pyright: ignore[reportArgumentType]
            ),
            group="Data",
        )
        self.total_frames_written = AttrR(
            Int(),
            io_ref=StatusSummaryAttributeIORef(
                [""],
                "FramesWritten",
                lambda val: int(self.frames_written.get() / self.count.get())
                if self.count.get() > 0
                else 0,
                [self.frames_written],
            ),
        )

        self.raw_file_path = AttrRW(
            String(),
            io_ref=ConfigFanAttributeIORef(
                [
                    attr
                    for attr in self.attributes["file_path"].io_ref.attributes  # pyright: ignore[reportAttributeAccessIssue]
                    if "RAW" in attr.full_name
                ]  # pyright: ignore[reportArgumentType]
            ),
        )

        self.attributes["file_path"].io_ref.attributes = [  # pyright: ignore[reportAttributeAccessIssue]
            attr
            for attr in self.attributes["file_path"].io_ref.attributes  # pyright: ignore[reportAttributeAccessIssue]
            if "RAW" not in attr.full_name
        ]

        async def set_chunk_fp(value: int):
            for sub_controller, mca_num in mca_list:
                await self.connection.put(
                    f"api/0.1/fp/{sub_controller}/config/hdf/dataset/mca_{mca_num}/chunks",
                    [value, 1, 4096],  # pyright: ignore[reportArgumentType]
                )

        self.chunks.add_on_update_callback(callback=set_chunk_fp)
