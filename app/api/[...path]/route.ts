import { NextRequest, NextResponse } from "next/server"

const BACKEND_URL =
  process.env.BACKEND_URL ??
  "https://jsshackathon.onrender.com"

async function proxy(
  req: NextRequest,
  { params }: { params: Promise<{ path: string[] }> }
) {
  const { path } = await params
  const target = `${BACKEND_URL}/${path.join("/")}`

  const headers: HeadersInit = {
    "Content-Type": "application/json",
    "ngrok-skip-browser-warning": "1",
  }

  const init: RequestInit = {
    method: req.method,
    headers,
  }

  if (req.method !== "GET" && req.method !== "HEAD") {
    init.body = await req.text()
  }

  try {
    const res = await fetch(target, init)
    const data = await res.text()

    return new NextResponse(data, {
      status: res.status,
      headers: {
        "Content-Type": res.headers.get("Content-Type") ?? "application/json",
      },
    })
  } catch (err) {
    return NextResponse.json(
      { detail: `Proxy error: ${err instanceof Error ? err.message : err}` },
      { status: 502 }
    )
  }
}

export const GET = proxy
export const POST = proxy
export const PUT = proxy
export const DELETE = proxy
export const PATCH = proxy
