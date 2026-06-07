#!/usr/bin/env python3
"""
hermes_http_client.py - Simple HTTP Client for Hermes Agent

Provides a dead-simple utility for the local Python Hermes Agent to:
1. Poll for user commands.
2. Send replies back to the chat log.
3. Register and update task checklist statuses (without needing task IDs).
"""

import json
import urllib.request
import urllib.parse
from typing import List, Dict, Any, Optional

class HermesHTTPClient:
    def __init__(self, base_url: str = "http://localhost:3000", dept: str = "marketing"):
        self.base_url = base_url.rstrip("/")
        self.dept = dept
        self.last_seen_timestamp = None

    def _post(self, path: str, payload: dict) -> dict:
        url = f"{self.base_url}{path}?dept={self.dept}"
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            url,
            data=data,
            headers={"Content-Type": "application/json"},
            method="POST"
        )
        with urllib.request.urlopen(req, timeout=10) as response:
            return json.loads(response.read().decode("utf-8"))

    def _get(self, path: str) -> dict:
        url = f"{self.base_url}{path}?dept={self.dept}"
        with urllib.request.urlopen(url, timeout=10) as response:
            return json.loads(response.read().decode("utf-8"))

    def get_messages(self) -> List[Dict[str, Any]]:
        """Fetch full chat history."""
        try:
            res = self._get("/api/messages")
            return res.get("messages", [])
        except Exception as e:
            print(f"[Client Error] Failed to fetch messages: {e}")
            return []

    def get_latest_command(self) -> Optional[str]:
        """
        Polls the chat. If the latest message is from the user, returns it.
        Otherwise, returns None.
        """
        messages = self.get_messages()
        if not messages:
            return None
        
        latest = messages[-1]
        if latest.get("sender") == "user":
            return latest.get("text")
        return None

    def send_reply(self, text: str) -> bool:
        """Send an agent reply back to the chat room."""
        try:
            res = self._post("/api/messages", {"sender": "agent", "text": text})
            return res.get("success", False)
        except Exception as e:
            print(f"[Client Error] Failed to send reply: {e}")
            return False

    def request_approval(self, summary: str, plan: str) -> bool:
        """
        Pauses and posts an approval request message.
        Formatted specifically so the UI will open the modal window.
        """
        payload_text = f"[APPROVAL_REQUEST]\nSummary: {summary}\nPlan:\n{plan}"
        return self.send_reply(payload_text)

    def report_task(self, title: str, status: str, success_criteria: str = "") -> bool:
        """
        Upsert a task checklist item.
        Automatically creates it if it doesn't exist, otherwise updates its status.
        """
        try:
            payload = {
                "title": title,
                "status": status,
                "success_criteria": success_criteria
            }
            res = self._post("/api/tasks", payload)
            return res.get("success", False)
        except Exception as e:
            print(f"[Client Error] Failed to update task '{title}': {e}")
            return False


# --- Quick Test Driver ---
if __name__ == "__main__":
    import time
    
    print("Initializing Hermes simple HTTP Client...")
    client = HermesHTTPClient(base_url="http://localhost:3000", dept="marketing")
    
    # 1. Post a test message
    print("\n1. Testing Chat message delivery...")
    if client.send_reply("Hello! This is a test message from the local Hermes agent python client."):
        print("-> Message posted successfully.")
    
    # 2. Add some checklist items
    print("\n2. Testing Task checklist updates (smart upsert)...")
    client.report_task("Analyze instructions", "completed", "Review prompt directives")
    client.report_task("Run smoke tests", "running", "Confirm standard systems are online")
    
    print("Wait 2 seconds...")
    time.sleep(2)
    
    client.report_task("Run smoke tests", "completed", "Smoke tests passed in 1.4s")
    client.report_task("Deploying application to staging", "running", "Pushing to remote build server")
    print("-> Checklist updated successfully.")
    
    # 3. Requesting a plan approval
    print("\n3. Testing Approval request flow...")
    plan_code = "npm run test\npython setup.py install"
    client.request_approval("Run testing phase", plan_code)
    print("-> Approval request uploaded. Open http://localhost:3000 to verify.")
