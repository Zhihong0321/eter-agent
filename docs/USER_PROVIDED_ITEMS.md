# Items only Eternalgy can supply

This is the one-page checklist of secrets, accounts, and decisions that
no agent (including me) can produce on its own. Everything in
`docs/ARCHITECTURE.md` and `docs/RUNBOOK.md` is already done or scaffolded;
what's left is gated on the items below.

Estimated total elapsed time for you: ~30 minutes, mostly waiting on
GitHub / Railway / GitHub OAuth setup screens.

================================================================
HARD BLOCKERS (need at least these to start Phase 1 implementation)
================================================================

## A. GitHub access (so I can push code to https://github.com/Zhihong0321/eter-agent)

  [ ] 1. The repo already exists (confirmed via public API, currently
        empty, currently **public**). Decide:
          - Keep public? (fine for a portfolio piece)
          - Make private? (do this yourself, I do not have admin auth yet)
            gh repo edit Zhihong0321/eter-agent --visibility private
  [ ] 2. Authenticate `gh` on this Windows laptop so I can push. Pick ONE:
          a) Interactive: open a fresh shell and run
                gh auth login
             then: GitHub.com -> HTTPS -> Yes (authenticate git) ->
             "Login with a web browser" -> paste the one-time code at
             https://github.com/login/device
          b) Paste a PAT (classic, scopes: `repo`, `delete_repo`):
                echo "ghp_xxxxx" | gh auth login --with-token
          c) SSH key already in this laptop: tell me and I'll set the
             remote to git@github.com:Zhihong0321/eter-agent.git

  -> Tell me when you're done, or just run (b) and paste the token in your
     next message and I'll wrap it.

## B. LLM API key (so the agents can think)

  [ ] 3. OpenRouter API key (recommended default, my preferred routing)
        Get one at https://openrouter.ai/keys
        Format: sk-or-v1-...
        Drop it in a follow-up message; I'll put it in the per-department
        Hermes profiles (and tell you to do the same on the Mac Mini).

        Optional: also an Anthropic / OpenAI direct key if you want to
        pin a specific model. Otherwise OpenRouter will pick.

================================================================
PHASE 5 BLOCKERS (needed before backend deploy to Railway)
================================================================

## C. Railway account

  [ ] 4. Create a Railway account at https://railway.app
        (free tier = $5 credit, enough for this project).
  [ ] 5. Install the Railway CLI on this laptop and log in. I already
        have `railway 4.27.4` installed; I just need you to run
            railway login
        once. A browser window opens for OAuth. After that, I can
        `railway init` and `railway up` autonomously.
  [ ] 6. Tell me your Railway project name (e.g. "eter-agent") and
        whether you want a Postgres plugin attached from day one
        ($0.000016/GB-hour, basically free) or start on SQLite.

## D. GitHub OAuth App (for the PWA login)

  [ ] 7. Go to https://github.com/settings/developers -> New OAuth App
        Settings:
          Homepage URL:        https://command-center.up.railway.app
                              (or http://localhost:5173 for dev - we can
                               register two apps, one for each)
          Authorization callback URL:
                              https://command-center.up.railway.app/auth/github/callback
        Note the Client ID and generate a Client Secret.
        Paste both to me in your next message.

================================================================
PHASE 6 BLOCKERS (needed before PWA "approval needed" push works)
================================================================

## E. Branding (so I can generate icons + manifest)

  [ ] 8. PWA display name (default: "Eter Agent")
  [ ] 9. Primary brand color (hex, default: #2563eb if you don't care)
  [ ] 10. Short description for the manifest (default: "AI IT team
        control plane")
  [ ] 11. App icon. Either:
          - Send me a 512x512 PNG/JPG
          - Or tell me to generate a placeholder SVG (geometric monogram
            with your brand color) and you'll swap it later

================================================================
PHASE 7 BLOCKERS (needed before E2E playtest)
================================================================

## F. Real hardware access

  [ ] 12. The M4 Mac Mini is on, on the network, and you have admin
        access. Confirm it's running macOS 15+ and has outbound 443 to
        *.railway.app open (almost certainly yes; just confirm).
  [ ] 13. A real iPhone (iOS 16.4+) or Android phone you can install
        the PWA on. Browser devtools mobile emulation is not enough
        for testing web push.
  [ ] 14. A way for me to send files / commands to the Mac Mini.
        Easiest: iCloud / Dropbox / OneDrive shared folder.
        Otherwise: `scp daemon/ macmini:~/`.
        Tell me which.

================================================================
DESIGN DECISIONS (10 min, but matter)
================================================================

  [ ] 15. **Database for the backend**: Postgres on Railway (recommended)
        or SQLite (simpler, single-region)?
  [ ] 16. **PWA stack**: stick with the spec's React + Vite + Tailwind +
        Nanostores + vite-plugin-pwa, or substitute (SvelteKit, Solid,
        plain HTML)?
  [ ] 17. **Department list**: confirm Marketing / Sales / Operations,
        or give me your real list. Each gets its own Hermes profile +
        its own WSS room on the backend + its own PWA tab.
  [ ] 18. **LLM per department**: same model for all, or different? (My
        default: anthropic/claude-3.5-sonnet for everything.)
  [ ] 19. **Notification channel for "approval needed"**: web push (needs
        VAPID, included), or also Telegram / email? If Telegram, give me
        a bot token from @BotFather.
  [ ] 20. **Railway auth in the PWA**: since Railway does not support
        3rd-party OAuth, confirm the plan: the HoD pastes their
        personal Railway token into the PWA, the backend stores it
        (encrypted at rest), and forwards it to the Mac daemon's `.env`
        on first connect. Alternative: skip per-user Railway auth and
        use a single master token (simpler, less safe).
  [ ] 21. **PWA-to-server auth** (separate from GitHub OAuth): how do you
        log into the PWA itself? Options: no auth (URL is the secret -
        only safe on Railway private network), per-department password,
        magic link via email, or reuse the GitHub OAuth above.

================================================================
NICE-TO-HAVE (not blocking, ask me if you want them)
================================================================

  [ ] 22. CI/CD: should I add a GitHub Actions workflow that auto-deploys
        the backend to Railway on push to main?
  [ ] 23. PR previews: Railway's "PR Environment" feature spins up a
        staging URL per PR. Nice for safety, costs a bit of credit.
  [ ] 24. ngrok auth token: I installed ngrok but did not authtoken it.
        If you sign up at ngrok.com I can use a fixed subdomain, which
        makes the Mac daemon's WSS URL stable.
  [ ] 25. Local Postgres in Docker: useful for offline dev. I can
        install Docker Desktop and add a `docker-compose.yml` if you
        want.

================================================================
HOW TO TURN THIS CHECKLIST INTO PROGRESS
================================================================

For each numbered item, the protocol is:

  - If it's a "do this once on your laptop" item, do it and tell me.
  - If it's a "send me a secret" item, paste the secret in your next
    message. I will never echo secrets back to chat unredacted, and I
    will write them straight to .env files (which are gitignored).
  - If it's a "make a decision" item, just answer.

When you come back with answers, I will:
  1. Update this file, checking off the boxes you completed.
  2. Continue execution from where I paused (backend deploy / PWA
     scaffold / Mac install, in that order).
