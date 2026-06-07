// server.js
const express = require('express');
const http = require('http');
const WebSocket = require('ws');
const cors = require('cors');
const fs = require('fs');
const path = require('path');
const { Pool } = require('pg');
const sqlite3 = require('sqlite3').verbose();
require('dotenv').config();

const app = express();
app.use(cors());
app.use(express.json());
app.use(express.static(path.join(__dirname, 'public')));

const PORT = process.env.PORT || 3000;
const isPostgres = !!process.env.DATABASE_URL;
let db;

// --- 1. Database Connection & Schema Setup ---
async function initDb() {
  if (isPostgres) {
    console.log("Using PostgreSQL Database...");
    db = new Pool({
      connectionString: process.env.DATABASE_URL,
      ssl: process.env.DATABASE_URL.includes('localhost') ? false : { rejectUnauthorized: false }
    });
    // Auto-run schema creations
    try {
      const schemaSql = fs.readFileSync(path.join(__dirname, 'schema.sql'), 'utf8');
      await db.query(schemaSql);
      console.log("PostgreSQL Database tables verified/created successfully.");
    } catch (err) {
      console.error("Error initializing PostgreSQL schema:", err);
    }
  } else {
    console.log("Using SQLite Database...");
    const dbPath = path.join(__dirname, 'state.db');
    db = new sqlite3.Database(dbPath);
    
    // Convert PostgreSQL SERIAL/IF NOT EXISTS statements to SQLite syntax roughly or run standard schema query
    // To make it robust, let's run the schema commands one by one
    db.serialize(() => {
      db.run(`
        CREATE TABLE IF NOT EXISTS departments (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            status TEXT DEFAULT 'offline',
            last_ping_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
      `);
      db.run(`
        CREATE TABLE IF NOT EXISTS sessions (
            id TEXT PRIMARY KEY,
            department_id TEXT REFERENCES departments(id) ON DELETE CASCADE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
      `);
      db.run(`
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT REFERENCES sessions(id) ON DELETE CASCADE,
            sender TEXT CHECK (sender IN ('user', 'agent')),
            text TEXT NOT NULL,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
      `);
      db.run(`
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT REFERENCES sessions(id) ON DELETE CASCADE,
            title TEXT NOT NULL,
            status TEXT DEFAULT 'pending' CHECK (status IN ('pending', 'running', 'completed')),
            success_criteria TEXT,
            order_index INT,
            is_negative_constraint BOOLEAN DEFAULT FALSE
        )
      `);
      db.run(`
        CREATE TABLE IF NOT EXISTS approvals (
            id TEXT PRIMARY KEY,
            session_id TEXT REFERENCES sessions(id) ON DELETE CASCADE,
            description TEXT NOT NULL,
            status TEXT DEFAULT 'pending' CHECK (status IN ('pending', 'approved', 'rejected'))
        )
      `);
      db.run(`
        CREATE TABLE IF NOT EXISTS previews (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT REFERENCES sessions(id) ON DELETE CASCADE,
            url TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
      `);
      console.log("SQLite Database tables verified/created successfully.");
    });
  }
}

// Database helper functions to abstract Pg vs SQLite
function runQuery(sql, params = []) {
  return new Promise((resolve, reject) => {
    if (isPostgres) {
      db.query(sql, params)
        .then(res => resolve({ rows: res.rows, rowCount: res.rowCount }))
        .catch(err => reject(err));
    } else {
      // Convert PostgreSQL positional parameters $1, $2 to SQLite style ?, ?
      const sqliteSql = sql.replace(/\$(\d+)/g, '?');
      const isInsert = sqliteSql.trim().toUpperCase().startsWith('INSERT');
      const isUpdateOrDelete = sqliteSql.trim().toUpperCase().startsWith('UPDATE') || sqliteSql.trim().toUpperCase().startsWith('DELETE');
      
      if (isInsert || isUpdateOrDelete) {
        db.run(sqliteSql, params, function(err) {
          if (err) return reject(err);
          resolve({ rows: [], rowCount: this.changes, lastID: this.lastID });
        });
      } else {
        db.all(sqliteSql, params, (err, rows) => {
          if (err) return reject(err);
          resolve({ rows, rowCount: rows.length });
        });
      }
    }
  });
}

