// 설정
const CONFIG = {
    apiUrl: 'http://localhost:8080',  // 백엔드 서버 URL
    projectId: 'gsneotek-ncc-demo',
    location: 'us-central1',
    resourceId: null,  // Agent Engine Resource ID (설정 필요)
    userId: 'traveler-' + Date.now(),
    sessionId: null,
    autoScroll: true,
    logPollInterval: 10000,  // 로그 폴링 간격 (ms) - 429 에러 방지를 위해 10초로 증가
};

// DOM 요소
const chatMessages = document.getElementById('chatMessages');
const messageInput = document.getElementById('messageInput');
const sendButton = document.getElementById('sendButton');
const stopButton = document.getElementById('stopButton');
const logsContent = document.getElementById('logsContent');
const connectionStatus = document.getElementById('connectionStatus');
const statusText = document.getElementById('statusText');
const clearLogsBtn = document.getElementById('clearLogs');
const toggleAutoScrollBtn = document.getElementById('toggleAutoScroll');
const resizer = document.getElementById('resizer');
const logsPanel = document.getElementById('logsPanel');
const chatPanel = document.querySelector('.chat-panel');
const resourceIdModal = document.getElementById('resourceIdModal');
const resourceIdInput = document.getElementById('resourceIdInput');
const modalConfirmBtn = document.getElementById('modalConfirmBtn');
const modalError = document.getElementById('modalError');

// 상태
let isConnected = false;
let isProcessing = false;
let logPollingInterval = null;
let abortController = null;
let currentReader = null;

// 초기화
document.addEventListener('DOMContentLoaded', () => {
    setupResourceIdModal();
    initializeLogs();
    setupEventListeners();
    setupResizer();
    checkConnection();
});

// 이벤트 리스너 설정
function setupEventListeners() {
    sendButton.addEventListener('click', sendMessage);
    stopButton.addEventListener('click', stopResponse);
    messageInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
        }
    });
    
    clearLogsBtn.addEventListener('click', clearLogs);
    toggleAutoScrollBtn.addEventListener('click', toggleAutoScroll);
}

// 리사이저 설정
function setupResizer() {
    if (!resizer || !logsPanel || !chatPanel) return;
    
    let isResizing = false;
    let startX = 0;
    let startWidth = 0;
    
    resizer.addEventListener('mousedown', (e) => {
        isResizing = true;
        startX = e.clientX;
        startWidth = logsPanel.offsetWidth;
        resizer.classList.add('resizing');
        document.body.style.cursor = 'col-resize';
        document.body.style.userSelect = 'none';
        
        e.preventDefault();
    });
    
    document.addEventListener('mousemove', (e) => {
        if (!isResizing) return;
        
        const diff = startX - e.clientX; // 오른쪽으로 드래그하면 양수
        const newWidth = startWidth + diff;
        
        // 최소/최대 너비 제한
        const minWidth = 300;
        const maxWidth = window.innerWidth * 0.8;
        
        if (newWidth >= minWidth && newWidth <= maxWidth) {
            logsPanel.style.width = `${newWidth}px`;
        }
        
        e.preventDefault();
    });
    
    document.addEventListener('mouseup', () => {
        if (isResizing) {
            isResizing = false;
            resizer.classList.remove('resizing');
            document.body.style.cursor = '';
            document.body.style.userSelect = '';
            
            // 로컬 스토리지에 너비 저장
            localStorage.setItem('logsPanelWidth', logsPanel.style.width);
        }
    });
    
    // 저장된 너비 복원
    const savedWidth = localStorage.getItem('logsPanelWidth');
    if (savedWidth) {
        logsPanel.style.width = savedWidth;
    }
}

// 채팅 초기화
// Resource ID 모달 설정
function setupResourceIdModal() {
    if (!resourceIdModal || !resourceIdInput || !modalConfirmBtn) return;
    
    // 입력값 변경 시 확인 버튼 활성화/비활성화
    resourceIdInput.addEventListener('input', (e) => {
        const value = e.target.value.trim();
        if (value.length > 0) {
            modalConfirmBtn.disabled = false;
            modalError.classList.remove('show');
            modalError.textContent = '';
        } else {
            modalConfirmBtn.disabled = true;
        }
    });
    
    // Enter 키로 확인
    resourceIdInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter' && !modalConfirmBtn.disabled) {
            handleResourceIdConfirm();
        }
    });
    
    // 확인 버튼 클릭
    modalConfirmBtn.addEventListener('click', handleResourceIdConfirm);
    
    // 모달 외부 클릭 방지 (모달이 닫히지 않도록)
    resourceIdModal.addEventListener('click', (e) => {
        if (e.target === resourceIdModal) {
            // 모달 외부 클릭 시 아무 동작도 하지 않음
            e.stopPropagation();
        }
    });
}

