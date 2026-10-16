import asyncio
import json
from pathlib import Path

import pytest
from fastcs.attributes import AttrRW
from fastcs.connections.ip_connection import IPConnectionSettings
from fastcs.datatypes import Int, String
from fastcs_odin.controllers.odin_data.frame_processor import (
    FrameProcessorAdapterController,
)
from fastcs_odin.controllers.odin_subcontroller import OdinSubController
from fastcs_odin.io.config_fan_sender_attribute_io import (
    ConfigFanAttributeIO,
    ConfigFanAttributeIORef,
)
from fastcs_odin.util import OdinParameter, OdinParameterMetadata
from pytest_mock import MockerFixture

from fastcs_xspress.xspress_adapter_controller import XspressAdapterController
from fastcs_xspress.xspress_controller import XspressController
from fastcs_xspress.xspress_fp_adapter_controller import XspressFPAdapterController
from fastcs_xspress.xspress_meta_writer_adapter import (
    XspressMetaWriterAdapterController,
)
from fastcs_xspress.xspress_odin_controller import XspressOdinController

_lock = asyncio.Lock()
HERE = Path(__file__).parent


@pytest.fixture
def xsp_odin_fp_controller(mocker: MockerFixture):
    controller = XspressFPAdapterController(mocker.AsyncMock(), [], "", [])

    controller.file_path = AttrRW(String(), initial_value="/tmp/data")  # pyright: ignore[reportAttributeAccessIssue]
    controller.file_prefix = AttrRW(String(), initial_value="test_prefix")  # pyright: ignore[reportAttributeAccessIssue]
    controller.acquisition_id = AttrRW(String(), initial_value="test_id")  # pyright: ignore[reportAttributeAccessIssue]
    controller.acq_id = AttrRW(String(), initial_value="test_id")
    controller.chunks = AttrRW(Int(), initial_value=0)

    return controller


@pytest.fixture
def xsp_odin_mw_controller(mocker: MockerFixture):
    XspressMetaWriterAdapterController(mocker.AsyncMock(), [], "", [])

    return XspressMetaWriterAdapterController(mocker.AsyncMock(), [], "", [])


@pytest.mark.asyncio
async def test_create_xspress_controller(mocker: MockerFixture):
    xsp_controller = XspressController(IPConnectionSettings("127.0.0.1", 80))

    connection = mocker.patch.object(xsp_controller, "connection")
    connection.get = mocker.AsyncMock()
    connection.get.side_effect = [
        {"value": 1},
    ]

    drv_connection = mocker.patch(
        "fastcs_xspress.xspress_adapter_controller.XspressAdapterController.initialise"
    )
    od_connection = mocker.patch(
        "fastcs_xspress.xspress_odin_controller.XspressOdinController.initialise"
    )
    mocker.patch("fastcs_odin.util.create_odin_parameters")

    await xsp_controller.initialise()

    drv_connection.assert_called_once()
    od_connection.assert_called_once()
    assert isinstance(xsp_controller.xspress, XspressAdapterController)  # pyright: ignore[reportAttributeAccessIssue]
    assert isinstance(xsp_controller.OD, XspressOdinController)


@pytest.mark.asyncio
async def test_xspress_adapter_controller_creates_sub_controllers(
    mocker: MockerFixture,
):
    xsp_controller = XspressController(IPConnectionSettings("127.0.0.1", 80))

    parameters = [{"dtc": "", "scalars": ""}]

    connection = mocker.patch.object(xsp_controller, "connection")
    connection.get = mocker.AsyncMock()
    connection.get.side_effect = parameters
    mocker.patch(
        "fastcs_xspress.xspress_odin_controller.XspressOdinController.initialise"
    )

    await xsp_controller.initialise()
    assert isinstance(
        xsp_controller.xspress.sub_controllers["dtc_controller"],  # pyright: ignore[reportAttributeAccessIssue]
        OdinSubController,
    )
    assert isinstance(
        xsp_controller.xspress.sub_controllers["scalar_controller"],  # pyright: ignore[reportAttributeAccessIssue]
        OdinSubController,
    )