// --- 2. WebSocket Registry ---
// Structure: { [deptId]: { agents: Set<WebSocket>, users: Set<WebSocket> } }
const clientRooms = {};

function broadcastToRoom(deptId, roleType, messageObj) {
  const room = clientRooms[deptId];
  if (!room) return;
  
  const targets = roleType === 'user' ? room.users : room.agents;
  const payload = JSON.stringify(messageObj);
  
  targets.forEach(client => {
    if (client.readyState === WebSocket.OPEN) {
      client.send(payload);
    }
  });
}

// --- 3. Express HTTP Endpoints ---

// Task Status Update Endpoint (Called by Mac Mini agent or tools)
app.post('/api/dept/:dept_id/sessions/:session_id/tasks/:task_id/status', async (req, res) => {
  const { dept_id, session_id, task_id } = req.params;
  const { status } = req.body;
  
  if (!status || !['pending', 'running', 'completed'].includes(status)) {
    return res.status(400).json({ error: "Invalid status parameter. Must be pending, running, or completed." });
  }
  
  try {
    // 1. Update status in database
    const updateResult = await runQuery(
      `UPDATE tasks SET status = $1 WHERE id = $2 AND session_id = $3`,
      [status, parseInt(task_id), session_id]
    );
    
    if (updateResult.rowCount === 0) {
      // If the task wasn't found, let's try creating/inserting it as a fallback if dynamic task syncing is active
      // For now, return 404
      return res.status(404).json({ error: `Task ID ${task_id} not found in session ${session_id}.` });
    }
    
    // 2. Fetch the revised list of tasks
    const tasksResult = await runQuery(
      `SELECT id, title, status, success_criteria, order_index, is_negative_constraint 
       FROM tasks WHERE session_id = $1 ORDER BY order_index ASC, id ASC`,
      [session_id]
    );
    
    const checklist = tasksResult.rows;
    
    // 3. Broadcast the state update to all mobile phone users in this department
    broadcastToRoom(dept_id, 'user', {
      type: "state_update",
      session_id,
      checklist
    });
    
    console.log(`Task ${task_id} status updated to '${status}' in session ${session_id} (Department: ${dept_id}). Broadcasted to users.`);
    return res.json({ success: true, task_id, status });
  } catch (err) {
    console.error("Error updating task status:", err);
    return res.status(500).json({ error: "Internal Database Error" });
  }
});

// Fetch active session checklist (Called by Mobile App)
app.get('/api/dept/:dept_id/sessions/active', async (req, res) => {
  const { dept_id } = req.params;
  try {
    // Find the latest active session for this department
    const sessionResult = await runQuery(
      `SELECT id FROM sessions WHERE department_id = $1 ORDER BY created_at DESC LIMIT 1`,
      [dept_id]
    );
    
    if (sessionResult.rows.length === 0) {
      return res.json({ session_id: null, checklist: [], messages: [] });
    }
    
    const session_id = sessionResult.rows[0].id;
    
    // Fetch checklist
    const tasksResult = await runQuery(
      `SELECT id, title, status, success_criteria, order_index, is_negative_constraint 
       FROM tasks WHERE session_id = $1 ORDER BY order_index ASC, id ASC`,
      [session_id]
    );
    
    // Fetch recent messages
    const messagesResult = await runQuery(
      `SELECT sender, text, timestamp FROM messages WHERE session_id = $1 ORDER BY timestamp ASC`,
      [session_id]
    );
    
    return res.json({
      session_id,
      checklist: tasksResult.rows,
      messages: messagesResult.rows
    });
  } catch (err) {
    console.error("Error fetching active session:", err);
    return res.status(500).json({ error: "Internal Database Error" });
  }
});