// Resource ID 확인 처리
async function handleResourceIdConfirm() {
    const resourceId = resourceIdInput.value.trim();
    
    if (!resourceId) {
        modalError.textContent = 'Resource ID를 입력해주세요.';
        modalError.classList.add('show');
        resourceIdInput.focus();
        return;
    }
    
    // 입력 필드와 버튼 비활성화
    resourceIdInput.disabled = true;
    modalConfirmBtn.disabled = true;
    modalConfirmBtn.textContent = '연결 중...';
    modalError.classList.remove('show');
    
    CONFIG.resourceId = resourceId;
    
    // 세션 생성
    try {
        const response = await fetch(`${CONFIG.apiUrl}/api/session`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                projectId: CONFIG.projectId,
                location: CONFIG.location,
                resourceId: CONFIG.resourceId,
                userId: CONFIG.userId,
            }),
        });
        
        if (!response.ok) {
            throw new Error('세션 생성 실패');
        }
        
        const data = await response.json();
        CONFIG.sessionId = data.sessionId;
        addLog('success', `세션 생성 완료: ${CONFIG.sessionId}`);
        updateConnectionStatus(true);
        
        // 모달 숨기기
        resourceIdModal.style.display = 'none';
        initializeChat();
    } catch (error) {
        addLog('error', `세션 생성 실패: ${error.message}`);
        updateConnectionStatus(false);
        
        // 에러 표시 및 재시도 가능하도록 활성화
        modalError.textContent = `세션 생성 실패: ${error.message}`;
        modalError.classList.add('show');
        resourceIdInput.disabled = false;
        modalConfirmBtn.disabled = false;
        modalConfirmBtn.textContent = '확인';
        resourceIdInput.focus();
    }
}

// 채팅 초기화 (Resource ID 입력 후)
function initializeChat() {
    // 채팅 관련 초기화 로직이 필요하면 여기에 추가
}

// 로그 초기화
function initializeLogs() {
    addLog('info', 'Travel Concierge 로그 모니터링 시작');
    startLogPolling();
}

// 연결 상태 확인
async function checkConnection() {
    try {
        const response = await fetch(`${CONFIG.apiUrl}/api/health`);
        if (response.ok) {
            updateConnectionStatus(true);
        } else {
            updateConnectionStatus(false);
        }
    } catch (error) {
        updateConnectionStatus(false);
    }
}

// 연결 상태 업데이트
function updateConnectionStatus(connected) {
    isConnected = connected;
    const statusDot = connectionStatus.querySelector('.status-dot');
    if (connected) {
        statusDot.classList.add('connected');
        statusText.textContent = '연결됨';
    } else {
        statusDot.classList.remove('connected');
        statusText.textContent = '연결 끊김';
    }
}

// 응답 중지
async function stopResponse() {
    if (!isProcessing) return;
    
    addLog('info', '응답 중지 요청');
    
    // AbortController로 요청 취소
    if (abortController) {
        abortController.abort();
    }
    
    // Reader 정리
    if (currentReader) {
        try {
            await currentReader.cancel();
        } catch (e) {
            // 이미 취소되었을 수 있음
        }
        currentReader = null;
    }
    
    // 상태 정리
    isProcessing = false;
    sendButton.disabled = false;
    messageInput.disabled = false;
    stopButton.style.display = 'none';
    sendButton.style.display = 'flex';
    messageInput.focus();
    
    addLog('warning', '응답이 중지되었습니다.');
}

