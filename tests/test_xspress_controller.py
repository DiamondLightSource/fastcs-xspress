import asyncio
import json
from pathlib import Path

import pytest
from fastcs.attributes import AttrRW
from fastcs.connections.ip_connection import IPConnectionSettings
from fastcs.datatypes import Int
from fastcs_odin.controllers.odin_data.frame_processor import (
    FrameProcessorAdapterController,
)
from fastcs_odin.controllers.odin_subcontroller import OdinSubController
from fastcs_odin.util import (
    OdinParameter,
    OdinParameterMetadata,
)
from pytest_mock import MockerFixture

from fastcs_xspress.xspress_adapter_controller import XspressAdapterController
from fastcs_xspress.xspress_controller import XspressController
from fastcs_xspress.xspress_fp_adapter_controller import XspressFPAdapterController

_lock = asyncio.Lock()
HERE = Path(__file__).parent


@pytest.mark.asyncio
async def test_xspress_controller_creates_xspress_adapter(mocker: MockerFixture):
    xsp_controller = XspressController(IPConnectionSettings("127.0.0.1", 80))

    connection = mocker.patch.object(xsp_controller, "connection")
    connection.get = mocker.AsyncMock()
    connection.get.side_effect = [
        {"adapters": ["XSPRESS"]},
        {"module": {"value": "XspressAdapter"}},
        {"allowed": ["command_1", "command_2"]},
    ]

    await xsp_controller.initialise()

    assert list(xsp_controller.sub_controllers.keys()) == ["XSPRESS"]
    assert isinstance(
        xsp_controller.sub_controllers["XSPRESS"], XspressAdapterController
    )
    assert isinstance(
        xsp_controller.sub_controllers["XSPRESS"].sub_controllers["dtc_controller"],
        OdinSubController,
    )
    assert isinstance(
        xsp_controller.sub_controllers["XSPRESS"].sub_controllers["scalar_controller"],
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
        {"adapters": ["XSPRESS"]},
        response,
        {"allowed": response["command"]["allowed"]},
    ]

    await xsp_controller.initialise()

    assert (
        len(
            xsp_controller.sub_controllers["XSPRESS"]
            .sub_controllers["dtc_controller"]
            .attributes
        )
        == 81
    )
    assert (
        len(
            xsp_controller.sub_controllers["XSPRESS"]
            .sub_controllers["scalar_controller"]
            .attributes
        )
        == 120
    )
    assert len(xsp_controller.sub_controllers["XSPRESS"].attributes) == 53
    assert len(xsp_controller.sub_controllers["XSPRESS"].command_methods) == 4


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
