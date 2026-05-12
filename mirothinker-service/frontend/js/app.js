// === App State ===
const state = {
  isRunning: false,
  currentTaskId: null,
  pollInterval: null,
  resultMarkdown: '',
};

// === DOM Elements ===
const elements = {
  form: document.getElementById('research-form'),
  submitBtn: document.getElementById('submit-btn'),
  btnText: document.querySelector('.btn-text'),
  btnLoading: document.querySelector('.btn-loading'),
  tempValue: document.getElementById('temp-value'),
  resultPanel: document.getElementById('result-panel'),
  resultContent: document.getElementById('result-content'),
  resultTime: document.getElementById('result-time'),
  resultTurns: document.getElementById('result-turns'),
  statusPanel: document.getElementById('status-panel'),
  statusSteps: document.getElementById('status-steps'),
  statusLog: document.getElementById('status-log'),
  copyBtn: document.getElementById('copy-btn'),
  downloadBtn: document.getElementById('download-btn'),
  toastContainer: document.getElementById('toast-container'),
};

// === Event Listeners ===
elements.form.addEventListener('submit', handleFormSubmit);
document.getElementById('temperature').addEventListener('input', (e) => {
  elements.tempValue.textContent = e.target.value;
});
elements.copyBtn.addEventListener('click', copyResult);
elements.downloadBtn.addEventListener('click', downloadResult);

// === Core Functions ===
async function handleFormSubmit(e) {
  e.preventDefault();

  if (state.isRunning) return;

  const query = document.getElementById('query').value.trim();
  if (!query) {
    showToast('请输入研究问题', 'error');
    return;
  }

  const params = {
    query,
    max_turns: parseInt(document.getElementById('max-turns').value),
    context_keep: parseInt(document.getElementById('context-keep').value),
    model: document.getElementById('model').value,
    temperature: parseFloat(document.getElementById('temperature').value),
  };

  // Start research
  state.isRunning = true;
  elements.submitBtn.disabled = true;
  elements.btnText.style.display = 'none';
  elements.btnLoading.style.display = 'flex';

  // Show status panel
  elements.statusPanel.style.display = 'block';
  elements.resultPanel.style.display = 'none';
  resetStatusSteps();
  elements.statusLog.innerHTML = '';

  addLog('启动研究任务...');
  updateStep('starting', 'active');

  try {
    const response = await fetch('/api/research', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(params),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || '研究任务启动失败');
    }

    const data = await response.json();
    state.currentTaskId = data.task_id;

    addLog(`任务 ID: ${data.task_id}`);
    addLog('Agent 开始执行研究流程...');
    updateStep('starting', 'completed');
    updateStep('searching', 'active');

    // Start polling for results
    startPolling(data.task_id);

  } catch (err) {
    addLog(`错误: ${err.message}`, 'error');
    showToast(`研究失败: ${err.message}`, 'error');
    resetUI();
  }
}

function startPolling(taskId) {
  if (state.pollInterval) {
    clearInterval(state.pollInterval);
  }

  state.pollInterval = setInterval(async () => {
    try {
      const response = await fetch(`/api/research/${taskId}`);
      const data = await response.json();

      if (data.error) {
        clearInterval(state.pollInterval);
        addLog(`研究出错: ${data.error}`, 'error');
        showToast('研究完成但结果解析出错', 'error');
        resetUI();
        return;
      }

      if (data.status === 'completed') {
        clearInterval(state.pollInterval);
        displayResult(data);
        resetUI();
      } else if (data.status === 'failed') {
        clearInterval(state.pollInterval);
        addLog('研究任务失败', 'error');
        showToast('研究任务失败，请重试', 'error');
        resetUI();
      } else {
        // Still running - update status
        updateStatusFromData(data);
      }
    } catch (err) {
      console.error('Polling error:', err);
    }
  }, 3000);
}

function updateStatusFromData(data) {
  // Update step indicators based on agent state
  const turn = data.turn_count || 0;
  const elapsed = data.elapsed_time || 0;

  if (turn < 5) {
    updateStep('searching', 'active');
  } else if (turn < 20) {
    updateStep('searching', 'completed');
    updateStep('analyzing', 'active');
  } else {
    updateStep('searching', 'completed');
    updateStep('analyzing', 'completed');
    updateStep('synthesizing', 'active');
  }

  addLog(`轮次: ${turn} | 耗时: ${formatTime(elapsed)}`);
}

