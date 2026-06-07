# AI IT Team - Setup & Implementation Checklist

This checklist outlines the step-by-step tasks required to configure a fresh installation of `hermes-agent` on your M4 Mac Mini into a multi-department AI IT Team connected to your custom Railway Mobile App.

---

## Reference Blueprints & Specifications

Before starting execution, review the following design files:
*   **System Architecture Blueprint**: [AI_IT_Team_Notes.md](file:///e:/hermes-ai/AI_IT_Team_Notes.md)
*   **Railway Cloud App Specifications**: [Railway_App_Specification.md](file:///e:/hermes-ai/Railway_App_Specification.md)

---

## Phase 1: Local PC (M4 Mac Mini) Preparation & Profile Creation
*Reference Blueprint Section: [2. Supporting Multiple Department HoDs](file:///e:/hermes-ai/AI_IT_Team_Notes.md#2-supporting-multiple-department-hods-local-pc-isolation)*

- [ ] **1. Install Hermes Agent Core**
  * Run the installer on the Mac Mini to set up Python, virtual environments, and required dependencies.
  * Command: `pip install hermes-agent` (or use the portable shell bootstrap).
- [ ] **2. Create Isolated Department Profiles**
  * Create unique CLI profiles for each department. Each profile contains its own configuration and memory.
  * Commands:
    * `hermes profile create marketing`
    * `hermes profile create sales`
    * `hermes profile create operations`
  * *Note: This creates isolated directories under `~/.hermes/profiles/<name>/`.*
- [ ] **3. Configure Default LLM Providers Per Profile**
  * Set the primary models for each department.
  * Commands:
    * `hermes -p marketing config set model.provider openrouter`
    * `hermes -p marketing config set model.default anthropic/claude-3.5-sonnet`
- [ ] **4. Lock Down Workspaces Per Profile**
  * Edit the `config.yaml` in each profile to set the default project directory.
  * Path: `~/.hermes/profiles/<dept_name>/config.yaml`
  * Configuration to verify/add:
    ```yaml
    terminal:
      cwd: "~/projects/marketing-workspace"  # Point to department files
    ```

---

## Phase 2: Environment Awareness & Quartermaster Setup
*Reference Blueprint Section: [3. The Environment Awareness System](file:///e:/hermes-ai/AI_IT_Team_Notes.md#3-the-environment-awareness-system-capabilities--boundaries) & [4. The Quartermaster AI](file:///e:/hermes-ai/AI_IT_Team_Notes.md#4-the-quartermaster-ai-the-logistics-agent)*

- [ ] **1. Create the Environment Awareness Template**
  * Save a template file at `~/.hermes/profiles/<dept_name>/environment_awareness.yaml` listing the tools that will be audited.
- [ ] **2. Configure Quartermaster System Resource Audits**
  * Write a Python check in `~/.hermes/scripts/smoke_test.py` to audit hardware:
    * Check if disk space is > 10GB.
    * Check if system memory availability is healthy.
- [ ] **3. Implement Quartermaster Smoke Test Script**
  * Expand `smoke_test.py` to test the CLIs and integrations:
    * Git: `git --version`
    * Playwright: `npx playwright --version`
    * Railway: `railway status`
    * GitHub Auth: `gh auth status`
  * The script writes the output (`PASS` / `FAIL`) to `environment_awareness.yaml`.
- [ ] **4. Implement Quartermaster Dependency Prep Script**
  * Create a workflow script `~/.hermes/scripts/prep_deps.py` that the Quartermaster can call before coding tasks:
    * Automatically runs `npm install` or `pip install -r requirements.txt` if new packages are requested by the Coder.
- [ ] **5. Integrate Smoke Tests with Boot Flow**
  * Configure the background client to execute `smoke_test.py` automatically whenever the Mac Mini boots up or receives a configuration update from the mobile app.

---

## Phase 3: The Outbound WebSocket Client
*Reference Blueprint Section: [9. Deployment & Networking](file:///e:/hermes-ai/AI_IT_Team_Notes.md#9-deployment--networking-outbound-only-connection-model)*

- [ ] **1. Create the Background Client Daemon (`mailbox_client.py`)**
  * Write a Python daemon script on the Mac Mini that runs on system startup.
- [ ] **2. Configure Client Connection Parameters**
  * The script reads its local profile settings and connects outbound to the Railway server:
    * `wss://command-center.up.railway.app/ws/marketing`
- [ ] **3. Bridge Client to Hermes API**
  * Configure `mailbox_client.py` to:
    * Listen on the WebSocket for incoming JSON commands from Railway.
    * Initialize the local `AIAgent` instance (importing from `run_agent.py` using the department's profile context).
    * Stream the agent's text responses and tool execution states back over the WebSocket.

---

## Phase 4: Swarm Manager, Guardrail & Subagent Configuration
*Reference Blueprint Section: [7. No-Code Safety & On-Device Automation](file:///e:/hermes-ai/AI_IT_Team_Notes.md#7-no-code-safety--on-device-automation)*

- [ ] **1. Enforce the "Logical Processing" System Prompt (SOUL.md)**
  * Create a custom personality file (`SOUL.md`) in `~/.hermes/profiles/<dept_name>/SOUL.md`.
  * *See Blueprint: [11. The Logical Processing Engine](file:///e:/hermes-ai/AI_IT_Team_Notes.md#11-the-logical-processing-engine-anti-overconfidence-gate)*
  * Add the mandatory instruction:
    > "You are the Swarm Manager. You must NEVER immediately execute coding commands. First, compare the request against `environment_awareness.yaml`. Draft a result-focused verification plan and checklist. Pause and send the plan for approval. Wait until the user confirms the plan via the mobile UI before spawning coding/testing subagents."
- [ ] **2. Configure the Guardrail Agent System Prompt**
  * Set up the Guardrail Agent prompt instructions under the Swarm Orchestration profile.
  * *See Blueprint: [5. The Guardrail Agent](file:///e:/hermes-ai/AI_IT_Team_Notes.md#5-the-guardrail-agent-safety--negative-constraints)*
  * Add the mandatory instruction:
    > "Review the proposed task checklist and project context. Output a list of safety constraints beginning with 'Do not...'. Focus on database safety, credentials protection, directory boundaries, and deployment rules."
- [ ] **3. Enable Subagent Spawning (Delegation)**
  * Verify that `delegation` is active in `config.yaml` for subagent coordination.
  * Configuration:
    ```yaml
    delegation:
      orchestrator_enabled: true
      max_spawn_depth: 2
      subagent_auto_approve: false  # Do not auto-execute without verification
    ```
- [x] **4. Install the Task Progress Reporter Skill**
  * Copy [SKILL.md](file:///e:/hermes-ai/skills/task_progress_reporter/SKILL.md) into the profile's local skills folder: `~/.hermes/profiles/<dept_name>/skills/task_progress_reporter/SKILL.md`.
  * Register the python helper tool `report_task_status(task_id, status)` in the local plugins/tools directory.
  * The tool performs an outbound HTTP POST to:
    `https://command-center.up.railway.app/api/dept/<dept_id>/sessions/<session_id>/tasks/<task_id>/status`
- [ ] **5. Configure DevOps Agent for Automated Railway Deployments**
  * *See Blueprint: [7.4. Automated Railway Deployments](file:///e:/hermes-ai/AI_IT_Team_Notes.md#7-no-code-safety--on-device-automation)*
  * Install `railway-cli` locally on the M4 Mac Mini (`npm install -g @railway/cli` or brew install).
  * Configure the profile `config.yaml` to allow running railway commands.
  * Test execution commands programmatically via the agent:
    * Run a trial `railway link` and `railway up --detach` in a dummy workspace.
  * Register Railway API access:
    * Verify that the local profile's `.env` contains the environment variable `RAILWAY_TOKEN`.
    * Verify that the agent can connect to Railway's GraphQL API (`https://backboard.railway.app/graphql`) by running a test query.

---

## Phase 5: Railway Cloud App - Mailbox Coordinator Backend
*Reference Specifications: [2. Mailbox Coordinator API (Backend)](file:///e:/hermes-ai/Railway_App_Specification.md#2-mailbox-coordinator-api-backend)*

- [x] **1. Set Up the Railway Database**
  * Create a Postgres or SQLite service on Railway.
  * Execute the SQL schema migrations to create the 6 tables: `departments`, `sessions`, `messages`, `tasks` (checklist), `approvals`, and `previews`.
  * Ensure the `tasks` table is updated to support storing and displaying negative constraints (`Do Not` flags).
- [ ] **2. Write the WebSocket Server (`/ws`)**
  * Implement the server-side WebSocket router.
  * Write the registration logic to distinguish connections using `department_id` and `role` ('agent' vs 'user').
- [ ] **3. Write the Message Routing Logic**
  * Relay HoD text commands down the matching `agent` socket.
  * Relay agent chat text responses back to the active `user` socket.
- [ ] **4. Implement Checklist State Persistence**
  * Write the handler for `state_update` payloads. 
  * Whenever the Mac Mini pushes a status update, parse the checklist JSON, write it to the `tasks` database table, and push the update to the phone.
- [x] **5. Implement the Task Status Update Endpoint**
  * Build the endpoint `POST /api/dept/:dept_id/sessions/:session_id/tasks/:task_id/status`.
  * Write code to:
    * Authenticate using token/bearer.
    * Update the database `tasks` table status column (`running` or `completed`) for the matching `task_id`.
    * Broadcast the new checklist state to the mobile WebSocket client.
- [ ] **6. Implement the Approval Loop API**
  * Handle incoming `request_approval` payloads from the Mac Mini: write them to the `approvals` table and notify the mobile socket.
  * Handle incoming `respond_approval` payloads from the phone: update the database and push the response down to the M4 Mac Mini.
- [ ] **7. Build Staging URL & Health Check Handlers**
  * Store the staging preview URLs sent by the Mac Mini in the `previews` table.
  * Handle incoming `heartbeat` payloads from the Mac Mini to update the `departments` table (status and `last_ping_at`).

---

## Phase 6: Railway Cloud App - Custom Mobile Frontend (PWA)
*Reference Specifications: [3. Custom Mobile UI (PWA Frontend)](file:///e:/hermes-ai/Railway_App_Specification.md#3-custom-mobile-ui-pwa-frontend)*

- [ ] **1. Initialize Frontend Project**
  * Create a mobile-responsive React/Vite web application.
  * Configure routing and state management (e.g. standard React Context or Nanostores).
- [ ] **2. Design the Simplified Chat Console**
  * Build a clean chat bubble interface.
  * Ensure system prompts, formatting logs, and code outputs are filtered out.
  * Render visual execution indicators (`Thinking...`, `Testing code...`) based on websocket updates.
- [ ] **3. Build the Task Checklist Component**
  * Build a mobile drop-down menu that reads from the `tasks` state.
  * Render checklist items with real-time status indicators (Done, In-Progress, Pending).
  * Render the **"Do Not" / Safety Constraints** section in a prominent red card under the checklist.
- [ ] **4. Build the Approval & Preview Modals**
  * Implement a blocking modal overlay for pending approvals (`Approve` / `Reject`).
  * Implement the floating preview banner that becomes active when a `staging_preview` URL is received, letting the HoD tap and open the staging site.
- [ ] **5. Build the OAuth Config Module**
  * Integrate GitHub and Railway OAuth redirect login flows.
  * Set up the UI to push the generated keys down the WebSocket room once authenticated, allowing hands-free configuration of the Mac Mini.

---

## Phase 7: E2E Verification & Play Testing

- [ ] **1. Run On-Device Boot checks**
  * Boot the M4 Mac Mini and verify `mailbox_client.py` connects successfully to Railway.
- [ ] **2. Run Mobile OAuth Setup**
  * Log in to the custom mobile app on a phone and link the department's GitHub and Railway accounts.
  * Verify that the tokens are successfully written to the Mac Mini's local `.env`.
- [ ] **3. Run a Smoke Test Task**
  * Send a test command from the phone: *"Create a static page with a button and deploy to staging."*
  * Verify:
    * The Main Brain rejects immediately if credentials fail.
    * The Main Brain proposes a plan and waits for approval.
    * Coder edits the file, and Tester runs Playwright tests.
    * Tester deploys to Railway Staging and returns the preview link.
    * The phone displays the "Preview Changes" button.
