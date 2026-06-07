# Railway Cloud App Specification

This document details the software architecture, database models, WebSocket schemas, and user interface modules for the **Railway Cloud App** (the coordinator backend + the mobile Progressive Web App frontend).

---

## 1. Component Overview

The Railway app acts as a secure cloud-based "Mailbox Coordinator". It does not run the AI agent itself; it merely coordinates data between the HoD's mobile phone and the local M4 Mac Mini.

```
                  ┌──────────────────────────────────────────┐
                  │              RAILWAY CLOUD               │
                  │                                          │
                  │   ┌──────────────────────────────────┐   │
                  │   │   Mobile Front-End (React PWA)   │   │
                  │   └────────────────▲─────────────────┘   │
                  │                    │ REST / WSS          │
                  │   ┌────────────────▼─────────────────┐   │
                  │   │   Mailbox Coordinator (NodeJS)   │   │
                  │   │        + SQLite / Postgres       │   │
                  │   └────────────────▲─────────────────┘   │
                  └────────────────────┼─────────────────────┘
                                       │ WebSocket Client
                                       │ (Outbound-only)
                  ┌────────────────────▼─────────────────────┐
                  │            M4 MAC MINI (LOCAL)           │
                  │  Hermes Swarm: Main Brain, Coder, Tester │
                  └──────────────────────────────────────────┘
```

---

## 2. Mailbox Coordinator API (Backend)

The backend can be written in Node.js (Express / `ws` library) or Python (FastAPI). It coordinates connections and stores chat state.

### A. Database Schema
A lightweight relational database (SQLite or PostgreSQL) keeps track of sessions and states so that the mobile app doesn't lose context if the connection drops.