@pytest.mark.asyncio
async def test_xspress_controller_creates_fp_adapter(
    xsp_odin_fp_controller, xsp_odin_mw_controller, mocker: MockerFixture
):
    xsp_controller = XspressOdinController(IPConnectionSettings("127.0.0.1", 80))
    connection = mocker.patch.object(xsp_controller, "connection")
    connection.get = mocker.AsyncMock()
    connection.get.side_effect = [
        {"adapters": ["xspress", "fp", "mw"]},
        {"module": {"value": "FrameProcessorAdapter"}},
        {"module": {"value": "MetaListenerAdapter"}},
    ]
    func = mocker.patch(
        "fastcs_xspress.xspress_odin_controller.XspressOdinController._create_adapter_controller"
    )
    func.side_effect = [xsp_odin_fp_controller, xsp_odin_mw_controller]
    mocker.patch(
        "fastcs_xspress.xspress_fp_adapter_controller.XspressFPAdapterController.initialise"
    )

    mocker.patch(
        "fastcs_odin.controllers.odin_data.meta_writer.MetaWriterAdapterController.initialise"
    )
    mocker.patch(
        "fastcs_odin.io.status_summary_attribute_io.initialise_summary_attributes"
    )

    await xsp_controller.initialise()
    assert isinstance(xsp_controller.FP, XspressFPAdapterController)
    assert isinstance(xsp_controller.MW, XspressMetaWriterAdapterController)


@pytest.mark.asyncio
async def test_initialise_raises(mocker: MockerFixture):
    xsp_controller = XspressOdinController(IPConnectionSettings("127.0.0.1", 80))
    xsp_controller.connection = mocker.AsyncMock()
    xsp_controller.connection.open = mocker.Mock()
    xsp_controller.connection.get.return_value = {"not_adapters": []}

    with pytest.raises(ValueError, match=r"Did not find valid adapters in response"):
        await xsp_controller.initialise()

    xsp_controller.connection.get.return_value = {"adapters": []}
    with pytest.raises(ValueError, match=r"'xspress' is not in list"):
        await xsp_controller.initialise()


@pytest.mark.asyncio
async def test_xspress_odin_adoater_creation(mocker: MockerFixture):
    xsp_controller = XspressOdinController(IPConnectionSettings("127.0.0.1", 80))
    xsp_controller.connection = mocker.AsyncMock()
    parameters = [
        OdinParameter(
            ["0"], metadata=OdinParameterMetadata(value=0, type="int", writeable=False)
        )
    ]
    ctrl = xsp_controller._create_adapter_controller(
        xsp_controller.connection, parameters, "fp", "FrameProcessorAdapter"
    )
    assert isinstance(ctrl, XspressFPAdapterController)

    ctrl = xsp_controller._create_adapter_controller(
        xsp_controller.connection, parameters, "mw", "MetaListenerAdapter"
    )
    assert isinstance(ctrl, XspressMetaWriterAdapterController)


@pytest.mark.asyncio
async def test_xspress_attribute_creation(mocker: MockerFixture):
    with (HERE / "input/xspress.json").open() as f:
        response = json.loads(f.read())

    xsp_controller = XspressController(IPConnectionSettings("127.0.0.1", 80))

    connection = mocker.patch.object(xsp_controller, "connection")
    connection.get = mocker.AsyncMock()
    connection.get.side_effect = [
        response,
        {"allowed": response["command"]["allowed"]},
    ]
    mocker.patch("fastcs_xspress.xspress_controller.XspressOdinController.initialise")

    await xsp_controller.initialise()

    assert (
        len(
            xsp_controller.sub_controllers["xspress"]
            .sub_controllers["dtc_controller"]
            .attributes
        )
        == 81
    )
    assert (
        len(
            xsp_controller.sub_controllers["xspress"]
            .sub_controllers["scalar_controller"]
            .attributes
        )
        == 120
    )
    assert len(xsp_controller.sub_controllers["xspress"].attributes) == 53
    assert len(xsp_controller.sub_controllers["xspress"].command_methods) == 4