// 메시지 전송
async function sendMessage() {
    const message = messageInput.value.trim();
    if (!message || isProcessing) return;
    
    if (!isConnected || !CONFIG.sessionId) {
        addLog('error', '연결되지 않았습니다. 세션을 확인하세요.');
        return;
    }
    
    // 사용자 메시지 표시
    addMessage('user', message);
    messageInput.value = '';
    isProcessing = true;
    sendButton.disabled = true;
    sendButton.style.display = 'none';
    stopButton.style.display = 'flex';
    messageInput.disabled = true;
    
    // AbortController 생성
    abortController = new AbortController();
    
    // 처리 중 표시 (점점점 애니메이션)
    const thinkingId = addMessage('assistant', '응답 준비 중', 'thinking');
    startThinkingAnimation(thinkingId);
    
    try {
        addLog('info', `메시지 전송: ${message}`);
        
        const response = await fetch(`${CONFIG.apiUrl}/api/chat`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                projectId: CONFIG.projectId,
                location: CONFIG.location,
                resourceId: CONFIG.resourceId,
                userId: CONFIG.userId,
                sessionId: CONFIG.sessionId,
                message: message,
            }),
            signal: abortController.signal,
        });
        
        if (!response.ok) {
            throw new Error(`서버 오류: ${response.status}`);
        }
        
        // 스트리밍 응답 처리
        const reader = response.body.getReader();
        currentReader = reader;
        const decoder = new TextDecoder();
        let buffer = '';
        
        let assistantMessageId = null;
        let fullResponse = '';
        let hasContent = false;
        let thinkingRemoved = false;
        
        while (true) {
            // 중지 요청 확인
            if (abortController.signal.aborted) {
                break;
            }
            
            const { done, value } = await reader.read();
            if (done) break;
            
            buffer += decoder.decode(value, { stream: true });
            const lines = buffer.split('\n');
            buffer = lines.pop() || '';
            
            for (const line of lines) {
                if (line.trim() === '') continue;
                
                if (line.startsWith('data: ')) {
                    try {
                        const jsonStr = line.slice(6).trim();
                        if (!jsonStr) continue;
                        
                        const data = JSON.parse(jsonStr);
                        
                        // 디버깅: 콘솔에 출력
                        console.log('Received event:', data);
                        
                        if (data.type === 'content' && data.content) {
                            hasContent = true;
                            // 첫 번째 콘텐츠가 오면 thinking 메시지 제거
                            if (!thinkingRemoved) {
                                stopThinkingAnimation(thinkingId);
                                removeMessage(thinkingId);
                                thinkingRemoved = true;
                            }
                            if (!assistantMessageId) {
                                assistantMessageId = addMessage('assistant', '');
                                fullResponse = '';
                            }
                            // 모든 이벤트의 텍스트를 누적 (공백으로 구분하여 자연스럽게 연결)
                            if (fullResponse && !fullResponse.endsWith('\n') && !fullResponse.endsWith(' ') && 
                                !data.content.startsWith('\n') && !data.content.startsWith(' ')) {
                                // 이전 텍스트가 문장으로 끝나면 공백 추가, 아니면 줄바꿈
                                if (fullResponse.match(/[.!?]$/)) {
                                    fullResponse += ' ';
                                } else {
                                    fullResponse += '\n';
                                }
                            }
                            fullResponse += data.content;
                            updateMessage(assistantMessageId, fullResponse);
                        } else if (data.type === 'tool_call') {
                            addLog('info', `🔧 Tool 호출: ${data.tool_name || 'unknown'}`);
                        } else if (data.type === 'tool_response') {
                            addLog('debug', `✅ Tool 응답: ${data.tool_name || 'unknown'}`);
                            
                            // Tool 응답에 콘텐츠가 포함된 경우 (서버에서 포맷된 경우)
                            // 이미 content 타입으로 전송되므로 여기서는 로그만 남김
                        } else if (data.type === 'debug') {
                            // 디버그 메시지를 로그에 표시
                            addLog('debug', `🔍 ${data.message}`);
                        } else if (data.type === 'error') {
                            addLog('error', `❌ 오류: ${data.message}`);
                            if (data.traceback) {
                                console.error('Server traceback:', data.traceback);
                                addLog('error', `상세: ${data.traceback.split('\n')[0]}`);
                            }
                        } else if (data.type === 'done') {
                            // 완료 신호
                            if (data.content_received === false) {
                                addLog('warning', '⚠️ Agent Engine에서 콘텐츠를 받지 못했습니다.');
                            } else {
                                addLog('success', '✅ Agent Engine 응답 완료');
                            }
                        }
                    } catch (e) {
                        console.error('JSON 파싱 오류:', e, 'Line:', line);
                        addLog('error', `응답 파싱 오류: ${e.message}`);
                    }
                }
            }
        }
        
        // 응답이 없으면 메시지 표시
        if (!hasContent && !assistantMessageId) {
            if (!thinkingRemoved) {
                stopThinkingAnimation(thinkingId);
                removeMessage(thinkingId);
            }
            // 중지된 경우가 아니면 에러 메시지 표시
            if (!abortController.signal.aborted) {
                assistantMessageId = addMessage('assistant', '응답을 받지 못했습니다. 다시 시도해주세요.');
                addLog('warning', '응답 내용이 없습니다.');
            }
        } else if (hasContent) {
            addLog('success', '응답 수신 완료');
        }
        
    } catch (error) {
        // AbortError는 정상적인 중지이므로 에러로 표시하지 않음
        if (error.name === 'AbortError') {
            addLog('info', '응답이 중지되었습니다.');
            stopThinkingAnimation(thinkingId);
            if (!thinkingRemoved) {
                removeMessage(thinkingId);
            }
            // 중지 메시지 추가
            if (!assistantMessageId) {
                addMessage('assistant', '응답이 중지되었습니다.');
            }
        } else {
            addLog('error', `메시지 전송 실패: ${error.message}`);
            stopThinkingAnimation(thinkingId);
            removeMessage(thinkingId);
            addMessage('assistant', '죄송합니다. 오류가 발생했습니다. 다시 시도해주세요.');
        }
    } finally {
        isProcessing = false;
        sendButton.disabled = false;
        sendButton.style.display = 'flex';
        stopButton.style.display = 'none';
        messageInput.disabled = false;
        messageInput.focus();
        
        // 정리
        abortController = null;
        currentReader = null;
    }
}

