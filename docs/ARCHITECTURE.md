# ARCHITECTURE

## Components

1.  **M4 Mac Mini (per department)**
    - Hermes Agent runtime, one isolated profile per department
    - `mailbox_client.py` daemon: outbound WSS to Railway
    - `smoke_test.py`: produces `environment_awareness.yaml`
    - `SOUL.md`: enforces the Logical Processing gate
    - `devops` subagent: uses local Railway CLI to deploy staging

2.  **Railway (Mailbox Coordinator)**
    - FastAPI service
    - WebSocket router at `/ws`, multiplexed per `department_id`
    - 6 tables: `departments`, `sessions`, `messages`, `tasks`,
      `approvals`, `previews`
    - Heartbeat sweeper flips stale depts to `offline`

3.  **Mobile PWA (control plane)**
    - React + Vite + Tailwind + Nanostores
    - PWA installable on iOS 16.4+ and Android
    - Web push for "approval needed" alerts
    - OAuth: GitHub for HoD identity, Railway via pasted personal token

## Data flow (typical task)

```
   [HoD phone]                                          [Mac Mini]
       |                                                      |
       |  user_chat  ---->  Railway WS  ---->  mailbox_client |
       |                                                     \|/
       |                                            Hermes Swarm Manager
       |                                                     |
       |                          <-- state_update  (checklist push)
       |                          <-- request_approval  (plan)
       |                                                     |
   Approve/Reject   --->  Railway WS  --->  mailbox_client   |
       |                                                     \|/
       |                                            spawns Coder / Tester / DevOps
       |                                                     |
       |                          <-- staging_preview (URL)  |
       |                          <-- agent_chat (final reply)
       |                                                     |
```

## Why no inbound ports on the Mac?

The Mac sits behind a home router and may be on a flaky ISP. Opening
inbound WSS on a residential IP is fragile and exposed. Instead the
daemon dials out, the way corporate laptops do for MDM. This is the same
pattern as Tailscale, ngrok agents, and most EDR clients.

## The Logical Processing gate (the one safety rule)

`SOUL.md` instructs the Swarm Manager to NEVER run a coding/testing/devops
subagent without an approved plan from the HoD. The plan rides the same
WebSocket via the `approvals` table. This is the single most important
behavior in the system.
