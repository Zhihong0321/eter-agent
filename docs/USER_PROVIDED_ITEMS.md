# Items only Eternalgy can supply

This is the one-page checklist of secrets, accounts, and decisions
that no agent can produce on its own.

The Railway-specific items from earlier versions are gone. We're
hosting the backend on a Coolify server. Items below are what
blocks shipping today.

================================================================
HARD BLOCKERS (need at least these to ship)
================================================================

## A. GitHub access

  [ ] 1. The repo https://github.com/Zhihong0321/eter-agent exists
        (confirmed via API, currently public, 16+ commits).
        Decide: keep public, or flip to private yourself.

  [ ] 2. `gh` authenticated on this laptop. Either:
        a) Run `gh auth login` in a fresh shell on this laptop.
        b) Paste me a PAT (classic, scopes: `repo`).
        c) Tell me an SSH key is on this box; I'll switch the remote.

## B. LLM API key (so the agents can think on the Mac)

  [ ] 3. OpenRouter API key from https://openrouter.ai/keys
        Format: `sk-or-v1-...`
        Drop in a follow-up message; goes into the per-department
        Hermes profile. Optional: Anthropic / OpenAI direct key.

================================================================
COOLIFY SETUP (before backend goes live)
================================================================

## C. Coolify server

  [ ] 4. Coolify instance is up. Either self-hosted (Docker on a VPS)
        or Coolify Cloud. You will point the GitHub repo at it.
  [ ] 5. In Coolify: create Resource > Application > Public.
        Source = `Zhihong0321/eter-agent`, Branch = `main`,
        Build Pack = `Dockerfile`, Base Directory = `backend`,
        Port = `8000`.
  [ ] 6. Set the env vars in Coolify:
        - `DATABASE_URL` = `sqlite+aiosqlite:///./data/eter-agent.db`
          (or postgresql+asyncpg://... if you attached a Postgres
           service in Coolify)
        - `WS_SHARED_SECRET` = a 48-char random string.
          Generate: `python -c "import secrets; print(secrets.token_urlsafe(48))"`
        - `CORS_ORIGINS` = the PWA origin (or `*` while testing)
        - `ENV` = `prod`
  [ ] 7. Deploy. Coolify gives you `https://eter-agent.example.com`.
        That becomes the URL the Mac daemon and phone PWA use.

================================================================
DESIGN DECISIONS (5 min, but matter)
================================================================

  [ ] 8. Database: SQLite (default, simpler) or attach a Coolify
        Postgres service?
  [ ] 9. Department list: confirm Marketing / Sales / Operations,
        or give me your real list. Each gets its own Hermes profile
        and its own WSS room.
  [ ] 10. LLM per department: same model for all, or different?
        My default: Anthropic Claude via OpenRouter.
  [ ] 11. PWA stack: React + Vite + Tailwind + Nanostores
        (the original spec). Or substitute?
  [ ] 12. PWA auth: how do you log into the phone app? Options:
        no auth (URL is the secret), per-department password,
        magic link via email, or GitHub OAuth.

================================================================
WHEN YOU'RE DONE WITH A
================================================================

Paste the answers / secrets in your next message. I will:
  1. Update this file, checking off the boxes you completed.
  2. Continue execution from where we paused.
