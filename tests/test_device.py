import pytest
from unittest.mock import patch

from CheckCiscoDeviceConfig.core.device.config import DeviceDataRetriever

# Fake Netmiko connection
class FakeConnection:
    def __enter__(self): return self
    def __exit__(self, exc_type, exc_val, exc_tb): return False
    def send_command(self, cmd):
        if cmd == "show version":
            return "Cisco IOS XE Software, Version 17.3.1"
        elif cmd == "show running-config":
            return "hostname Router1\nusername admin password 7 secret"
        else:
            return f"output for {cmd}"

# Wrapper that catches exceptions
def run_func(retriever: DeviceDataRetriever):
    try:
        return retriever._run_session()
    except Exception as e:
        retriever.result["error"] = str(e)
        return retriever.result

@pytest.fixture
def retriever():
    return DeviceDataRetriever(
        hostname="router1",
        host="10.0.0.1",
        os="iosxe",
        user="admin",
        password="pass",
        cmdlist=["show version", "show running-config"],
        sanitizeconfig=True,
        removepassword=15,
    )

def test_run_session_success(retriever):
    with patch("core.device.ConnectHandler", return_value=FakeConnection()):
        result = run_func(retriever)
        print(result)
        assert result["success"] is True
        assert "Cisco IOS XE Software" in result["output"]
        assert "password 7 <removed>" in result["output"]

def test_run_session_failure(retriever):
    # Simulate unsupported OS
    retriever.os = "unsupported_os"
    result = run_func(retriever)
    assert result["success"] is False
    assert "Unsupported OS type" in result["error"]

def test_run_session_exception(retriever):
    # Simulate Netmiko raising an exception
    class BrokenConnection(FakeConnection):
        def send_command(self, cmd):
            raise RuntimeError("Connection failed")

    with patch("core.device.ConnectHandler", return_value=BrokenConnection()):
        result = run_func(retriever)
        assert result["success"] is False
        assert "Connection failed" in result["error"]
