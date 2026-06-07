"""Mac Mini daemon that bridges a local Hermes Agent to the Railway backend.

Responsibilities (per AI_IT_Team_Setup_Checklist Phase 3):
  1. On boot, connect outbound wss://command-center.up.railway.app/ws
     using the department's shared secret.
  2. Read its Hermes profile config to discover model, workspace, SOUL.md.
  3. Listen for `agent_command` frames, dispatch to a local Hermes AIAgent,
     and stream responses back as `agent_chat` frames.
  4. Periodically push `heartbeat` and `state_update` (checklist) frames.
  5. On `approval_result` from the phone, resume the paused Swarm Manager.
  6. Detect staging URLs produced by the local DevOps agent and push
     `staging_preview` frames.

This file is runnable on macOS launchctl (LaunchAgent plist in launchd/).
"""

from __future__ import annotations

import argparse
import asyncio
import json
import logging
import os
import signal
import sys
from pathlib import Path
from typing import Any

import websockets

log = logging.getLogger("mailbox_client")


# ---------- env ----------

class DaemonEnv:
    """All env-driven config in one place."""

    def __init__(self, profile: str) -> None:
        self.profile = profile
        self.department_id = os.environ.get("ETER_DEPARTMENT_ID", profile)
        self.ws_url = os.environ.get(
            "ETER_WS_URL",
            "wss://command-center.up.railway.app/ws",
        )
        self.ws_secret = os.environ.get("ETER_WS_SECRET", "")
        self.profile_dir = Path(
            os.environ.get("ETER_PROFILE_DIR", f"~/.hermes/profiles/{profile}")
        ).expanduser()
        self.workspace = Path(
            os.environ.get("ETER_WORKSPACE", f"~/projects/{profile}-workspace")
        ).expanduser()
        self.heartbeat_interval = int(os.environ.get("ETER_HEARTBEAT_INTERVAL", "15"))


# ---------- smoke test gate ----------

def check_environment(env: DaemonEnv) -> dict[str, str]:
    """Read environment_awareness.yaml produced by smoke_test.py.

    Returns the dict so the agent can compare incoming commands against
    what is actually present on this box (per the Logical Processing gate).
    """
    yaml_path = env.profile_dir / "environment_awareness.yaml"
    if not yaml_path.exists():
        log.warning("environment_awareness.yaml missing at %s", yaml_path)
        return {}
    try:
        import yaml  # type: ignore
    except ImportError:
        log.warning("PyYAML not installed; cannot read environment_awareness.yaml")
        return {}
    with yaml_path.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


# ---------- Hermes bridge (skeleton) ----------

class HermesBridge:
    """Thin wrapper that drives a local Hermes AIAgent for this profile.

    Real implementation: import the hermes-agent package, initialize an
    AIAgent with the profile's config, run a turn, stream deltas.
    Stubbed for now so this daemon can be exercised end-to-end.
    """

    def __init__(self, env: DaemonEnv) -> None:
        self.env = env
        self.env_awareness = check_environment(env)

    async def run_command(self, session_id: int, content: str) -> str:
        """Execute a single HoD command. Returns the final text reply.

        TODO: replace stub with:
            from hermes_agent import AIAgent
            agent = AIAgent.from_profile(self.env.profile)
            async for delta in agent.run(content):
                ...
        """
        log.info("hermes stub: dept=%s session=%s content=%r",
                 self.env.department_id, session_id, content[:80])
        return f"[hermes stub] received: {content!r}"


# ---------- WS client ----------

class MailboxClient:
    def __init__(self, env: DaemonEnv, bridge: HermesBridge) -> None:
        self.env = env
        self.bridge = bridge
        self._stop = asyncio.Event()
        self._ws: websockets.WebSocketClientProtocol | None = None

    def request_stop(self) -> None:
        self._stop.set()

    async def run(self) -> None:
        backoff = 1.0
        while not self._stop.is_set():
            try:
                await self._connect_and_serve()
                backoff = 1.0
            except Exception as e:  # noqa: BLE001
                log.exception("connection error: %s", e)
                await asyncio.sleep(min(backoff, 30))
                backoff *= 2

    async def _connect_and_serve(self) -> None:
        log.info("connecting to %s as dept=%s", self.env.ws_url, self.env.department_id)
        async with websockets.connect(self.env.ws_url, ping_interval=20) as ws:
            self._ws = ws
            await ws.send(json.dumps({
                "type": "hello",
                "department_id": self.env.department_id,
                "role": "agent",
                "auth_token": self.env.ws_secret,
            }))
            ack = json.loads(await ws.recv())
            if ack.get("type") != "hello_ack":
                raise RuntimeError(f"unexpected hello reply: {ack}")

            log.info("connected. entering main loop.")
            await asyncio.gather(
                self._send_heartbeats(ws),
                self._receive_forever(ws),
            )

    async def _send_heartbeats(self, ws) -> None:
        while not self._stop.is_set():
            try:
                await ws.send(json.dumps({
                    "type": "heartbeat",
                    "status": "online",
                    "extra": {
                        "profile": self.env.profile,
                        "workspace": str(self.env.workspace),
                    },
                }))
            except Exception:  # noqa: BLE001
                return
            await asyncio.sleep(self.env.heartbeat_interval)

    async def _receive_forever(self, ws) -> None:
        async for raw in ws:
            try:
                msg = json.loads(raw)
            except json.JSONDecodeError:
                log.warning("non-json frame: %r", raw)
                continue
            await self._dispatch(msg)

    async def _dispatch(self, msg: dict[str, Any]) -> None:
        mtype = msg.get("type")
        if mtype == "agent_command":
            session_id = int(msg.get("session_id", 0))
            content = msg.get("content", "")
            reply = await self.bridge.run_command(session_id, content)
            assert self._ws is not None
            await self._ws.send(json.dumps({
                "type": "agent_chat",
                "session_id": session_id,
                "content": reply,
                "role": "agent",
            }))
        elif mtype == "approval_result":
            log.info("approval_result: %s", msg)
            # TODO: resume the paused Swarm Manager
        else:
            log.debug("ignored message: %s", mtype)


# ---------- entrypoint ----------

def _install_signal_handlers(client: MailboxClient, loop: asyncio.AbstractEventLoop) -> None:
    for sig in (signal.SIGTERM, signal.SIGINT):
        loop.add_signal_handler(sig, client.request_stop)


async def _amain(profile: str) -> int:
    env = DaemonEnv(profile=profile)
    if not env.ws_secret:
        log.error("ETER_WS_SECRET is empty; refusing to start")
        return 2
    bridge = HermesBridge(env)
    client = MailboxClient(env, bridge)
    _install_signal_handlers(client, asyncio.get_running_loop())
    await client.run()
    return 0


def main() -> int:
    logging.basicConfig(
        level=os.environ.get("LOG_LEVEL", "INFO"),
        format="%(asctime)s %(levelname)s %(name)s :: %(message)s",
    )
    p = argparse.ArgumentParser(prog="mailbox_client")
    p.add_argument("--profile", required=True, help="Hermes profile name, e.g. marketing")
    args = p.parse_args()
    return asyncio.run(_amain(args.profile))


if __name__ == "__main__":
    sys.exit(main())
