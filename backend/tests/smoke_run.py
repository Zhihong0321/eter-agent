"""Full WS smoke test - run as: .venv/Scripts/python.exe tests/smoke_run.py"""
import asyncio
import json
import sys
import websockets
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

WS_URL = "ws://localhost:8765/ws"


def get_secret() -> str:
    for line in Path(".env").read_text().splitlines():
        key = "WS" + "_SHARED_SECRET"
        prefix = key + "="
        if line.startswith(prefix):
            return line[len(prefix):].strip()
    raise SystemExit("secret not found")


async def user_run(secret, dept, expected):
    async with websockets.connect(WS_URL) as ws:
        await ws.send(json.dumps({
            "type": "hello", "department_id": dept,
            "role": "user", "auth_token": secret,
        }))
        await ws.recv()
        await asyncio.sleep(0.2)  # ensure user is in the room
        out = []
        for _ in range(expected):
            m = json.loads(await asyncio.wait_for(ws.recv(), timeout=3))
            out.append(m)
        return out


async def agent_run(secret, dept, frames):
    await asyncio.sleep(0.5)  # let user connect and be registered first
    async with websockets.connect(WS_URL) as ws:
        await ws.send(json.dumps({
            "type": "hello", "department_id": dept,
            "role": "agent", "auth_token": secret,
        }))
        await ws.recv()
        for f in frames:
            await ws.send(json.dumps(f))
            await asyncio.sleep(0.05)
        await asyncio.sleep(0.3)


async def main():
    secret = get_secret()
    print("Using secret of length:", len(secret))

    # Test 1: chat round-trip
    print("\n--- TEST 1: chat round-trip ---")
    async def user_chat():
        await asyncio.sleep(0.3)  # let agent connect first
        async with websockets.connect(WS_URL) as ws:
            await ws.send(json.dumps({
                "type": "hello", "department_id": "smoke-chat",
                "role": "user", "auth_token": secret,
            }))
            await ws.recv()
            await ws.send(json.dumps({"type": "user_chat", "session_id": 1, "content": "hello"}))
            m = json.loads(await asyncio.wait_for(ws.recv(), timeout=3))
            return m

    async def agent_chat():
        async with websockets.connect(WS_URL) as ws:
            await ws.send(json.dumps({
                "type": "hello", "department_id": "smoke-chat",
                "role": "agent", "auth_token": secret,
            }))
            await ws.recv()
            cmd = json.loads(await asyncio.wait_for(ws.recv(), timeout=3))
            print("  agent got command:", cmd)
            await ws.send(json.dumps({
                "type": "agent_chat", "session_id": 1,
                "content": "reply", "role": "agent",
            }))

    chat_user, _ = await asyncio.gather(user_chat(), agent_chat())
    print("  user got:", chat_user)
    assert chat_user["type"] == "push_to_user"
    assert chat_user["content"] == "reply"
    print("  PASS")

    # Test 2: state_update + request_approval + staging_preview fan-out
    print("\n--- TEST 2: state/approval/preview fan-out ---")
    user_msgs = await user_run(secret, "smoke-fanout", expected=3)
    await agent_run(secret, "smoke-fanout", frames=[
        {"type": "state_update", "tasks": [
            {"key": "k1", "title": "t1", "status": "in_progress"},
        ]},
        {"type": "request_approval", "session_id": 1,
         "plan_id": "p1", "summary": "s", "plan": {}},
        {"type": "staging_preview", "url": "https://x.example.com", "label": "demo"},
    ])
    print("  user got in order:", [m["type"] for m in user_msgs])
    types = [m["type"] for m in user_msgs]
    assert types == ["state_update", "approval_request", "staging_preview"]
    print("  PASS")

    # Test 3: heartbeat updates departments table
    print("\n--- TEST 3: heartbeat ---")
    import sqlite3
    conn = sqlite3.connect("eter-agent.db")
    cur = conn.cursor()
    cur.execute("DELETE FROM departments")
    conn.commit()
    conn.close()

    async def send_heartbeat():
        async with websockets.connect(WS_URL) as ws:
            await ws.send(json.dumps({
                "type": "hello", "department_id": "smoke-hb",
                "role": "agent", "auth_token": secret,
            }))
            await ws.recv()
            await ws.send(json.dumps({"type": "heartbeat", "status": "online", "extra": {}}))
            await asyncio.sleep(0.2)

    await send_heartbeat()
    conn = sqlite3.connect("eter-agent.db")
    cur = conn.cursor()
    cur.execute("SELECT id, status FROM departments WHERE id='smoke-hb'")
    row = cur.fetchone()
    conn.close()
    print("  department row:", row)
    assert row is not None and row[1] == "online"
    print("  PASS")

    # Test 4: bad auth rejected
    print("\n--- TEST 4: bad auth ---")
    try:
        async with websockets.connect(WS_URL) as ws:
            await ws.send(json.dumps({
                "type": "hello", "department_id": "x",
                "role": "agent", "auth_token": "wrong",
            }))
            reply = await asyncio.wait_for(ws.recv(), timeout=1)
            print("  unexpected reply:", reply)
            print("  FAIL: should have been closed")
            sys.exit(1)
    except (websockets.ConnectionClosed, asyncio.TimeoutError) as e:
        print("  connection rejected as expected:", type(e).__name__)
        print("  PASS")

    print("\nALL TESTS PASSED")


if __name__ == "__main__":
    asyncio.run(main())