```sql
-- 1. Departments / Active Profiles
CREATE TABLE departments (
    id VARCHAR(50) PRIMARY KEY, -- e.g., "marketing", "sales"
    name VARCHAR(100) NOT NULL,
    status VARCHAR(20) DEFAULT 'offline', -- 'online' or 'offline'
    last_ping_at TIMESTAMP
);

-- 2. Chat Sessions
CREATE TABLE sessions (
    id VARCHAR(50) PRIMARY KEY,
    department_id VARCHAR(50) REFERENCES departments(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 3. Messages
CREATE TABLE messages (
    id SERIAL PRIMARY KEY,
    session_id VARCHAR(50) REFERENCES sessions(id),
    sender VARCHAR(10) CHECK (sender IN ('user', 'agent')), -- who sent it
    text TEXT NOT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 4. Task Checklists
CREATE TABLE tasks (
    id SERIAL PRIMARY KEY,
    session_id VARCHAR(50) REFERENCES sessions(id),
    title VARCHAR(255) NOT NULL,
    status VARCHAR(20) CHECK (status IN ('pending', 'running', 'completed')),
    success_criteria TEXT,
    order_index INT
);

-- 5. Approval Requests
CREATE TABLE approvals (
    id VARCHAR(50) PRIMARY KEY,
    session_id VARCHAR(50) REFERENCES sessions(id),
    description TEXT NOT NULL,
    status VARCHAR(20) DEFAULT 'pending' CHECK (status IN ('pending', 'approved', 'rejected'))
);

-- 6. Staging Preview URLs
CREATE TABLE previews (
    id SERIAL PRIMARY KEY,
    session_id VARCHAR(50) REFERENCES sessions(id),
    url TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### B. WebSocket Message Schemas
All real-time coordination is driven by JSON payloads sent over WebSockets.

#### 1. Connection Handshake
*   **Mac Mini Client Registers**:
    ```json
    { "type": "register", "department_id": "marketing", "role": "agent" }
    ```
*   **Mobile Phone Client Registers**:
    ```json
    { "type": "register", "department_id": "marketing", "role": "user" }
    ```

#### 2. Chat & Commands
*   **HoD sends a task command (Phone -> Railway -> Mac Mini)**:
    ```json
    { "type": "command", "text": "Deploy summer promo landing page" }
    ```

#### 3. Swarm Status Updates
*   **Mac Mini updates current task state (Mac Mini -> Railway -> Phone)**:
    ```json
    {
      "type": "state_update",
      "status": "testing", 
      "checklist": [
        { "title": "Analyze request", "status": "completed" },
        { "title": "Write landing page code", "status": "completed" },
        { "title": "Run Playwright tests", "status": "running" }
      ]
    }
    ```

#### 4. Human-in-the-Loop Approvals
*   **Mac Mini pauses and requests approval (Mac Mini -> Railway -> Phone)**:
    ```json
    {
      "type": "request_approval",
      "approval_id": "app_982f1",
      "description": "Ready to deploy Summer Promo code to staging."
    }
    ```
*   **HoD responds on mobile (Phone -> Railway -> Mac Mini)**:
    ```json
    {
      "type": "respond_approval",
      "approval_id": "app_982f1",
      "approved": true
    }
    ```

#### 5. Preview & Health Payloads
*   **Mac Mini sends Staging Web Preview Link (Mac Mini -> Railway -> Phone)**:
    ```json
    { "type": "staging_preview", "url": "https://marketing-staging.up.railway.app" }
    ```
*   **Mac Mini pings Health Heartbeat (Mac Mini -> Railway)**:
    ```json
    {
      "type": "heartbeat",
      "git": "online",
      "playwright": "online",
      "claude_code": "online"
    }
    ```

---

### C. REST API Endpoints

While real-time events use WebSockets, standard actions and status reporting use standard HTTP endpoints:

#### 1. Task Status Update (Called by Mac Mini)
*   **Endpoint**: `POST /api/dept/:dept_id/sessions/:session_id/tasks/:task_id/status`
*   **Bearer Auth**: Authorized using the dynamic `DEPARTMENT_TOKEN` or `RAILWAY_TOKEN`.
*   **Payload**:
    ```json
    { "status": "running" }  // or "completed"
    ```
*   **Server Action**: 
    1. Updates the `tasks` table row matching `task_id` and `session_id`.
    2. Broadcasts a WebSocket `state_update` message containing the revised checklist to the HoD's connected mobile client.

#### 2. Get Active Session & Checklist (Called by Mobile App)
*   **Endpoint**: `GET /api/dept/:dept_id/sessions/active`
*   **Server Action**: Returns the active session ID, messages history, and current task checklist status array.

#### 3. Save OAuth Token (Called by Mobile App)
*   **Endpoint**: `POST /api/dept/:dept_id/oauth/token`
*   **Payload**:
    ```json
    { "provider": "github", "access_token": "gho_..." }
    ```
*   **Server Action**: Temporarily caches the key and pushes it down the active WebSocket connection to the M4 Mac Mini client, triggering a local write to the profile `.env` configuration.

---

## 3. Custom Mobile UI (PWA Frontend)

The frontend is a single-page application optimized for mobile safari/chrome. It consists of 4 main panels:

```
┌────────────────────────────────────────┐
│ ☤ AI IT TEAM COMMAND CENTER  [Online]  │ ◄── Team Online/Offline status
├────────────────────────────────────────┤
│ [Checklist]                            │
│  ✓ 1. Analyze request                  │ ◄── Interactive Checklist
│  ⚙️ 2. Write landing page code          │     (Hides raw coding outputs)
│  ☐ 3. Run Playwright tests             │
├────────────────────────────────────────┤
│                                        │
│  [Agent] I have completed the          │
│  coding phase. Running checks.         │ ◄── Chat Message Stream
│                                        │
├────────────────────────────────────────┤
│ ┌────────────────────────────────────┐ │
│ │ Click to view Staging Web Preview  │ │ ◄── Rendered Preview button
│ └────────────────────────────────────┘ │
│ [ Enter task for Marketing Team... ] ✉️ │ ◄── Plain English input field
└────────────────────────────────────────┘
```

### Mobile Views:
1.  **Chat Panel**: A standard messaging screen. Shows streaming agent text responses and hides all intermediate command outputs, compiling traces, or code logs.
2.  ** Checklist Panel**: A drop-down header displaying the decomposed steps from `tasks` table. The status switches from empty box, to spin icon, to checkmark in real time.
3.  **Approval Modal**: A blocking overlay that appears when an approval is requested:
    *   *Text*: "Verification passed. Okay to deploy to staging?"
    *   *Buttons*: `[ Cancel ]` (Red) / `[ Approve ]` (Green).
4.  **Preview Banner**: A floating action button that appears when the `staging_preview` URL is received, letting the HoD open the temporary staging website in a new tab.
5.  **OAuth Link Panel**: A settings modal enabling the HoD to tap "Link GitHub Account" or "Link Railway Account". This initiates OAuth redirects and pushes the resulting access keys securely back to the local Mac Mini.