function displayResult(data) {
  updateStep('synthesizing', 'completed');
  addLog('研究完成!');

  state.resultMarkdown = data.result || '';

  // Render markdown as HTML (simple rendering)
  elements.resultContent.innerHTML = renderMarkdown(state.resultMarkdown);

  // Update meta
  elements.resultTime.textContent = `耗时: ${formatTime(data.elapsed_time || 0)}`;
  elements.resultTurns.textContent = `轮次: ${data.turn_count || 0}`;

  // Show result panel
  elements.resultPanel.style.display = 'block';
  elements.statusPanel.style.display = 'none';

  showToast('研究完成!', 'success');
}

function resetUI() {
  state.isRunning = false;
  elements.submitBtn.disabled = false;
  elements.btnText.style.display = 'flex';
  elements.btnLoading.style.display = 'none';
  if (state.pollInterval) {
    clearInterval(state.pollInterval);
    state.pollInterval = null;
  }
}

function resetStatusSteps() {
  const steps = elements.statusSteps.querySelectorAll('.status-step');
  steps.forEach(step => {
    step.classList.remove('active', 'completed');
  });
}

function updateStep(stepName, status) {
  const step = elements.statusSteps.querySelector(`[data-step="${stepName}"]`);
  if (!step) return;
  step.classList.remove('active', 'completed');
  if (status) {
    step.classList.add(status);
  }
}

function addLog(message, type = 'info') {
  const time = new Date().toLocaleTimeString('zh-CN');
  const entry = document.createElement('div');
  entry.textContent = `[${time}] ${message}`;
  if (type === 'error') {
    entry.style.color = 'var(--error)';
  }
  elements.statusLog.appendChild(entry);
  elements.statusLog.scrollTop = elements.statusLog.scrollHeight;
}

// === Utility Functions ===
function formatTime(seconds) {
  const mins = Math.floor(seconds / 60);
  const secs = Math.floor(seconds % 60);
  return `${mins}分${secs}秒`;
}

function showToast(message, type = 'info') {
  const toast = document.createElement('div');
  toast.className = `toast toast-${type}`;
  toast.textContent = message;
  elements.toastContainer.appendChild(toast);

  setTimeout(() => {
    toast.style.opacity = '0';
    toast.style.transform = 'translateX(20px)';
    setTimeout(() => toast.remove(), 300);
  }, 3000);
}

// Simple Markdown renderer
function renderMarkdown(text) {
  if (!text) return '<p>暂无结果</p>';

  return text
    // Code blocks
    .replace(/```(\w*)\n([\s\S]*?)```/g, '<pre><code>$2</code></pre>')
    // Inline code
    .replace(/`([^`]+)`/g, '<code>$1</code>')
    // Headers
    .replace(/^### (.+)$/gm, '<h3>$1</h3>')
    .replace(/^## (.+)$/gm, '<h2>$1</h2>')
    .replace(/^# (.+)$/gm, '<h1>$1</h1>')
    // Bold
    .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
    // Italic
    .replace(/\*(.+?)\*/g, '<em>$1</em>')
    // Blockquotes
    .replace(/^> (.+)$/gm, '<blockquote>$1</blockquote>')
    // Unordered lists
    .replace(/^[-*] (.+)$/gm, '<li>$1</li>')
    // Ordered lists
    .replace(/^\d+\. (.+)$/gm, '<li>$1</li>')
    // Line breaks to paragraphs
    .replace(/\n\n/g, '</p><p>')
    .replace(/\n/g, '<br>');
}

// === Copy & Download ===
function copyResult() {
  navigator.clipboard.writeText(state.resultMarkdown).then(() => {
    showToast('结果已复制到剪贴板', 'success');
  }).catch(() => {
    showToast('复制失败', 'error');
  });
}

function downloadResult() {
  const blob = new Blob([state.resultMarkdown], { type: 'text/markdown' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = `mirothinker-research-${Date.now()}.md`;
  a.click();
  URL.revokeObjectURL(url);
  showToast('结果已下载', 'success');
}
