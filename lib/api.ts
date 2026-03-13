import type {
  AddDeviceRequest,
  AlertOut,
  DeviceDetail,
  DeviceSummary,
  EventOut,
  ExplainResponse,
  NetworkMap,
  OverviewStats,
  SimulateAttackRequest,
  SimulateAttackResponse,
} from "./api-types"

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`/api${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...init?.headers,
    },
  })
  if (!res.ok) {
    const body = await res.text().catch(() => "")
    throw new Error(`API ${res.status}: ${body}`)
  }
  return res.json()
}

export const api = {
  health: () => request<{ status: string }>("/health"),

  overview: () => request<OverviewStats>("/overview"),

  devices: () => request<DeviceSummary[]>("/devices"),

  device: (id: string) => request<DeviceDetail>(`/devices/${id}`),

  explain: (id: string) => request<ExplainResponse>(`/devices/${id}/explain`),

  addDevice: (body: AddDeviceRequest) =>
    request<DeviceSummary>("/devices", {
      method: "POST",
      body: JSON.stringify(body),
    }),

  networkMap: () => request<NetworkMap>("/network-map"),

  alerts: () => request<AlertOut[]>("/alerts"),

  events: () => request<EventOut[]>("/events"),

  simulateAttack: (body: SimulateAttackRequest) =>
    request<SimulateAttackResponse>("/simulate-attack", {
      method: "POST",
      body: JSON.stringify(body),
    }),

  simulateBackdoor: (deviceId: string) =>
    request<SimulateAttackResponse>("/simulate/backdoor", {
      method: "POST",
      body: JSON.stringify({ device_id: deviceId, attack_type: "BACKDOOR" }),
    }),

  simulateTrafficSpike: (deviceId: string) =>
    request<SimulateAttackResponse>("/simulate/traffic-spike", {
      method: "POST",
      body: JSON.stringify({
        device_id: deviceId,
        attack_type: "TRAFFIC_SPIKE",
      }),
    }),

  simulateExfiltration: (deviceId: string) =>
    request<SimulateAttackResponse>("/simulate/data-exfiltration", {
      method: "POST",
      body: JSON.stringify({
        device_id: deviceId,
        attack_type: "DATA_EXFILTRATION",
      }),
    }),
}
