from pydantic import BaseModel, Field
from typing import Optional, Literal
from datetime import datetime
from enum import Enum


class DeviceType(str, Enum):
    CAMERA = "camera"
    PRINTER = "printer"
    ROUTER = "router"
    LAPTOP = "laptop"
    SMART_TV = "smart_tv"
    THERMOSTAT = "thermostat"
    SMART_DOOR_LOCK = "smart_door_lock"
    SMART_LIGHT_HUB = "smart_light_hub"
    TEMPERATURE_SENSOR = "temperature_sensor"
    NETWORK_GATEWAY = "network_gateway"


class Protocol(str, Enum):
    RTSP = "RTSP"
    HTTPS = "HTTPS"
    HTTP = "HTTP"
    DNS = "DNS"
    NTP = "NTP"
    SSH = "SSH"
    TELNET = "Telnet"
    FTP = "FTP"
    IPP = "IPP"
    MDNS = "mDNS"
    DHCP = "DHCP"
    QUIC = "QUIC"
    UDP = "UDP"
    TCP = "TCP"
    WEBSOCKET = "WebSocket"
    GIT = "Git"
    MQTT = "MQTT"
    COAP = "CoAP"
    ZIGBEE = "Zigbee"
    BLUETOOTH = "BLE"


class DestinationType(str, Enum):
    INTERNAL = "internal"
    TRUSTED_CLOUD = "trusted_cloud"
    UNKNOWN_EXTERNAL = "unknown_external"


class TelemetryRecord(BaseModel):
    record_id: str
    device_id: str
    device_type: DeviceType
    src_ip: str
    dst_ip: str
    protocol: Protocol
    bytes_sent: int = Field(ge=0)
    bytes_received: int = Field(ge=0)
    session_duration: float = Field(ge=0, description="Duration in seconds")
    packet_count: int = Field(ge=0)
    destination_type: DestinationType
    timestamp: datetime
    window_id: Optional[int] = None


class DeviceState(BaseModel):
    device_id: str
    device_type: DeviceType
    ip_address: str
    is_compromised: bool = False
    active_attack: Optional[str] = None
    last_seen: Optional[datetime] = None
    total_records: int = 0


class TelemetrySummary(BaseModel):
    total_records: int
    total_devices: int
    records_by_device_type: dict[str, int]
    protocols_observed: list[str]
    time_range_start: Optional[datetime] = None
    time_range_end: Optional[datetime] = None
