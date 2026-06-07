# PWA frontend placeholder

The mobile control plane lives here. Scaffolding (Vite + React + TS + Tailwind
+ Nanostores + vite-plugin-pwa) is in progress; see `docs/USER_PROVIDED_ITEMS.md`
for the stack decision point and the scaffolding commands.

What will eventually live in this directory:
- `src/pages/Chat.tsx`         chat console
- `src/pages/Checklist.tsx`    task checklist
- `src/components/ApprovalModal.tsx`
- `src/components/PreviewBanner.tsx`
- `src/components/OAuthCallback.tsx`
- `src/stores/*.ts`            Nanostores for ws, session, tasks
- `src/types/ws.ts`            TypeScript mirror of backend/app/schemas.py
- `public/manifest.webmanifest`
- `public/sw.js`               service worker for PWA install + push
- `vite.config.ts`             with vite-plugin-pwa

Until the scaffolding is created, leave this directory empty (or with a
`.gitkeep` only).
