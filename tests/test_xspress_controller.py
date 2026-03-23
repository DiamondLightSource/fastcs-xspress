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
from fastcs_odin.util import (
    OdinParameter,
    OdinParameterMetadata,
    create_odin_parameters,
)
from pytest_mock import MockerFixture

from fastcs_xspress.xspress_adapter_controller import XspressAdapterController
from fastcs_xspress.xspress_controller import XspressController
from fastcs_xspress.xspress_fp_adapter_controller import XspressFPAdapterController

_lock = asyncio.Lock()
HERE = Path(__file__).parent


@pytest.mark.asyncio
async def test_create_xspress_controller(mocker: MockerFixture):
    xsp_controller = XspressController(IPConnectionSettings("127.0.0.1", 80))

    xsp_controller.file_path = AttrRW(String(), initial_value="/tmp/data")  # pyright: ignore[reportAttributeAccessIssue]
    xsp_controller.file_prefix = AttrRW(String(), initial_value="test_prefix")  # pyright: ignore[reportAttributeAccessIssue]

    connection = mocker.patch.object(xsp_controller, "connection")
    connection.get = mocker.AsyncMock()

    xspress_initialise_mock = mocker.patch(
        "fastcs_xspress.xspress_controller.XspressController.initialise"
    )

    await xsp_controller.initialise()

    xspress_initialise_mock.assert_called_once_with()


@pytest.mark.asyncio
async def test_xspress_controller_creates_xspress_adapter(mocker: MockerFixture):
    xsp_controller = XspressController(IPConnectionSettings("127.0.0.1", 80))

    parameters = [
        OdinParameter(
            ["dtc"],
            metadata=OdinParameterMetadata(value=0, type="int", writeable=False),
        ),
        OdinParameter(
            ["scalar"],
            metadata=OdinParameterMetadata(value=0, type="int", writeable=False),
        ),
    ]
    ctrl = xsp_controller._create_adapter_controller(
        xsp_controller.connection, parameters, "xspress", "XspressAdapter"
    )

    assert isinstance(ctrl, XspressAdapterController)

    await ctrl.initialise()
    assert isinstance(
        ctrl.sub_controllers["dtc_controller"],
        OdinSubController,
    )
    assert isinstance(
        ctrl.sub_controllers["scalar_controller"],
        OdinSubController,
    )


@pytest.mark.asyncio
async def test_xspress_controller_creates_fp_adapter(mocker: MockerFixture):
    xsp_controller = XspressController(IPConnectionSettings("127.0.0.1", 80))
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


@pytest.mark.asyncio
async def test_xspress_attribute_creation(mocker: MockerFixture):
    with (HERE / "input/xspress.json").open() as f:
        response = json.loads(f.read())

    xsp_controller = XspressController(IPConnectionSettings("127.0.0.1", 80))

    connection = mocker.patch.object(xsp_controller, "connection")
    connection.get = mocker.AsyncMock()
    connection.get.side_effect = [
        {"allowed": response["command"]["allowed"]},
    ]
    ctrl = xsp_controller._create_adapter_controller(
        xsp_controller.connection,
        create_odin_parameters(response),
        "xspress",
        "XspressAdapter",
    )

    await ctrl.initialise()

    assert len(ctrl.sub_controllers["dtc_controller"].attributes) == 81
    assert len(ctrl.sub_controllers["scalar_controller"].attributes) == 120
    assert len(ctrl.attributes) == 53
    assert len(ctrl.command_methods) == 4


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
