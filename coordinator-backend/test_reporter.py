#!/usr/bin/env python3
"""
test_reporter.py - Integration Test for Task Status Reporting

Boots the Express coordinator server locally, creates mock DB records,
uses the python reporting tool to submit status changes, and verifies the update.
"""

import os
import sys
import time
import subprocess
import sqlite3
import urllib.request
import json

# Ensure we can import from hermes-agent/tools
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "hermes-agent")))

from tools.report_tool import report_task_status

def setup_test_db():
    print("[1/5] Setting up mock SQLite database...")
    db_path = os.path.join(os.path.dirname(__file__), "state.db")
    if os.path.exists(db_path):
        os.remove(db_path)
        
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Create tables
    cursor.execute("""
        CREATE TABLE departments (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            status TEXT DEFAULT 'offline',
            last_ping_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    cursor.execute("""
        CREATE TABLE sessions (
            id TEXT PRIMARY KEY,
            department_id TEXT REFERENCES departments(id) ON DELETE CASCADE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    cursor.execute("""
        CREATE TABLE tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT REFERENCES sessions(id) ON DELETE CASCADE,
            title TEXT NOT NULL,
            status TEXT DEFAULT 'pending' CHECK (status IN ('pending', 'running', 'completed')),
            success_criteria TEXT,
            order_index INT,
            is_negative_constraint BOOLEAN DEFAULT FALSE
        )
    """)
    
    # Insert mock records
    cursor.execute("INSERT INTO departments (id, name, status) VALUES ('marketing', 'Marketing Team', 'online')")
    cursor.execute("INSERT INTO sessions (id, department_id) VALUES ('sess_test_123', 'marketing')")
    cursor.execute("INSERT INTO tasks (id, session_id, title, status, order_index) VALUES (1, 'sess_test_123', 'Analyze request', 'pending', 0)")
    
    conn.commit()
    conn.close()
    print("[1/5] SQLite database set up successfully.")

def start_server():
    print("[2/5] Starting coordinator backend server...")
    server_path = os.path.join(os.path.dirname(__file__), "server.js")
    
    # Launch server as subprocess, pointing to SQLite
    env = os.environ.copy()
    env["PORT"] = "3500" # Use a non-conflicting port for testing
    
    proc = subprocess.Popen(
        ["node", server_path],
        env=env
    )
    
    # Give server 2 seconds to start
    time.sleep(2.0)
    return proc

def run_tests():
    print("[3/5] Setting environment variables and executing report tool...")
    
    # Configure tool environment
    os.environ["SESSION_ID"] = "sess_test_123"
    os.environ["DEPARTMENT_ID"] = "marketing"
    os.environ["COMMAND_CENTER_URL"] = "http://localhost:3500"
    
    # 1. Report "running"
    print("Sending: task_id=1, status=running")
    result_running = report_task_status("1", "running")
    print("Result:", result_running)
    assert "running" in result_running, f"Expected 'running' status. Got: {result_running}"
    
    # Check DB directly
    db_path = os.path.join(os.path.dirname(__file__), "state.db")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT status FROM tasks WHERE id = 1")
    status = cursor.fetchone()[0]
    conn.close()
    print("Database checked: task status is", status)
    assert status == "running", f"Expected 'running' database status. Got: {status}"
    
    # 2. Report "completed"
    print("Sending: task_id=1, status=completed")
    result_completed = report_task_status("1", "completed")
    print("Result:", result_completed)
    assert "completed" in result_completed, f"Expected 'completed' status. Got: {result_completed}"
    
    # Check DB again
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT status FROM tasks WHERE id = 1")
    status = cursor.fetchone()[0]
    conn.close()
    print("Database checked: task status is", status)
    assert status == "completed", f"Expected 'completed' database status. Got: {status}"
    
    print("[4/5] All assertions passed!")

def main():
    proc = None
    try:
        setup_test_db()
        proc = start_server()
        run_tests()
    except Exception as e:
        print("[FAIL] Test encountered an error:", e)
        if proc:
            proc.terminate()
        sys.exit(1)
    finally:
        if proc:
            print("[5/5] Shutting down coordinator server...")
            proc.terminate()
            proc.wait()
            print("Cleanup complete.")

if __name__ == "__main__":
    main()