// 간단한 마크다운 파싱 (XSS 방지)
function parseMarkdown(text) {
    if (!text) return '';
    
    // **text** -> <strong>text</strong>
    let html = text.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>');
    
    // 줄바꿈 처리
    html = html.replace(/\n/g, '<br>');
    
    return html;
}

// 메시지 추가
function addMessage(role, content, className = '') {
    const messageDiv = document.createElement('div');
    const messageId = Date.now().toString() + '-' + Math.random().toString(36).substr(2, 9);
    messageDiv.className = `message ${role} ${className}`;
    messageDiv.dataset.messageId = messageId;
    
    const contentDiv = document.createElement('div');
    contentDiv.className = 'message-content';
    // 마크다운 파싱하여 HTML로 표시
    contentDiv.innerHTML = parseMarkdown(content);
    
    const timeDiv = document.createElement('div');
    timeDiv.className = 'message-time';
    timeDiv.textContent = new Date().toLocaleTimeString('ko-KR');
    
    messageDiv.appendChild(contentDiv);
    messageDiv.appendChild(timeDiv);
    chatMessages.appendChild(messageDiv);
    
    scrollChatToBottom();
    return messageId;
}

// Thinking 애니메이션 시작
function startThinkingAnimation(messageId) {
    const messageDiv = document.querySelector(`[data-message-id="${messageId}"]`);
    if (!messageDiv) return;
    
    const contentDiv = messageDiv.querySelector('.message-content');
    if (!contentDiv) return;
    
    // 점점점 애니메이션을 위한 span 추가
    const dotsSpan = document.createElement('span');
    dotsSpan.className = 'thinking-dots';
    dotsSpan.textContent = '...';
    contentDiv.appendChild(dotsSpan);
    
    // 애니메이션 인터벌 저장
    messageDiv.dataset.animationInterval = setInterval(() => {
        const dots = dotsSpan.textContent;
        if (dots === '...') {
            dotsSpan.textContent = '.';
        } else if (dots === '.') {
            dotsSpan.textContent = '..';
        } else if (dots === '..') {
            dotsSpan.textContent = '...';
        }
    }, 500);
}

