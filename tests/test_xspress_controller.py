import asyncio
import json
from pathlib import Path

import pytest
from fastcs.connections.ip_connection import IPConnectionSettings
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

_lock = asyncio.Lock()
HERE = Path(__file__).parent


@pytest.mark.asyncio
async def test_xspress_controller_creates_xspress_adapter(mocker: MockerFixture):
    xsp_controller = XspressController(IPConnectionSettings("127.0.0.1", 80))

    connection = mocker.patch.object(xsp_controller, "connection")
    connection.get = mocker.AsyncMock()
    connection.get.side_effect = [
        {"adapters": ["xspress"]},
        {"module": {"value": "XspressAdapter"}},
    ]

    await xsp_controller.initialise()

    assert list(xsp_controller.sub_controllers.keys()) == ["xspress"]
    assert isinstance(
        xsp_controller.sub_controllers["xspress"], XspressAdapterController
    )
    assert isinstance(
        xsp_controller.sub_controllers["xspress"].sub_controllers["dtc_controller"],
        OdinSubController,
    )
    assert isinstance(
        xsp_controller.sub_controllers["xspress"].sub_controllers["scalar_controller"],
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

    assert isinstance(ctrl, FrameProcessorAdapterController)


@pytest.mark.asyncio
async def test_xspress_attribute_creation(mocker: MockerFixture):
    with (HERE / "input/xspress.json").open() as f:
        response = json.loads(f.read())

    xsp_controller = XspressController(IPConnectionSettings("127.0.0.1", 80))

    connection = mocker.patch.object(xsp_controller, "connection")
    connection.get = mocker.AsyncMock()
    connection.get.side_effect = [
        {"adapters": ["xspress"]},
        response,
        {"allowed": response["command"]["allowed"]},
    ]

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
