# Mac daemon (mailbox_client)

This directory holds the Python process that runs on the M4 Mac Mini and
bridges a local Hermes Agent to the Railway backend.

## Files

- `mailbox_client.py`      outbound WebSocket client (no inbound ports)
- `smoke_test.py`          probes git / playwright / railway / gh / node / python
                           and writes `environment_awareness.yaml` to the
                           Hermes profile directory
- `SOUL.md.template.py`    string template for the per-department `SOUL.md`
                           that enforces the Logical Processing gate
- `launchd/*.plist`        drop-in LaunchAgent that boots the daemon at login

## Install on the Mac Mini (one-time, per department)

```bash
# 1. Copy this dir to the Mac
scp -r daemon/ macmini:~/

# 2. On the Mac, install the daemon code
python3 -m venv ~/.eter-agent
~/.eter-agent/bin/pip install -e daemon/
cp daemon/launchd/com.eteragent.mailbox.plist ~/Library/LaunchAgents/
# (edit the plist to set ETER_WS_SECRET, paths, and profile name)

# 3. Run the smoke test once
python3 daemon/smoke_test.py --profile-dir ~/.hermes/profiles/marketing

# 4. Bootstrap the LaunchAgent
launchctl bootstrap gui/$UID ~/Library/LaunchAgents/com.eteragent.mailbox.plist
launchctl enable gui/$UID/com.eteragent.mailbox
launchctl kickstart -k gui/$UID/com.eteragent.mailbox

# 5. Tail logs
tail -F /tmp/eter-agent-mailbox.out.log
```

## Security notes

- The daemon ONLY opens outbound TCP 443 to Railway. No inbound ports.
- `ETER_WS_SECRET` should be stored in the macOS Keychain and loaded by the
  LaunchAgent, not committed in plaintext.
- The Mac daemon holds a `RAILWAY_TOKEN` in its `.env` to deploy to staging
  via the local Railway CLI.
