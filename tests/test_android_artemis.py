from unittest.mock import MagicMock, patch
import pytest
from ultron.integrations.artemis.device_manager import DeviceManager
from ultron.integrations.artemis.artemis_client import ArtemisClient
from ultron.integrations.artemis.android_tasks import AndroidTaskRunner, COMMON_APP_PACKAGES


def test_device_manager_init():
    dm = DeviceManager(adb_path="adb")
    assert dm.adb is not None


def test_artemis_client_status():
    client = ArtemisClient(artemis_dir="artemis")
    status = client.get_status()
    assert "artemis_installed" in status
    assert "connected_devices" in status
    assert status["artemis_installed"] is True


def test_android_task_no_device():
    dm = MagicMock()
    dm.get_primary_device.return_value = None
    runner = AndroidTaskRunner(device_manager=dm)

    res = runner.open_app("whatsapp")
    assert res["success"] is False
    assert "No Android device connected" in res["error"]


def test_common_app_packages():
    assert COMMON_APP_PACKAGES["whatsapp"] == "com.whatsapp"
    assert COMMON_APP_PACKAGES["chrome"] == "com.android.chrome"
    assert COMMON_APP_PACKAGES["ultron_node"] == "org.ultron.node"
