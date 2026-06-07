/**
 * Hermes Swarm Coordinator - Client Application Logic
 * Simplified HTTP-only Polling & State-Driven Architecture
 */

(function () {
  // --- App State ---
  let activeDept = 'marketing';
  let sessionId = null;
  let pollTimer = null;
  let lastMessageCount = 0;
  let lastTaskStateHash = '';
  
  // DOM Elements
  const deptSelect = document.getElementById('dept-select');
  const connectionStatus = document.getElementById('connection-status');
  const agentStatusBadge = document.getElementById('agent-status-badge');
  const agentStatusLabel = document.getElementById('agent-status-label');
  const messageList = document.getElementById('message-list');
  const typingIndicator = document.getElementById('typing-indicator');
  const typingText = document.getElementById('typing-text');
  const chatForm = document.getElementById('chat-form');
  const chatInput = document.getElementById('chat-input');
  
  const progressText = document.getElementById('progress-text');
  const progressBarFill = document.getElementById('progress-bar-fill');
  const safetyCard = document.getElementById('safety-card');
  const safetyList = document.getElementById('safety-list');
  const taskList = document.getElementById('task-list');
  const emptyTasksState = document.getElementById('empty-tasks-state');
  
  const previewBanner = document.getElementById('preview-banner');
  const previewUrlText = document.getElementById('preview-url-text');
  const previewBtnLink = document.getElementById('preview-btn-link');
  const previewCloseBtn = document.getElementById('preview-close-btn');
  
  const approvalOverlay = document.getElementById('approval-overlay');
  const approvalSummary = document.getElementById('approval-summary');
  const approvalDescription = document.getElementById('approval-description');
  const approvalPlanCode = document.getElementById('approval-plan');
  const approvalFeedback = document.getElementById('approval-feedback');
  const approveBtn = document.getElementById('approve-btn');
  const rejectBtn = document.getElementById('reject-btn');
  
  const navChatBtn = document.getElementById('nav-chat-btn');
  const navTasksBtn = document.getElementById('nav-tasks-btn');
  const chatPaneView = document.getElementById('chat-pane-view');
  const checklistPaneView = document.getElementById('checklist-pane-view');

  let currentApprovalText = null;

  // --- Initialize App ---
  function init() {
    activeDept = deptSelect.value;
    
    // Set up event listeners
    deptSelect.addEventListener('change', handleDeptChange);
    chatForm.addEventListener('submit', handleSendMessage);
    previewCloseBtn.addEventListener('click', hidePreviewBanner);
    
    // Approval actions
    approveBtn.addEventListener('click', () => handleApprovalDecision(true));
    rejectBtn.addEventListener('click', () => handleApprovalDecision(false));
    
    // Mobile navigation
    navChatBtn.addEventListener('click', () => switchMobilePane('chat'));
    navTasksBtn.addEventListener('click', () => switchMobilePane('tasks'));
    
    // Initial load and start sync polling loop
    syncData();
    pollTimer = setInterval(syncData, 2000);
  }

  // --- Sync Data Polling Loop ---
  async function syncData() {
    try {
      updateConnectionStatus('connected');
      
      // Perform concurrent fetches for messages and tasks
      const [msgRes, taskRes] = await Promise.all([
        fetch(`/api/messages?dept=${activeDept}`),
        fetch(`/api/tasks?dept=${activeDept}`)
      ]);
      
      if (!msgRes.ok || !taskRes.ok) throw new Error('API Sync Error');
      
      const msgData = await msgRes.json();
      const taskData = await taskRes.json();
      
      sessionId = msgData.session_id;
      
      // Update Agent status depending on if there has been any activity
      updateAgentOnlineStatus(sessionId ? 'online' : 'offline');
      
      // 1. Process and render chat messages
      processMessages(msgData.messages);
      
      // 2. Process and render task checklist
      processTasks(taskData.tasks);
      
    } catch (err) {
      console.error('Data sync error:', err);
      updateConnectionStatus('disconnected');
      updateAgentOnlineStatus('offline');
    }
  }

  function updateConnectionStatus(state) {
    const statusDot = connectionStatus.querySelector('.status-dot');
    const statusText = connectionStatus.querySelector('.status-text');
    
    statusDot.className = 'status-dot';
    
    if (state === 'connected') {
      statusDot.classList.add('online');
      statusText.textContent = 'API Online';
    } else {
      statusDot.classList.add('offline');
      statusText.textContent = 'Offline';
    }
  }

  function handleDeptChange() {
    activeDept = deptSelect.value;
    console.log(`Department changed to: ${activeDept}`);
    
    // Reset hashes & states to force full rebuild
    sessionId = null;
    lastMessageCount = 0;
    lastTaskStateHash = '';
    currentApprovalText = null;
    
    hideApprovalModal();
    hidePreviewBanner();
    
    messageList.innerHTML = '';
    
    syncData();
  }

  // --- Message Processing ---
  function processMessages(messages) {
    if (!messages) return;
    
    // Only redraw if the count of messages has changed to prevent UI disruption
    if (messages.length !== lastMessageCount) {
      messageList.innerHTML = '';
      messages.forEach(msg => {
        appendMessageBubble(msg.sender, msg.text, msg.timestamp);
      });
      lastMessageCount = messages.length;
    }
    
    // Check if the latest message is a pending approval request
    if (messages.length > 0) {
      const latest = messages[messages.length - 1];
      if (latest.sender === 'agent' && latest.text.startsWith('[APPROVAL_REQUEST]')) {
        if (currentApprovalText !== latest.text) {
          showApprovalModal(latest.text);
        }
      } else {
        // If the latest message is no longer an approval request, close the modal
        hideApprovalModal();
      }
    } else {
      hideApprovalModal();
    }
  }

  // --- Task Checklist Processing ---
  function processTasks(tasks) {
    if (!tasks) return;
    
    // Create simple state hash to check for status updates
    const stateHash = tasks.map(t => `${t.id}:${t.status}`).join('|');
    if (stateHash === lastTaskStateHash) return;
    
    lastTaskStateHash = stateHash;
    renderChecklist(tasks);
  }

  // --- Send Message ---
  async function handleSendMessage(e) {
    e.preventDefault();
    const text = chatInput.value.trim();
    if (!text) return;
    
    chatInput.value = '';
    
    // Optimistic UI update
    appendMessageBubble('user', text);
    showTypingIndicator('Sending command...');
    
    try {
      const res = await fetch(`/api/messages?dept=${activeDept}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ sender: 'user', text: text })
      });
      if (!res.ok) throw new Error('Send failed');
      
      // Pull updates immediately
      await syncData();
    } catch (err) {
      console.error(err);
      appendSystemMessage('Failed to deliver message. Check connection.');
      hideTypingIndicator();
    }
  }

  // --- UI Renderers ---

  function appendMessageBubble(sender, text, timestamp) {
    const bubble = document.createElement('div');
    bubble.className = `message-bubble ${sender}`;
    
    const meta = document.createElement('div');
    meta.className = 'message-meta';
    
    const displayName = sender === 'user' ? 'You' : `${activeDept.charAt(0).toUpperCase() + activeDept.slice(1)} Agent`;
    
    let timeStr = '';
    if (timestamp) {
      const d = new Date(timestamp);
      timeStr = ` • ${d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}`;
    } else {
      const d = new Date();
      timeStr = ` • ${d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}`;
    }
    
    meta.textContent = `${displayName}${timeStr}`;
    
    const body = document.createElement('div');
    body.className = 'message-body';
    
    // Format approvals and previews nicely in inline bubbles
    if (text.startsWith('[APPROVAL_REQUEST]')) {
      body.innerHTML = `<span class="material-symbols-outlined text-warning" style="vertical-align:middle;margin-right:6px">security</span><strong>Requested execution plan approval. Check overlay.</strong>`;
    } else if (text.startsWith('[APPROVED]')) {
      body.innerHTML = `<span class="material-symbols-outlined text-success" style="vertical-align:middle;margin-right:6px">check_circle</span><strong>Approved plan:</strong> ${formatMessageText(text.replace('[APPROVED]', '').trim())}`;
    } else if (text.startsWith('[REJECTED]')) {
      body.innerHTML = `<span class="material-symbols-outlined text-danger" style="vertical-align:middle;margin-right:6px">cancel</span><strong>Rejected plan:</strong> ${formatMessageText(text.replace('[REJECTED]', '').trim())}`;
    } else {
      body.innerHTML = formatMessageText(text);
    }
    
    bubble.appendChild(meta);
    bubble.appendChild(body);
    
    messageList.appendChild(bubble);
    scrollChatToBottom();
  }

  function appendSystemMessage(text) {
    const container = document.createElement('div');
    container.className = 'system-message';
    
    const icon = document.createElement('span');
    icon.className = 'material-symbols-outlined';
    icon.textContent = 'info';
    
    const p = document.createElement('p');
    p.textContent = text;
    
    container.appendChild(icon);
    container.appendChild(p);
    
    messageList.appendChild(container);
    scrollChatToBottom();
  }

  function formatMessageText(text) {
    if (!text) return '';
    let clean = text
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;');
      
    clean = clean.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
    clean = clean.replace(/`(.*?)`/g, '<code class="inline-code">$1</code>');
    clean = clean.replace(/^\s*&gt;\s*(.*?)$/gm, '<blockquote>$1</blockquote>');
    clean = clean.replace(/(https?:\/\/[^\s]+)/g, '<a href="$1" target="_blank">$1</a>');
    
    return clean.replace(/\n/g, '<br>');
  }

  function scrollChatToBottom() {
    messageList.scrollTop = messageList.scrollHeight;
  }

  function updateAgentOnlineStatus(status) {
    const isOnline = status === 'online';
    agentStatusIndicator.className = `agent-status-indicator ${isOnline ? 'online' : 'offline'}`;
    agentStatusLabel.textContent = isOnline ? 'Agent Active' : 'Agent Idle';
  }

  function showTypingIndicator(label) {
    typingText.textContent = label || 'Agent is working...';
    typingIndicator.classList.remove('hidden');
    scrollChatToBottom();
  }

  function hideTypingIndicator() {
    typingIndicator.classList.add('hidden');
  }

  // --- Render Checklist Tasks & Safety warnings ---
  function renderChecklist(tasks) {
    taskList.innerHTML = '';
    
    if (!tasks || tasks.length === 0) {
      emptyTasksState.classList.remove('hidden');
      progressText.textContent = '0 / 0 Completed';
      progressBarFill.style.width = '0%';
      safetyCard.classList.add('hidden');
      return;
    }
    
    emptyTasksState.classList.add('hidden');
    
    const negativeConstraints = [];
    const regularTasks = [];
    
    tasks.forEach(task => {
      if (task.is_negative_constraint || task.title.toLowerCase().startsWith('do not') || task.title.toLowerCase().startsWith('don\'t')) {
        negativeConstraints.push(task);
      } else {
        regularTasks.push(task);
      }
    });
    
    // 1. Render Safety Warnings
    if (negativeConstraints.length > 0) {
      safetyList.innerHTML = '';
      negativeConstraints.forEach(task => {
        const li = document.createElement('li');
        li.textContent = task.title;
        safetyList.appendChild(li);
      });
      safetyCard.classList.remove('hidden');
    } else {
      safetyCard.classList.add('hidden');
    }
    
    // 2. Render Regular Checklist
    let completedCount = 0;
    
    if (regularTasks.length > 0) {
      regularTasks.forEach(task => {
        const item = document.createElement('div');
        item.className = `task-item ${task.status || 'pending'}`;
        
        const checkbox = document.createElement('div');
        checkbox.className = 'task-checkbox';
        
        const icon = document.createElement('span');
        icon.className = 'material-symbols-outlined task-checkbox-icon';
        
        if (task.status === 'completed') {
          icon.textContent = 'check_circle';
          completedCount++;
        } else if (task.status === 'running') {
          icon.textContent = 'sync';
          showTypingIndicator(`Executing: ${task.title}`);
        } else {
          icon.textContent = 'radio_button_unchecked';
        }
        
        checkbox.appendChild(icon);
        
        const wrapper = document.createElement('div');
        wrapper.className = 'task-content-wrapper';
        
        const title = document.createElement('span');
        title.className = 'task-title';
        title.textContent = task.title;
        
        wrapper.appendChild(title);
        
        if (task.success_criteria || task.detail) {
          const criteria = document.createElement('span');
          criteria.className = 'task-criteria';
          criteria.textContent = task.success_criteria || task.detail;
          wrapper.appendChild(criteria);
        }
        
        item.appendChild(checkbox);
        item.appendChild(wrapper);
        taskList.appendChild(item);
      });
    } else {
      const emptyDiv = document.createElement('div');
      emptyDiv.className = 'empty-tasks-state';
      emptyDiv.innerHTML = '<span class="material-symbols-outlined empty-icon">check_circle</span><p>All checks completed successfully.</p>';
      taskList.appendChild(emptyDiv);
    }
    
    // Update progress bar
    const totalCount = regularTasks.length;
    progressText.textContent = `${completedCount} / ${totalCount} Completed`;
    const percentage = totalCount > 0 ? Math.round((completedCount / totalCount) * 100) : 0;
    progressBarFill.style.width = `${percentage}%`;
    
    // Hide typing indicator if all are idle
    const isSomethingRunning = tasks.some(task => task.status === 'running');
    if (!isSomethingRunning) {
      hideTypingIndicator();
    }
  }

  // --- Staging Banner ---
  function showPreviewBanner(url, label) {
    previewUrlText.textContent = `${label || 'Staging URL'}: ${url}`;
    previewBtnLink.href = url;
    previewBanner.classList.remove('hidden');
  }

  function hidePreviewBanner() {
    previewBanner.classList.add('hidden');
  }

  // --- State-Driven Approval Modal ---
  function showApprovalModal(text) {
    currentApprovalText = text;
    
    // Parse the approval details
    // Format is: [APPROVAL_REQUEST]\nSummary: <summary>\nPlan:\n<plan>
    let summary = 'Execution plan approval requested.';
    let plan = '';
    
    const lines = text.split('\n');
    let planMode = false;
    
    for (let i = 0; i < lines.length; i++) {
      const line = lines[i].trim();
      if (line.startsWith('Summary:')) {
        summary = line.replace('Summary:', '').trim();
      } else if (line.startsWith('Plan:')) {
        planMode = true;
      } else if (planMode) {
        plan += lines[i] + '\n';
      }
    }
    
    if (!plan.trim()) {
      // Fallback if formatting was simpler
      plan = text.replace('[APPROVAL_REQUEST]', '').trim();
    }
    
    approvalSummary.textContent = summary;
    approvalPlanCode.textContent = plan.trim();
    approvalFeedback.value = '';
    
    approvalOverlay.classList.remove('hidden');
  }

  function hideApprovalModal() {
    approvalOverlay.classList.add('hidden');
    currentApprovalText = null;
  }

  async function handleApprovalDecision(approved) {
    if (!currentApprovalText) return;
    
    const feedback = approvalFeedback.value.trim();
    const cleanSummary = approvalSummary.textContent;
    
    // Format response message
    let responseText = '';
    if (approved) {
      responseText = `[APPROVED] ${cleanSummary}`;
    } else {
      responseText = `[REJECTED] ${cleanSummary}\nFeedback: ${feedback || 'No comments'}`;
    }
    
    showTypingIndicator('Transmitting approval decision...');
    
    try {
      const res = await fetch(`/api/messages?dept=${activeDept}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ sender: 'user', text: responseText })
      });
      if (!res.ok) throw new Error('Decision send failed');
      
      hideApprovalModal();
      
      // Pull immediately
      await syncData();
    } catch (err) {
      console.error(err);
      alert('Unable to transmit decision. Check network.');
      hideTypingIndicator();
    }
  }

  // --- Mobile View Switching ---
  function switchMobilePane(pane) {
    if (pane === 'chat') {
      navChatBtn.classList.add('active');
      navTasksBtn.classList.remove('active');
      chatPaneView.classList.remove('mobile-hidden');
      checklistPaneView.classList.add('mobile-hidden');
    } else {
      navChatBtn.classList.remove('active');
      navTasksBtn.classList.add('active');
      chatPaneView.classList.add('mobile-hidden');
      checklistPaneView.classList.remove('mobile-hidden');
    }
  }

  function handleResize() {
    if (window.innerWidth <= 768) {
      switchMobilePane('chat');
    } else {
      chatPaneView.classList.remove('mobile-hidden');
      checklistPaneView.classList.remove('mobile-hidden');
    }
  }
  
  window.addEventListener('resize', handleResize);
  document.addEventListener('DOMContentLoaded', () => {
    init();
    handleResize();
  });

})();