// --- Simplified REST API for HTTP-only Polling & Updates ---

// Helper function to find or create the active session for a department
async function getOrCreateActiveSession(dept_id) {
  let sessionResult = await runQuery(
    `SELECT id FROM sessions WHERE department_id = $1 ORDER BY created_at DESC LIMIT 1`,
    [dept_id]
  );
  if (sessionResult.rows.length > 0) {
    return sessionResult.rows[0].id;
  }
  const session_id = `sess_${Date.now()}`;
  await runQuery(`INSERT INTO sessions (id, department_id) VALUES ($1, $2)`, [session_id, dept_id]);
  return session_id;
}

// 1. GET /api/messages
app.get('/api/messages', async (req, res) => {
  const dept = req.query.dept || 'marketing';
  try {
    const session_id = await getOrCreateActiveSession(dept);
    const result = await runQuery(
      `SELECT sender, text, timestamp FROM messages WHERE session_id = $1 ORDER BY timestamp ASC`,
      [session_id]
    );
    return res.json({ session_id, messages: result.rows });
  } catch (err) {
    console.error("Error fetching messages:", err);
    return res.status(500).json({ error: "Internal Database Error" });
  }
});

// 2. POST /api/messages
app.post('/api/messages', async (req, res) => {
  const dept = req.query.dept || 'marketing';
  const { text, sender } = req.body;
  if (!text) {
    return res.status(400).json({ error: "Message text is required." });
  }
  const msgSender = sender || 'user';
  try {
    const session_id = await getOrCreateActiveSession(dept);
    await runQuery(
      `INSERT INTO messages (session_id, sender, text) VALUES ($1, $2, $3)`,
      [session_id, msgSender, text]
    );
    return res.json({ success: true, session_id });
  } catch (err) {
    console.error("Error saving message:", err);
    return res.status(500).json({ error: "Internal Database Error" });
  }
});

// 5. POST /api/sessions/new
app.post('/api/sessions/new', async (req, res) => {
  const dept = req.query.dept || 'marketing';
  try {
    const session_id = `sess_${Date.now()}`;
    await runQuery(`INSERT INTO sessions (id, department_id) VALUES ($1, $2)`, [session_id, dept]);
    console.log(`Manual new session created: ${session_id} for department: ${dept}`);
    return res.json({ success: true, session_id });
  } catch (err) {
    console.error("Error creating manual session:", err);
    return res.status(500).json({ error: "Internal Database Error" });
  }
});

// 3. GET /api/tasks
app.get('/api/tasks', async (req, res) => {
  const dept = req.query.dept || 'marketing';
  try {
    const session_id = await getOrCreateActiveSession(dept);
    const result = await runQuery(
      `SELECT id, title, status, success_criteria, order_index, is_negative_constraint 
       FROM tasks WHERE session_id = $1 ORDER BY order_index ASC, id ASC`,
      [session_id]
    );
    return res.json({ session_id, tasks: result.rows });
  } catch (err) {
    console.error("Error fetching tasks:", err);
    return res.status(500).json({ error: "Internal Database Error" });
  }
});

// 4. POST /api/tasks
app.post('/api/tasks', async (req, res) => {
  const dept = req.query.dept || 'marketing';
  const { title, status, success_criteria } = req.body;
  if (!title || !status) {
    return res.status(400).json({ error: "Title and status are required." });
  }
  try {
    const session_id = await getOrCreateActiveSession(dept);
    
    // Check if task with title exists in the active session
    const existing = await runQuery(
      `SELECT id FROM tasks WHERE session_id = $1 AND title = $2 LIMIT 1`,
      [session_id, title]
    );
    
    if (existing.rows.length > 0) {
      // Update existing
      await runQuery(
        `UPDATE tasks SET status = $1, success_criteria = $2 WHERE session_id = $3 AND title = $4`,
        [status, success_criteria || '', session_id, title]
      );
      return res.json({ success: true, updated: true, title, status });
    } else {
      // Fetch count to set order index
      const countResult = await runQuery(`SELECT count(*) as count FROM tasks WHERE session_id = $1`, [session_id]);
      const count = (countResult.rows && countResult.rows[0]) ? (countResult.rows[0].count || 0) : 0;
      
      // Insert new
      await runQuery(
        `INSERT INTO tasks (session_id, title, status, success_criteria, order_index) VALUES ($1, $2, $3, $4, $5)`,
        [session_id, title, status, success_criteria || '', count]
      );
      return res.json({ success: true, created: true, title, status });
    }
  } catch (err) {
    console.error("Error upserting task:", err);
    return res.status(500).json({ error: "Internal Database Error" });
  }
});