@pytest.mark.asyncio
async def test_xspress_chunk_set(mocker: MockerFixture):
    xsp_fp = XspressFPAdapterController(mocker.AsyncMock(), [], "api/0.1", [])
    mocker.patch.object(
        FrameProcessorAdapterController,
        "initialise",
        new_callable=mocker.AsyncMock,
    )
    get_sub_controllers = mocker.patch(
        "fastcs_xspress.xspress_fp_adapter_controller.get_all_sub_controllers"
    )

    parameters = [
        OdinParameter(
            ["mca_0", "chunks", "0"],
            metadata=OdinParameterMetadata(value=0, type="int", writeable=False),
        ),
        OdinParameter(
            ["mca_1", "chunks", "0"],
            metadata=OdinParameterMetadata(value=0, type="int", writeable=False),
        ),
        OdinParameter(
            ["mca_2", "chunks", "0"],
            metadata=OdinParameterMetadata(value=0, type="int", writeable=False),
        ),
        OdinParameter(
            ["mca_3", "chunks", "0"],
            metadata=OdinParameterMetadata(value=0, type="int", writeable=False),
        ),
    ]
    subcontroller = OdinSubController(mocker.Mock(), parameters, "", [])
    subcontroller.set_path(["FP", "0", "config", "HDF", "dataset"])
    get_sub_controllers.return_value = [subcontroller]

    connection = mocker.patch.object(xsp_fp, "connection")
    connection.get = mocker.AsyncMock()
    xsp_fp.chunks = AttrRW(Int(), initial_value=0)
    mocker.patch(
        "fastcs_xspress.xspress_fp_adapter_controller.XspressFPAdapterController.attributes",
        {
            "file_path": AttrRW(
                String(),
                io_ref=ConfigFanAttributeIORef(
                    [
                        AttrRW(String(), None, initial_value=""),
                    ]
                ),
                initial_value="",
            ),
            "mca_dataset": AttrRW(
                String(),
                io_ref=ConfigFanAttributeIORef(
                    [
                        AttrRW(String(), None, initial_value=""),
                    ]
                ),
                initial_value="",
            ),
        },
    )

    await xsp_fp.initialise()

    await xsp_fp.chunks.update(1)

    connection.put.assert_any_await(
        "api/0.1/fp/0/config/hdf/dataset/mca_0/chunks", [1, 1, 4096]
    )
    connection.put.assert_any_await(
        "api/0.1/fp/0/config/hdf/dataset/mca_1/chunks", [1, 1, 4096]
    )
    connection.put.assert_any_await(
        "api/0.1/fp/0/config/hdf/dataset/mca_2/chunks", [1, 1, 4096]
    )
    connection.put.assert_any_await(
        "api/0.1/fp/0/config/hdf/dataset/mca_3/chunks", [1, 1, 4096]
    )
    assert connection.put.await_count == len(parameters)


@pytest.mark.asyncio
async def test_xspress_list_dataset(mocker: MockerFixture):
    xsp_fp = XspressFPAdapterController(mocker.AsyncMock(), [], "api/0.1", [])
    mocker.patch.object(
        FrameProcessorAdapterController,
        "initialise",
        new_callable=mocker.AsyncMock,
    )
    get_sub_controllers = mocker.patch(
        "fastcs_xspress.xspress_fp_adapter_controller.get_all_sub_controllers"
    )

    parameters = [
        OdinParameter(
            ["ch0_time_frame", "chunks", "0"],
            metadata=OdinParameterMetadata(value=0, type="int", writeable=True),
        ),
        OdinParameter(
            ["ch1_time_frame", "chunks", "0"],
            metadata=OdinParameterMetadata(value=0, type="int", writeable=True),
        ),
        OdinParameter(
            ["ch0_event_height", "chunks", "0"],
            metadata=OdinParameterMetadata(value=0, type="int", writeable=True),
        ),
        OdinParameter(
            ["ch1_event_height", "chunks", "0"],
            metadata=OdinParameterMetadata(value=0, type="int", writeable=True),
        ),
    ]

    xsp_fp.parameters = parameters

    get_sub_controllers.return_value = []

    connection = mocker.patch.object(xsp_fp, "connection")
    connection.get = mocker.AsyncMock()

    xsp_fp.attributes["file_path"] = AttrRW(
        String(),
        io_ref=ConfigFanAttributeIORef(
            [
                AttrRW(String(), None, initial_value=""),
            ]
        ),
        initial_value="",
    )

    mock_attrs = {}

    for parameter in xsp_fp.parameters:
        m = mocker.MagicMock()
        m.put = mocker.AsyncMock()
        mock_attrs[parameter.name] = m
        xsp_fp.add_attribute(
            parameter.name,
            m,
        )

    await xsp_fp.initialise()

    io = ConfigFanAttributeIO()

    await io.send(xsp_fp.list_data_chunks_0, 1)

    mock_attrs["ch0_event_height_chunks_0"].put.assert_called_once_with(
        1, sync_setpoint=True
    )
    mock_attrs["ch1_event_height_chunks_0"].put.assert_called_once_with(
        1, sync_setpoint=True
    )
    mock_attrs["ch0_time_frame_chunks_0"].put.assert_called_once_with(
        1, sync_setpoint=True
    )
    mock_attrs["ch1_time_frame_chunks_0"].put.assert_called_once_with(
        1, sync_setpoint=True
    )