// Thinking 애니메이션 중지
function stopThinkingAnimation(messageId) {
    const messageDiv = document.querySelector(`[data-message-id="${messageId}"]`);
    if (!messageDiv) return;
    
    const intervalId = messageDiv.dataset.animationInterval;
    if (intervalId) {
        clearInterval(intervalId);
        delete messageDiv.dataset.animationInterval;
    }
}

// 메시지 업데이트
function updateMessage(messageId, content) {
    const messageDiv = document.querySelector(`[data-message-id="${messageId}"]`);
    if (messageDiv) {
        const contentDiv = messageDiv.querySelector('.message-content');
        if (contentDiv) {
            // 마크다운 파싱하여 HTML로 표시
            contentDiv.innerHTML = parseMarkdown(content);
            scrollChatToBottom();
        }
    }
}

// 메시지 제거
function removeMessage(messageId) {
    const messageDiv = document.querySelector(`[data-message-id="${messageId}"]`);
    if (messageDiv) {
        messageDiv.remove();
    }
}

// 채팅 스크롤
function scrollChatToBottom() {
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

// 로그 추가
function addLog(level, message) {
    const logEntry = document.createElement('div');
    logEntry.className = `log-entry ${level}`;
    
    const timeSpan = document.createElement('span');
    timeSpan.className = 'log-time';
    timeSpan.textContent = new Date().toLocaleTimeString('ko-KR');
    
    const levelSpan = document.createElement('span');
    levelSpan.className = 'log-level';
    levelSpan.textContent = level.toUpperCase();
    
    const messageSpan = document.createElement('span');
    messageSpan.className = 'log-message';
    messageSpan.textContent = message;
    
    logEntry.appendChild(timeSpan);
    logEntry.appendChild(levelSpan);
    logEntry.appendChild(messageSpan);
    
    logsContent.appendChild(logEntry);
    
    if (CONFIG.autoScroll) {
        scrollLogsToBottom();
    }
}

// 로그 스크롤
function scrollLogsToBottom() {
    logsContent.scrollTop = logsContent.scrollHeight;
}

// 로그 지우기
function clearLogs() {
    logsContent.innerHTML = '';
    addLog('info', '로그가 지워졌습니다.');
}

// 자동 스크롤 토글
function toggleAutoScroll() {
    CONFIG.autoScroll = !CONFIG.autoScroll;
    toggleAutoScrollBtn.classList.toggle('active', CONFIG.autoScroll);
    if (CONFIG.autoScroll) {
        scrollLogsToBottom();
    }
}

// 로그 폴링 시작
let lastLogTimestamp = null;
function startLogPolling() {
    if (logPollingInterval) {
        clearInterval(logPollingInterval);
    }
    
    logPollingInterval = setInterval(async () => {
        if (!CONFIG.resourceId) return;
        
        try {
            const response = await fetch(
                `${CONFIG.apiUrl}/api/logs?projectId=${CONFIG.projectId}&resourceId=${CONFIG.resourceId}&limit=20&minutes=5`
            );
            
            if (response.ok) {
                const logs = await response.json();
                
                // 새로운 로그만 추가 (타임스탬프 기준)
                logs.forEach(log => {
                    if (!log.message || !log.timestamp) return;
                    
                    // 타임스탬프로 중복 체크
                    if (lastLogTimestamp && log.timestamp <= lastLogTimestamp) {
                        return;
                    }
                    
                    // 기존 로그와 중복 체크
                    const existingLogs = Array.from(logsContent.querySelectorAll('.log-message'));
                    const isDuplicate = existingLogs.some(el => {
                        const logText = el.textContent;
                        return logText.includes(log.message.substring(0, 50));
                    });
                    
                    if (!isDuplicate) {
                        // GCP 로그는 특별한 형식으로 표시
                        const logMessage = log.resource_type 
                            ? `[GCP ${log.resource_type}] ${log.message}`
                            : `[GCP] ${log.message}`;
                        addLog(log.level || 'info', logMessage);
                        
                        // 마지막 타임스탬프 업데이트
                        if (!lastLogTimestamp || log.timestamp > lastLogTimestamp) {
                            lastLogTimestamp = log.timestamp;
                        }
                    }
                });
            }
        } catch (error) {
            // 폴링 오류는 조용히 처리 (너무 자주 표시하지 않음)
            console.error('로그 폴링 오류:', error);
        }
    }, CONFIG.logPollInterval);
}