// Setup fallback route
app.get('/health', (req, res) => {
  res.json({ status: "ok", mode: isPostgres ? "postgresql" : "sqlite" });
});

// --- 4. HTTP & WebSocket Server Startup ---
const server = http.createServer(app);
const wss = new WebSocket.Server({ server });

wss.on('connection', (ws) => {
  let registeredDept = null;
  let registeredRole = null;
  
  ws.on('message', async (messageStr) => {
    try {
      const payload = JSON.parse(messageStr);
      
      switch (payload.type) {
        case 'register': {
          const { department_id, role } = payload;
          if (!department_id || !['agent', 'user'].includes(role)) {
            ws.send(JSON.stringify({ type: "error", message: "Invalid registration parameters." }));
            return;
          }
          
          registeredDept = department_id;
          registeredRole = role;
          
          if (!clientRooms[department_id]) {
            clientRooms[department_id] = { agents: new Set(), users: new Set() };
          }
          
          if (role === 'agent') {
            clientRooms[department_id].agents.add(ws);
            // Update department status to online
            await runQuery(
              `INSERT INTO departments (id, name, status, last_ping_at) 
               VALUES ($1, $2, 'online', CURRENT_TIMESTAMP)
               ON CONFLICT (id) DO UPDATE SET status = 'online', last_ping_at = CURRENT_TIMESTAMP`,
              [department_id, `${department_id.charAt(0).toUpperCase() + department_id.slice(1)} Team`]
            );
            console.log(`Agent registered for department: ${department_id}`);
          } else {
            clientRooms[department_id].users.add(ws);
            console.log(`User registered for department: ${department_id}`);
          }
          
          ws.send(JSON.stringify({ type: "registered", status: "success", department_id, role }));
          break;
        }
        
        case 'command': {
          // Relays user text commands down to the agent
          if (registeredRole !== 'user') return;
          console.log(`Received command from user in ${registeredDept}: ${payload.text}`);
          
          // Fetch or create session
          let session_id;
          const sessionResult = await runQuery(
            `SELECT id FROM sessions WHERE department_id = $1 ORDER BY created_at DESC LIMIT 1`,
            [registeredDept]
          );
          
          if (sessionResult.rows.length > 0) {
            session_id = sessionResult.rows[0].id;
          } else {
            session_id = `sess_${Date.now()}`;
            await runQuery(`INSERT INTO sessions (id, department_id) VALUES ($1, $2)`, [session_id, registeredDept]);
          }
          
          // Save message to DB
          await runQuery(
            `INSERT INTO messages (session_id, sender, text) VALUES ($1, 'user', $2)`,
            [session_id, payload.text]
          );
          
          // Relay message down to agents
          broadcastToRoom(registeredDept, 'agent', {
            type: "command",
            session_id,
            text: payload.text
          });
          break;
        }
        case 'agent_chat': {
          if (registeredRole !== 'agent') return;
          const { session_id, content } = payload;
          if (!session_id || !content) return;
          
          console.log(`Received agent_chat from agent in ${registeredDept} for session ${session_id}`);
          
          // Save message to DB
          await runQuery(
            `INSERT INTO messages (session_id, sender, text) VALUES ($1, 'agent', $2)`,
            [session_id, content]
          );
          
          // Relay message to users
          broadcastToRoom(registeredDept, 'user', {
            type: "agent_chat",
            session_id,
            content,
            role: payload.role || 'agent'
          });
          break;
        }
        
        case 'state_update': {
          // Relays agent state updates (checklist) to users
          if (registeredRole !== 'agent') return;
          const { session_id, checklist } = payload;
          if (!session_id || !Array.isArray(checklist)) return;
          
          console.log(`Received state_update from agent in ${registeredDept} for session ${session_id}`);
          
          // Save or update tasks list in the database
          // First delete existing tasks for this session, then insert them in order
          await runQuery(`DELETE FROM tasks WHERE session_id = $1`, [session_id]);
          for (let i = 0; i < checklist.length; i++) {
            const task = checklist[i];
            await runQuery(
              `INSERT INTO tasks (session_id, title, status, success_criteria, order_index, is_negative_constraint) 
               VALUES ($1, $2, $3, $4, $5, $6)`,
              [
                session_id,
                task.title,
                task.status || 'pending',
                task.success_criteria || '',
                i,
                !!task.is_negative_constraint
              ]
            );
          }
          
          // Fetch newly created checklist with IDs back to send it to the mobile user
          const tasksResult = await runQuery(
            `SELECT id, title, status, success_criteria, order_index, is_negative_constraint 
             FROM tasks WHERE session_id = $1 ORDER BY order_index ASC, id ASC`,
            [session_id]
          );
          
          // Relay back to the user sockets
          broadcastToRoom(registeredDept, 'user', {
            type: "state_update",
            session_id,
            checklist: tasksResult.rows
          });
          break;
        }
        
        case 'request_approval': {
          if (registeredRole !== 'agent') return;
          const { session_id, approval_id, description } = payload;
          if (!session_id || !approval_id || !description) return;
          
          console.log(`Received request_approval from agent in ${registeredDept}: ${description}`);
          
          await runQuery(
            `INSERT INTO approvals (id, session_id, description, status) 
             VALUES ($1, $2, $3, 'pending')
             ON CONFLICT (id) DO UPDATE SET description = $3, status = 'pending'`,
            [approval_id, session_id, description]
          );
          
          broadcastToRoom(registeredDept, 'user', payload);
          break;
        }
        
        case 'respond_approval': {
          if (registeredRole !== 'user') return;
          const { session_id, approval_id, approved } = payload;
          if (!session_id || !approval_id) return;
          
          const status = approved ? 'approved' : 'rejected';
          console.log(`Received respond_approval from user: ${approval_id} -> ${status}`);
          
          await runQuery(
            `UPDATE approvals SET status = $1 WHERE id = $2 AND session_id = $3`,
            [status, approval_id, session_id]
          );
          
          broadcastToRoom(registeredDept, 'agent', payload);
          break;
        }
        
        case 'heartbeat': {
          if (registeredRole !== 'agent') return;
          await runQuery(
            `UPDATE departments SET status = 'online', last_ping_at = CURRENT_TIMESTAMP WHERE id = $1`,
            [registeredDept]
          );
          break;
        }
        
        default:
          console.log(`Unhandled message type: ${payload.type}`);
      }
    } catch (err) {
      console.error("Failed to parse WebSocket message:", err);
    }
  });
  
  ws.on('close', async () => {
    if (registeredDept && registeredRole) {
      const room = clientRooms[registeredDept];
      if (room) {
        if (registeredRole === 'agent') {
          room.agents.delete(ws);
          // Update status to offline
          await runQuery(
            `UPDATE departments SET status = 'offline', last_ping_at = CURRENT_TIMESTAMP WHERE id = $1`,
            [registeredDept]
          );
          console.log(`Agent disconnected from department: ${registeredDept}`);
        } else {
          room.users.delete(ws);
          console.log(`User disconnected from department: ${registeredDept}`);
        }
      }
    }
  });
});

// Run
initDb().then(() => {
  server.listen(PORT, () => {
    console.log(`Coordinator server listening on port ${PORT}`);
  });
});
