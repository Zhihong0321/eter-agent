-- schema.sql
-- Database schema for the Railway App coordinator backend

-- 1. Departments / Active Profiles
CREATE TABLE IF NOT EXISTS departments (
    id VARCHAR(50) PRIMARY KEY, -- e.g., "marketing", "sales"
    name VARCHAR(100) NOT NULL,
    status VARCHAR(20) DEFAULT 'offline', -- 'online' or 'offline'
    last_ping_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    activity TEXT
);

-- 2. Chat Sessions
CREATE TABLE IF NOT EXISTS sessions (
    id VARCHAR(50) PRIMARY KEY,
    department_id VARCHAR(50) REFERENCES departments(id) ON DELETE CASCADE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 3. Messages
CREATE TABLE IF NOT EXISTS messages (
    id SERIAL PRIMARY KEY,
    session_id VARCHAR(50) REFERENCES sessions(id) ON DELETE CASCADE,
    sender VARCHAR(10) CHECK (sender IN ('user', 'agent')), -- who sent it
    text TEXT NOT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 4. Task Checklists
CREATE TABLE IF NOT EXISTS tasks (
    id SERIAL PRIMARY KEY,
    session_id VARCHAR(50) REFERENCES sessions(id) ON DELETE CASCADE,
    title VARCHAR(255) NOT NULL,
    status VARCHAR(20) DEFAULT 'pending' CHECK (status IN ('pending', 'running', 'completed')),
    success_criteria TEXT,
    order_index INT,
    is_negative_constraint BOOLEAN DEFAULT FALSE -- Flag for "Do Not..." safety boundaries
);

-- 5. Approval Requests
CREATE TABLE IF NOT EXISTS approvals (
    id VARCHAR(50) PRIMARY KEY,
    session_id VARCHAR(50) REFERENCES sessions(id) ON DELETE CASCADE,
    description TEXT NOT NULL,
    status VARCHAR(20) DEFAULT 'pending' CHECK (status IN ('pending', 'approved', 'rejected'))
);

-- 6. Staging Preview URLs
CREATE TABLE IF NOT EXISTS previews (
    id SERIAL PRIMARY KEY,
    session_id VARCHAR(50) REFERENCES sessions(id) ON DELETE CASCADE,
    url TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
