"""Tests for the miwifi component."""

from __future__ import annotations

from typing import Final
import logging
import json
from unittest.mock import AsyncMock
from pytest_homeassistant_custom_component.common import load_fixture

from homeassistant import setup
from homeassistant.const import (
    CONF_IP_ADDRESS,
    CONF_PASSWORD,
    CONF_SCAN_INTERVAL,
    CONF_TIMEOUT,
)
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.dispatcher import async_dispatcher_connect

from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.miwifi.const import (
    DOMAIN,
    UPDATER,
    SIGNAL_NEW_DEVICE,
    DEFAULT_SCAN_INTERVAL,
    DEFAULT_TIMEOUT,
    DEFAULT_ACTIVITY_DAYS,
    CONF_IS_FORCE_LOAD,
    CONF_ACTIVITY_DAYS,
    OPTION_IS_FROM_FLOW,
)
from custom_components.miwifi.helper import get_config_value, get_store
from custom_components.miwifi.updater import LuciUpdater

MOCK_IP_ADDRESS: Final = "192.168.31.1"
MOCK_PASSWORD: Final = "**REDACTED**"
OPTIONS_FLOW_DATA: Final = {
    CONF_IP_ADDRESS: MOCK_IP_ADDRESS,
    CONF_PASSWORD: MOCK_PASSWORD,
    CONF_TIMEOUT: DEFAULT_TIMEOUT,
    CONF_SCAN_INTERVAL: DEFAULT_SCAN_INTERVAL,
}

_LOGGER = logging.getLogger(__name__)


async def async_setup(
    hass: HomeAssistant,
    ip: str = MOCK_IP_ADDRESS,
    without_store: bool = False,
    activity_days: int = 0,
    is_force: bool = False,
) -> list:
    """Setup.

    :param hass: HomeAssistant
    :param ip: str
    :param without_store: bool
    :param activity_days: int
    :param is_force: bool
    """

    config_entry = MockConfigEntry(
        domain=DOMAIN,
        data=OPTIONS_FLOW_DATA | {CONF_IP_ADDRESS: ip, CONF_IS_FORCE_LOAD: is_force},
        options={OPTION_IS_FROM_FLOW: True},
    )
    config_entry.add_to_hass(hass)

    await setup.async_setup_component(hass, "http", {})

    updater: LuciUpdater = LuciUpdater(
        hass,
        ip,
        get_config_value(config_entry, CONF_PASSWORD),
        get_config_value(config_entry, CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL),
        get_config_value(config_entry, CONF_TIMEOUT, DEFAULT_TIMEOUT),
        get_config_value(config_entry, CONF_IS_FORCE_LOAD, is_force),
        activity_days,
        get_store(hass, ip) if not without_store else None,
        entry_id=config_entry.entry_id,
    )

    @callback
    def add_device(device: dict) -> None:
        """Add device.

        :param device: dict: Device object
        """

        return

    updater.new_device_callback = async_dispatcher_connect(
        hass, SIGNAL_NEW_DEVICE, add_device
    )

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][config_entry.entry_id] = {
        CONF_IP_ADDRESS: ip,
        UPDATER: updater,
    }

    return [updater, config_entry]


async def async_mock_luci_client(mock_luci_client) -> None:
    """Mock"""

    mock_luci_client.return_value.logout = AsyncMock(return_value=None)
    mock_luci_client.return_value.login = AsyncMock(
        return_value=json.loads(load_fixture("login_data.json"))
    )
    mock_luci_client.return_value.init_info = AsyncMock(
        return_value=json.loads(load_fixture("init_info_data.json"))
    )
    mock_luci_client.return_value.image = AsyncMock(
        return_value=load_fixture("image_data.txt")
    )
    mock_luci_client.return_value.status = AsyncMock(
        return_value=json.loads(load_fixture("status_data.json"))
    )
    mock_luci_client.return_value.rom_update = AsyncMock(
        return_value=json.loads(load_fixture("rom_update_data.json"))
    )
    mock_luci_client.return_value.mode = AsyncMock(
        return_value=json.loads(load_fixture("mode_data.json"))
    )
    mock_luci_client.return_value.wan_info = AsyncMock(
        return_value=json.loads(load_fixture("wan_info_data.json"))
    )
    mock_luci_client.return_value.led = AsyncMock(
        return_value=json.loads(load_fixture("led_data.json"))
    )
    mock_luci_client.return_value.wifi_connect_devices = AsyncMock(
        return_value=json.loads(load_fixture("wifi_connect_devices_data.json"))
    )
    mock_luci_client.return_value.wifi_detail_all = AsyncMock(
        return_value=json.loads(load_fixture("wifi_detail_all_data.json"))
    )
    mock_luci_client.return_value.wifi_diag_detail_all = AsyncMock(
        return_value=json.loads(load_fixture("wifi_diag_detail_all_data.json"))
    )
    mock_luci_client.return_value.device_list = AsyncMock(
        return_value=json.loads(load_fixture("device_list_data.json"))
    )

    async def mock_avaliable_channels(index: int = 1) -> dict:
        """Mock channels"""

        if index == 2:
            return json.loads(load_fixture("avaliable_channels_5g_data.json"))

        if index == 3:
            return json.loads(load_fixture("avaliable_channels_5g_game_data.json"))

        return json.loads(load_fixture("avaliable_channels_2g_data.json"))

    mock_luci_client.return_value.avaliable_channels = AsyncMock(
        side_effect=mock_avaliable_channels
    )
    mock_luci_client.return_value.new_status = AsyncMock(
        return_value=json.loads(load_fixture("new_status_data.json"))
    )
    mock_luci_client.return_value.wifi_ap_signal = AsyncMock(
        return_value=json.loads(load_fixture("wifi_ap_signal_data.json"))
    )
    mock_luci_client.return_value.topo_graph = AsyncMock(
        return_value=json.loads(load_fixture("topo_graph_data.json"))
    )


class MultipleSideEffect:
    """Multiple side effect"""

    def __init__(self, *fns):
        """init"""

        self.fs = iter(fns)

    def __call__(self, *args, **kwargs):
        """call"""
        f = next(self.fs)
        return f(*args, **kwargs)