@pytest.mark.asyncio
async def test_xspress_fp_adapter_controller_logging(mocker: MockerFixture):
    xsp_fp = XspressFPAdapterController(mocker.AsyncMock(), [], "api/0.1", [])
    mocker.patch.object(
        FrameProcessorAdapterController,
        "initialise",
        new_callable=mocker.AsyncMock,
    )
    get_sub_controllers = mocker.patch(
        "fastcs_xspress.xspress_fp_adapter_controller.get_all_sub_controllers"
    )

    logging = mocker.patch("logging.warning")

    get_sub_controllers.return_value = ["NotAnOdinSubController"]

    connection = mocker.patch.object(xsp_fp, "connection")
    connection.get = mocker.AsyncMock()
    xsp_fp.chunks = AttrRW(Int(), initial_value=0)
    mocker.patch(
        "fastcs_xspress.xspress_fp_adapter_controller.XspressFPAdapterController.attributes",
        {
            "file_path": AttrRW(
                String(),
                io_ref=ConfigFanAttributeIORef(
                    [
                        AttrRW(String(), None, initial_value=""),
                    ]
                ),
                initial_value="",
            )
        },
    )

    await xsp_fp.initialise()

    logging.assert_called_with(
        "Subcontroller NotAnOdinSubController not an OdinAdapterController"
    )


@pytest.mark.asyncio
async def test_xspress_fp_create_dataset_table(mocker: MockerFixture):
    xsp_fp = XspressFPAdapterController(mocker.AsyncMock(), [], "api/0.1", [])
    mocker.patch.object(
        FrameProcessorAdapterController,
        "initialise",
        new_callable=mocker.AsyncMock,
    )

    parameters = [
        OdinParameter(
            ["dataset", "mca_0", "datatype"],
            metadata=OdinParameterMetadata(value=0, type="str", writeable=False),
        ),
        OdinParameter(
            ["dataset", "mca_1", "datatype"],
            metadata=OdinParameterMetadata(value=0, type="str", writeable=False),
        ),
        OdinParameter(
            ["dataset", "mca_2", "datatype"],
            metadata=OdinParameterMetadata(value=0, type="str", writeable=False),
        ),
        OdinParameter(
            ["dataset", "mca_3", "datatype"],
            metadata=OdinParameterMetadata(value=0, type="str", writeable=False),
        ),
    ]
    xsp_fp.parameters = parameters

    connection = mocker.patch.object(xsp_fp, "connection")
    connection.get = mocker.AsyncMock()
    xsp_fp.chunks = AttrRW(Int(), initial_value=0)
    mocker.patch(
        "fastcs_xspress.xspress_fp_adapter_controller.XspressFPAdapterController.attributes",
        {
            "file_path": AttrRW(
                String(),
                io_ref=ConfigFanAttributeIORef(
                    [
                        AttrRW(String(), None, initial_value=""),
                    ]
                ),
                initial_value="",
            ),
            "mca_dataset": AttrRW(
                String(),
                io_ref=ConfigFanAttributeIORef(
                    [
                        AttrRW(String(), None, initial_value=""),
                    ]
                ),
                initial_value="",
            ),
        },
    )
    await xsp_fp.initialise()
    assert len(xsp_fp.dataset_table.get()) == 4
    assert (xsp_fp.dataset_table.get() == ["mca_0", "mca_1", "mca_2", "mca_3"]).all()


@pytest.mark.asyncio
async def test_xspress_mw_initialise(mocker: MockerFixture):
    xsp_mw = XspressMetaWriterAdapterController(mocker.AsyncMock(), [], "api/0.1", [])

    parameters = [
        OdinParameter(
            ["0", "status", "timestamp"],
            metadata=OdinParameterMetadata(value=0, type="str", writeable=False),
        ),
        OdinParameter(
            ["config", "acquisitions", "data_endpoints"],
            metadata=OdinParameterMetadata(value=0, type="str", writeable=False),
        ),
    ]
    xsp_mw.parameters = parameters

    await xsp_mw.initialise()
    assert len(xsp_mw.attributes) == 6
