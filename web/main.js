// 使用相对路径，自动适配当前域名和端口
const API_URL = window.location.origin + '/';
const chatContainer = document.getElementById('chatContainer');
const messageInput = document.getElementById('messageInput');
const sendBtn = document.getElementById('sendBtn');
const emptyState = document.getElementById('emptyState');
const historyContainer = document.getElementById('historyContainer');
const historyEmpty = document.getElementById('historyEmpty');
const historySearchInput = document.getElementById('historySearchInput');

// 聊天历史
let chatHistory = [];

// 当前选中的会话ID
let currentSessionId = null;
let filteredSessions = [];
let allSessions = [];

// 当前使用的会话ID（用于发送请求）
let activeSessionId = null;

// 从Redis加载对话历史列表
async function loadHistory() {
    try {
        const response = await fetch(API_URL + 'api/sessions');
        const data = await response.json();

        if (data.status === 200) {
            allSessions = data.sessions || [];
            renderHistory();
        } else {
            console.error('加载对话历史失败:', data.error);
            historyEmpty.style.display = 'block';
        }
    } catch (error) {
        console.error('加载对话历史失败:', error);
        historyEmpty.style.display = 'block';
    }
}

// 渲染对话历史
function renderHistory() {
    const sessionsToRender = filteredSessions.length > 0 ? filteredSessions : allSessions;

    console.log('渲染历史记录，数量:', sessionsToRender.length);

    if (sessionsToRender.length === 0) {
        historyEmpty.style.display = 'block';
        historyContainer.innerHTML = '';
        return;
    }

    historyEmpty.style.display = 'none';
    historyContainer.innerHTML = '';

    // 会话列表已经按时间倒序排列（从后端返回）
    sessionsToRender.forEach(session => {
        const historyItem = document.createElement('div');
        historyItem.className = 'history-item';
        // 确保使用严格相等比较，并且两个值都不为 null/undefined
        // 转换为字符串进行比较，确保类型一致
        const sessionId = String(session.session_id || '');
        const currentId = String(currentSessionId || '');
        if (sessionId && currentId && sessionId === currentId) {
            historyItem.classList.add('active');
        }

        // 格式化时间
        let timeStr = '';
        try {
            const time = new Date(session.update_time);
            timeStr = time.toLocaleString('zh-CN', {
                month: '2-digit',
                day: '2-digit',
                hour: '2-digit',
                minute: '2-digit'
            });
        } catch (e) {
            timeStr = session.update_time || '';
        }

        historyItem.innerHTML = `
            <div class="history-item-header">
                <div class="history-item-time">${timeStr}</div>
            </div>
            <div class="history-item-question">${escapeHtml(session.title || '新对话')}</div>
            <div class="history-item-answer">共 ${session.message_count || 0} 条对话</div>
        `;

        historyItem.onclick = () => loadHistoryItem(session.session_id);
        historyContainer.appendChild(historyItem);
    });
}

// 加载历史对话项
async function loadHistoryItem(sessionId) {
    try {
        const response = await fetch(API_URL + `api/sessions/${sessionId}`);
        const data = await response.json();

        if (data.status !== 200 || !data.conversations) {
            console.error('加载会话详情失败:', data.error);
            return;
        }

        // 确保 sessionId 是字符串类型，并设置为当前选中的会话ID
        const sessionIdStr = String(sessionId || '');
        currentSessionId = sessionIdStr; // 用于UI高亮显示
        // 注意：加载历史对话时，不自动设置 activeSessionId
        // 只有当用户在该历史对话中发送新消息时，才设置 activeSessionId
        // 这样避免创建新会话后，选择历史对话会覆盖新的 session_id

        renderHistory();

        // 清空当前聊天
        chatContainer.innerHTML = '';
        chatHistory = [];
        emptyState.style.display = 'none';

        // 重新渲染对话
        data.conversations.forEach(conv => {
            addQuestion(conv.question);
            addAnswer(conv.answer, null, null);
        });

        // 检查消息数量，如果达到10条，在输入框显示提示
        const messageCount = data.count || data.conversations.length;
        if (messageCount >= 10) {
            messageInput.placeholder = '该对话已达到10条消息上限，请创建新会话';
            messageInput.style.borderColor = 'var(--warning-color)';
        } else {
            messageInput.placeholder = '例如：感冒了有什么症状？应该怎么治疗？';
            messageInput.style.borderColor = '';
        }

        scrollToBottom();
    } catch (error) {
        console.error('加载会话详情失败:', error);
    }
}

// 刷新对话历史列表（对话已由后端自动保存到Redis）
function refreshHistory() {
    loadHistory();
}

// 创建新会话
async function createNewSession() {
    try {
        const oldSessionId = activeSessionId;
        const response = await fetch(API_URL + 'api/new_session', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                old_session_id: oldSessionId
            })
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const data = await response.json();

        if (data.status === 200 && data.session_id) {
            // 确保使用新的 session_id，并立即更新
            const newSessionId = String(data.session_id);
            activeSessionId = newSessionId;
            localStorage.setItem('currentSessionId', newSessionId);

            // 清空当前聊天
            chatContainer.innerHTML = '';
            chatHistory = [];
            currentSessionId = null; // 清除历史对话选中状态
            emptyState.style.display = 'block';

            // 重置输入框样式和提示
            messageInput.placeholder = '例如：感冒了有什么症状？应该怎么治疗？';
            messageInput.style.borderColor = '';

            // 刷新历史列表
            refreshHistory();

            console.log('新会话创建成功:', newSessionId);
            console.log('当前 activeSessionId:', activeSessionId);
        } else {
            console.error('创建新会话失败:', data);
        }
    } catch (error) {
        console.error('创建新会话失败:', error);
        alert('创建新会话失败，请稍后重试');
    }
}

// 过滤对话历史
function filterHistory() {
    const searchTerm = historySearchInput.value.trim().toLowerCase();

    if (!searchTerm) {
        filteredSessions = [];
        renderHistory();
        return;
    }

    filteredSessions = allSessions.filter(session => {
        return session.title.toLowerCase().includes(searchTerm);
    });

    renderHistory();
}

// 清空对话历史（仅清空前端显示，实际数据在Redis中）
function clearHistory() {
    if (confirm('确定要清空对话历史显示吗？实际数据仍保存在服务器中。')) {
        allSessions = [];
        filteredSessions = [];
        currentSessionId = null;
        renderHistory();
    }
}

// 导出对话历史
async function exportHistory() {
    if (allSessions.length === 0) {
        alert('暂无对话历史可导出');
        return;
    }

    try {
        // 获取所有会话的详细对话记录
        const exportData = [];
        for (const session of allSessions) {
            const response = await fetch(API_URL + `api/sessions/${session.session_id}`);
            const data = await response.json();
            if (data.status === 200) {
                exportData.push({
                    session_id: session.session_id,
                    title: session.title,
                    update_time: session.update_time,
                    message_count: session.message_count,
                    conversations: data.conversations
                });
            }
        }

        const dataStr = JSON.stringify(exportData, null, 2);
        const dataBlob = new Blob([dataStr], { type: 'application/json' });
        const url = URL.createObjectURL(dataBlob);
        const link = document.createElement('a');
        link.href = url;
        link.download = `conversation_history_${new Date().toISOString().split('T')[0]}.json`;
        link.click();
        URL.revokeObjectURL(url);
    } catch (error) {
        console.error('导出对话历史失败:', error);
        alert('导出失败，请稍后重试');
    }
}

// HTML转义
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// 滚动到聊天容器底部
function scrollToBottom(smooth = false) {
    if (!chatContainer) return;

    const scroll = () => {
        const maxScroll = chatContainer.scrollHeight - chatContainer.clientHeight;
        if (smooth) {
            chatContainer.scrollTo({
                top: chatContainer.scrollHeight,
                behavior: 'smooth'
            });
        } else {
            // 直接设置，立即滚动
            chatContainer.scrollTop = chatContainer.scrollHeight;
        }
    };

    // 使用 requestAnimationFrame 确保在下一帧渲染后执行
    requestAnimationFrame(() => {
        scroll();

        // 延迟再次检查，因为内容可能还在动态加载（如图片、图谱等）
        setTimeout(() => {
            scroll();
        }, 150);

        // 再次延迟检查，确保所有异步内容都加载完成
        setTimeout(() => {
            scroll();
        }, 500);
    });
}

// 简单的关键词提取
function extractKeywords(text) {
    // 这里实现简单的关键词提取，实际项目中可以使用更复杂的算法
    const stopWords = ['的', '了', '是', '在', '有', '和', '就', '不', '人', '都', '一', '一个', '上', '也', '很', '到', '说', '要', '去', '你', '会', '着', '没有', '看', '好', '自己', '这'];
    return text.split(/[\s,，.。、；;！!?？]+/)
        .filter(word => word.length > 1 && !stopWords.includes(word))
        .slice(0, 10); // 最多提取10个关键词
}

// 设置示例问题
function setExample(text) {
    messageInput.value = text;
    messageInput.focus();
}

// 处理回车键
function handleKeyPress(event) {
    if (event.key === 'Enter' && !event.shiftKey) {
        event.preventDefault();
        sendMessage();
    }
}

// 获取状态显示文本
function getStatusText(status) {
    const statusMap = {
        success: '成功',
        pending: '进行中',
        error: '失败',
        empty: '无结果',
        skipped: '跳过'
    };
    return statusMap[status] || status;
}

// 创建搜索路径展示
function createSearchPath(searchStages, searchPath) {
    const pathDiv = document.createElement('div');
    pathDiv.className = 'search-path';

    const titleDiv = document.createElement('div');
    titleDiv.className = 'search-path-title';
    titleDiv.textContent = '搜索路径与结果';
    pathDiv.appendChild(titleDiv);

    const stagesDiv = document.createElement('div');
    stagesDiv.className = 'search-stages';

    // 按顺序展示各个阶段
    const stageOrder = ['milvus_vector', 'knowledge_graph'];
    const stageNames = {
        milvus_vector: '向量数据库检索',
        knowledge_graph: '知识图谱查询'
    };

    stageOrder.forEach(stageKey => {
        const stage = searchStages[stageKey];
        if (!stage) return;

        const stageDiv = document.createElement('div');
        stageDiv.className = 'search-stage';

        const headerDiv = document.createElement('div');
        headerDiv.className = 'stage-header';

        const nameDiv = document.createElement('div');
        nameDiv.className = 'stage-name';
        nameDiv.textContent = stageNames[stageKey] || stage.description || stageKey;

        const statusDiv = document.createElement('div');
        statusDiv.className = `stage-status status-${stage.status}`;
        statusDiv.textContent = getStatusText(stage.status);

        headerDiv.appendChild(nameDiv);
        headerDiv.appendChild(statusDiv);
        stageDiv.appendChild(headerDiv);

        // 如果是知识图谱查询且状态为进行中，显示不同阶段的等待提示
        if (stageKey === 'knowledge_graph' && stage.status === 'pending') {
            const waitingDiv = document.createElement('div');
            waitingDiv.className = 'stage-info';
            waitingDiv.style.color = 'var(--warning-color)';
            waitingDiv.style.fontStyle = 'italic';
            waitingDiv.style.marginTop = '8px';

            // 根据 stage_detail 显示不同的提示信息
            const stageDetail = stage.stage_detail || 'generating';
            let message = '';
            switch (stageDetail) {
                case 'generating':
                    message = '⏳ 正在调用大模型生成 Cypher 查询语句，请稍候...';
                    break;
                case 'validating':
                    message = '✅ Cypher 查询已生成，正在验证查询语句的有效性...';
                    break;
                case 'executing':
                    message = '✅ 查询验证通过，正在执行查询并获取结果...';
                    break;
                default:
                    message = '⏳ 正在处理知识图谱查询，请稍候...';
            }
            waitingDiv.innerHTML = message;
            stageDiv.appendChild(waitingDiv);
        }

        // 显示数量信息
        if (stage.count !== undefined) {
            const infoDiv = document.createElement('div');
            infoDiv.className = 'stage-info';
            infoDiv.textContent = `检索到 ${stage.count} 条结果`;
            stageDiv.appendChild(infoDiv);
        }

        // 显示置信度（知识图谱）
        if (stage.confidence !== undefined && stage.confidence > 0) {
            const confDiv = document.createElement('div');
            confDiv.className = 'stage-info';
            confDiv.innerHTML = `置信度: <span class="confidence-badge">${(stage.confidence * 100).toFixed(1)}%</span>`;
            stageDiv.appendChild(confDiv);
        }

        // 显示Cypher查询（知识图谱）
        if (stage.cypher_query) {
            const cypherDiv = document.createElement('div');
            cypherDiv.className = 'cypher-query';
            cypherDiv.textContent = stage.cypher_query;
            stageDiv.appendChild(cypherDiv);
        }

        // 显示错误信息
        if (stage.error) {
            const errorDiv = document.createElement('div');
            errorDiv.className = 'result-item';
            errorDiv.style.borderLeftColor = '#ef4444';
            errorDiv.textContent = `错误: ${stage.error}`;
            stageDiv.appendChild(errorDiv);
        }

        // 显示结果
        if (stage.results && stage.results.length > 0) {
            const resultsDiv = document.createElement('div');
            resultsDiv.className = 'stage-results';
            stage.results.forEach(result => {
                const resultDiv = document.createElement('div');
                resultDiv.className = 'result-item';
                resultDiv.textContent = result;
                resultsDiv.appendChild(resultDiv);
            });
            stageDiv.appendChild(resultsDiv);
        }

        stagesDiv.appendChild(stageDiv);
    });

    pathDiv.appendChild(stagesDiv);
    return pathDiv;
}

// 创建最终结果展示
function createFinalResult(response) {
    const resultDiv = document.createElement('div');
    resultDiv.className = 'final-result';

    const titleDiv = document.createElement('div');
    titleDiv.className = 'final-result-title';
    titleDiv.textContent = '最终回答';
    resultDiv.appendChild(titleDiv);

    const contentDiv = document.createElement('div');
    contentDiv.className = 'final-result-content';
    contentDiv.textContent = response;
    resultDiv.appendChild(contentDiv);

    return resultDiv;
}

// 添加问题到界面
function addQuestion(text) {
    if (emptyState) {
        emptyState.style.display = 'none';
    }

    const qaItem = document.createElement('div');
    qaItem.className = 'qa-item';

    const questionCard = document.createElement('div');
    questionCard.className = 'question-card';

    const questionLabel = document.createElement('div');
    questionLabel.className = 'question-label';
    questionLabel.textContent = '问题';

    const questionText = document.createElement('div');
    questionText.className = 'question-text';
    questionText.textContent = text;

    questionCard.appendChild(questionLabel);
    questionCard.appendChild(questionText);
    qaItem.appendChild(questionCard);

    chatContainer.appendChild(qaItem);

    // 滚动到底部
    scrollToBottom();

    return qaItem;
}

// 添加答案到界面
function addAnswer(text, searchStages = null, searchPath = null, qaItem = null) {
    if (!qaItem) {
        // 如果没有提供qaItem，创建新的
        qaItem = document.createElement('div');
        qaItem.className = 'qa-item';
        chatContainer.appendChild(qaItem);
    }

    const answerCard = document.createElement('div');
    answerCard.className = 'answer-card';

    const answerLabel = document.createElement('div');
    answerLabel.className = 'answer-label';
    answerLabel.textContent = '回答';
    answerCard.appendChild(answerLabel);

    // 如果是机器人消息且有搜索信息，展示搜索路径和最终结果
    if (searchStages && searchPath) {
        const searchPathDiv = createSearchPath(searchStages, searchPath);
        answerCard.appendChild(searchPathDiv);

        const finalResultDiv = createFinalResult(text);
        answerCard.appendChild(finalResultDiv);
    } else {
        const answerText = document.createElement('div');
        answerText.className = 'final-result-content';
        answerText.textContent = text;
        answerCard.appendChild(answerText);
    }

    qaItem.appendChild(answerCard);

    // 滚动到底部
    scrollToBottom();

    return qaItem;
}

// 显示加载状态
function showLoading() {
    const loadingItem = document.createElement('div');
    loadingItem.className = 'qa-item';
    loadingItem.id = 'loadingMessage';

    const answerCard = document.createElement('div');
    answerCard.className = 'answer-card';

    const answerLabel = document.createElement('div');
    answerLabel.className = 'answer-label';
    answerLabel.textContent = '回答';
    answerCard.appendChild(answerLabel);

    const loadingDiv = document.createElement('div');
    loadingDiv.className = 'loading';
    loadingDiv.innerHTML = `
        <span>正在思考</span>
        <div class="loading-dots">
            <span></span>
            <span></span>
            <span></span>
        </div>
    `;

    answerCard.appendChild(loadingDiv);
    loadingItem.appendChild(answerCard);
    chatContainer.appendChild(loadingItem);
    scrollToBottom();
}

// 移除加载状态
function removeLoading() {
    const loadingMsg = document.getElementById('loadingMessage');
    if (loadingMsg) {
        loadingMsg.remove();
    }
}

// 发送消息（流式版本）
async function sendMessage() {
    const message = messageInput.value.trim();
    if (!message) {
        return;
    }

    // 如果当前有选中的历史对话（currentSessionId 不为空），使用历史对话的 session_id
    // 否则使用 activeSessionId（可能是新创建的会话）
    if (currentSessionId) {
        // 用户选择了历史对话，使用历史对话的 session_id
        activeSessionId = String(currentSessionId);
        localStorage.setItem('currentSessionId', activeSessionId);

        // 检查消息数量
        try {
            const response = await fetch(API_URL + `api/sessions/${activeSessionId}`);
            const data = await response.json();

            if (data.status === 200) {
                const messageCount = data.count || (data.conversations ? data.conversations.length : 0);
                if (messageCount >= 10) {
                    // 已达到10条，显示提示并阻止发送
                    messageInput.value = '';
                    messageInput.placeholder = '该对话已达到10条消息上限，请创建新会话';
                    messageInput.style.borderColor = 'var(--warning-color)';
                    alert('该对话已达到10条消息上限，请创建新会话后再继续提问');
                    return;
                }
            }
        } catch (error) {
            console.error('检查会话消息数量失败:', error);
        }
    } else {
        // 没有选择历史对话，使用 activeSessionId（可能是新创建的会话）
        // 如果 activeSessionId 为空，后端会生成新的
    }

    // 禁用输入和按钮
    messageInput.disabled = true;
    sendBtn.disabled = true;

    // 添加问题
    const qaItem = addQuestion(message);
    chatHistory.push({ role: 'user', content: message });

    // 清空输入框
    messageInput.value = '';

    // 移除加载状态（如果有）
    removeLoading();

    // 创建答案容器
    const answerCard = document.createElement('div');
    answerCard.className = 'answer-card';

    const answerLabel = document.createElement('div');
    answerLabel.className = 'answer-label';
    answerLabel.textContent = '回答';
    answerCard.appendChild(answerLabel);

    // 创建搜索路径容器（实时更新）
    const searchPathDiv = document.createElement('div');
    searchPathDiv.className = 'search-path';
    searchPathDiv.style.display = 'none'; // 初始隐藏，有数据时显示

    const searchPathTitle = document.createElement('div');
    searchPathTitle.className = 'search-path-title';
    searchPathTitle.textContent = '搜索路径与结果';
    searchPathDiv.appendChild(searchPathTitle);

    const stagesDiv = document.createElement('div');
    stagesDiv.className = 'search-stages';
    searchPathDiv.appendChild(stagesDiv);

    answerCard.appendChild(searchPathDiv);

    // 创建最终回答容器（实时更新）
    const finalResultDiv = document.createElement('div');
    finalResultDiv.className = 'final-result';

    const finalResultTitle = document.createElement('div');
    finalResultTitle.className = 'final-result-title';
    finalResultTitle.textContent = '最终回答';
    finalResultDiv.appendChild(finalResultTitle);

    const finalResultContent = document.createElement('div');
    finalResultContent.className = 'final-result-content';
    finalResultContent.textContent = '';
    finalResultDiv.appendChild(finalResultContent);

    answerCard.appendChild(finalResultDiv);

    // 添加到qaItem
    qaItem.appendChild(answerCard);

    // 初始化搜索阶段状态
    const searchStages = {
        milvus_vector: { status: 'pending', results: [], count: 0, description: '向量数据库检索' },
        knowledge_graph: { status: 'pending', results: [], count: 0, description: '知识图谱查询', cypher_query: '', confidence: 0, stage_detail: 'generating' }
    };

    // 更新搜索阶段显示的函数
    function updateSearchStage(stageKey, stageData) {
        const stageNames = {
            milvus_vector: '向量数据库检索',
            knowledge_graph: '知识图谱查询'
        };

        // 查找或创建阶段元素
        let stageDiv = stagesDiv.querySelector(`[data-stage="${stageKey}"]`);
        if (!stageDiv) {
            stageDiv = document.createElement('div');
            stageDiv.className = 'search-stage';
            stageDiv.setAttribute('data-stage', stageKey);
            stagesDiv.appendChild(stageDiv);
        }

        // 更新内容
        stageDiv.innerHTML = '';

        const headerDiv = document.createElement('div');
        headerDiv.className = 'stage-header';

        const nameDiv = document.createElement('div');
        nameDiv.className = 'stage-name';
        nameDiv.textContent = stageNames[stageKey] || stageData.description || stageKey;

        const statusDiv = document.createElement('div');
        statusDiv.className = `stage-status status-${stageData.status}`;
        statusDiv.textContent = getStatusText(stageData.status);

        headerDiv.appendChild(nameDiv);
        headerDiv.appendChild(statusDiv);
        stageDiv.appendChild(headerDiv);

        // 如果是知识图谱查询且状态为进行中，显示不同阶段的等待提示
        if (stageKey === 'knowledge_graph' && stageData.status === 'pending') {
            // 查找是否已存在等待提示元素，如果存在则先移除
            const existingWaitingDiv = stageDiv.querySelector('.stage-info.waiting-prompt');
            if (existingWaitingDiv) {
                existingWaitingDiv.remove();
            }

            const waitingDiv = document.createElement('div');
            waitingDiv.className = 'stage-info waiting-prompt';
            waitingDiv.style.color = 'var(--warning-color)';
            waitingDiv.style.fontStyle = 'italic';
            waitingDiv.style.marginTop = '8px';

            // 根据 stage_detail 显示不同的提示信息
            // 确保从 stageData 中正确读取 stage_detail
            const stageDetail = stageData.stage_detail || 'generating';
            // 调试日志：确认读取的 stage_detail 值
            console.log('updateSearchStage - stageKey:', stageKey);
            console.log('updateSearchStage - stage_detail 值:', stageDetail);
            console.log('updateSearchStage - 完整的 stageData:', JSON.stringify(stageData, null, 2));
            let message = '';
            switch (stageDetail) {
                case 'generating':
                    message = '⏳ 正在调用大模型生成 Cypher 查询语句，请稍候...';
                    break;
                case 'validating':
                    message = '✅ Cypher 查询已生成，正在验证查询语句的有效性...';
                    break;
                case 'executing':
                    message = '✅ 查询验证通过，正在执行查询并获取结果...';
                    break;
                default:
                    message = '⏳ 正在处理知识图谱查询，请稍候...';
                    console.warn('updateSearchStage - 未知的 stage_detail 值:', stageDetail);
            }
            console.log('updateSearchStage - 显示的消息:', message);
            waitingDiv.innerHTML = message;
            stageDiv.appendChild(waitingDiv);
        }

        // 显示数量信息
        if (stageData.count !== undefined) {
            const infoDiv = document.createElement('div');
            infoDiv.className = 'stage-info';
            infoDiv.textContent = `检索到 ${stageData.count} 条结果`;
            stageDiv.appendChild(infoDiv);
        }

        // 显示置信度
        if (stageData.confidence !== undefined && stageData.confidence > 0) {
            const confDiv = document.createElement('div');
            confDiv.className = 'stage-info';
            confDiv.innerHTML = `置信度: <span class="confidence-badge">${(stageData.confidence * 100).toFixed(1)}%</span>`;
            stageDiv.appendChild(confDiv);
        }

        // 显示Cypher查询
        if (stageData.cypher_query) {
            const cypherDiv = document.createElement('div');
            cypherDiv.className = 'cypher-query';
            cypherDiv.textContent = stageData.cypher_query;
            stageDiv.appendChild(cypherDiv);
        }

        // 显示错误信息
        if (stageData.error) {
            const errorDiv = document.createElement('div');
            errorDiv.className = 'result-item';
            errorDiv.style.borderLeftColor = '#ef4444';
            errorDiv.textContent = `错误: ${stageData.error}`;
            stageDiv.appendChild(errorDiv);
        }

        // 显示结果
        if (stageData.results && stageData.results.length > 0) {
            const resultsDiv = document.createElement('div');
            resultsDiv.className = 'stage-results';
            stageData.results.forEach(result => {
                const resultDiv = document.createElement('div');
                resultDiv.className = 'result-item';
                resultDiv.textContent = result;
                resultsDiv.appendChild(resultDiv);
            });
            stageDiv.appendChild(resultsDiv);
        }

        // 显示搜索路径
        searchPathDiv.style.display = 'block';
        scrollToBottom();
    }

    let fullResponse = '';
    let finalSearchStages = null;
    let finalSearchPath = null;

    // 处理事件的函数（定义在循环外部）
    function processEvent(eventType, data) {
        // 处理会话ID
        if (eventType === 'session_id') {
            activeSessionId = data.session_id;
            // 保存到localStorage以便下次使用
            if (activeSessionId) {
                localStorage.setItem('currentSessionId', activeSessionId);
            }
        }

        // 处理新会话创建
        if (eventType === 'new_session_created') {
            if (data.new_session_id) {
                activeSessionId = data.new_session_id;
                localStorage.setItem('currentSessionId', activeSessionId);
                currentSessionId = null; // 清除当前选中的历史对话
                // 刷新历史列表
                refreshHistory();
                // 重置输入框样式和提示
                messageInput.placeholder = '例如：感冒了有什么症状？应该怎么治疗？';
                messageInput.style.borderColor = '';
                // 提示用户
                console.log('对话达到10条，已自动创建新会话');
            }
        }

        // 处理搜索阶段更新
        if (eventType === 'search_stage') {
            const stageKey = data.stage;
            // 先更新 searchStages 对象
            if (stageKey === 'milvus_vector') {
                searchStages.milvus_vector = {
                    ...searchStages.milvus_vector,
                    ...data
                };
            } else if (stageKey === 'knowledge_graph') {
                // 确保 stage_detail 字段被正确更新
                searchStages.knowledge_graph = {
                    ...searchStages.knowledge_graph,
                    ...data
                };
                // 调试日志：确认 stage_detail 更新
                console.log('知识图谱阶段更新 - 接收到的数据:', data);
                console.log('知识图谱阶段更新 - 更新后的 searchStages:', searchStages.knowledge_graph);
            }
            // 使用合并后的最新数据更新显示（确保包含所有字段，特别是 stage_detail）
            const updatedData = {
                ...searchStages[stageKey],
                ...data // 再次合并 data，确保 stage_detail 等字段优先使用最新值
            };
            // 调试日志：确认传递给 updateSearchStage 的数据
            if (stageKey === 'knowledge_graph') {
                console.log('准备调用 updateSearchStage - updatedData:', updatedData);
                console.log('updatedData.stage_detail:', updatedData.stage_detail);
            }
            updateSearchStage(stageKey, updatedData);
        }

        // 处理回答开始
        if (eventType === 'answer_start') {
            finalResultContent.textContent = '正在生成回答...';
        }

        // 处理回答片段
        if (eventType === 'answer_chunk') {
            fullResponse += data.content || '';
            finalResultContent.textContent = fullResponse;
            scrollToBottom(true);
        }

        // 处理回答完成
        if (eventType === 'answer_complete') {
            fullResponse = data.response || fullResponse;
            finalResultContent.textContent = fullResponse;
            finalSearchStages = data.search_stages || searchStages;
            finalSearchPath = data.search_path || [];

            chatHistory.push({
                role: 'bot',
                content: fullResponse,
                searchStages: finalSearchStages,
                searchPath: finalSearchPath
            });

            // 刷新对话历史列表（对话已由后端自动保存到Redis）
            refreshHistory();
        }

        // 处理错误
        if (eventType === 'answer_error') {
            finalResultContent.textContent = `生成回答失败: ${data.error || '未知错误'}`;
        }
    }

    try {
        // 获取或使用当前会话ID
        // 如果 activeSessionId 为空，从 localStorage 获取
        if (!activeSessionId) {
            activeSessionId = localStorage.getItem('currentSessionId');
        }

        // 确保 session_id 是字符串类型
        const sessionIdToUse = activeSessionId ? String(activeSessionId) : null;

        // 调试日志：记录使用的 session_id
        console.log('发送消息，使用的 session_id:', sessionIdToUse);
        console.log('当前 activeSessionId:', activeSessionId);
        console.log('当前 currentSessionId:', currentSessionId);

        // 发送流式请求
        const response = await fetch(API_URL, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                question: message,
                stream: true,
                session_id: sessionIdToUse // 使用确定的 session_id，如果为 null 后端会生成新的
            }),
        });

        if (!response.ok) {
            throw new Error('服务暂时不可用');
        }

        // 读取流式响应
        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        let buffer = '';
        let currentEventType = '';
        let pendingData = null;

        while (true) {
            const { done, value } = await reader.read();
            if (done) {
                // 处理最后的数据
                if (pendingData && currentEventType) {
                    try {
                        const data = JSON.parse(pendingData);
                        processEvent(currentEventType, data);
                    } catch (e) {
                        console.error('解析SSE数据失败:', e, pendingData);
                    }
                }
                break;
            }

            buffer += decoder.decode(value, { stream: true });
            const lines = buffer.split('\n');
            buffer = lines.pop() || ''; // 保留最后不完整的行

            for (const line of lines) {
                if (line.trim() === '') {
                    // 空行表示事件结束，处理pendingData
                    if (pendingData && currentEventType) {
                        try {
                            const data = JSON.parse(pendingData);
                            // 调试日志：记录接收到的 search_stage 事件
                            if (currentEventType === 'search_stage' && data.stage === 'knowledge_graph') {
                                console.log('接收到 search_stage 事件:', currentEventType, data);
                                console.log('stage_detail 值:', data.stage_detail);
                            }
                            processEvent(currentEventType, data);
                        } catch (e) {
                            console.error('解析SSE数据失败:', e, pendingData);
                        }
                        pendingData = null;
                        currentEventType = '';
                    }
                    continue;
                }

                if (line.startsWith('event: ')) {
                    currentEventType = line.substring(7).trim();
                    continue;
                }

                if (line.startsWith('data: ')) {
                    const dataStr = line.substring(6).trim();
                    if (dataStr) {
                        pendingData = dataStr;
                    }
                    continue;
                }
            }
        }
    } catch (error) {
        console.error('Error:', error);
        finalResultContent.textContent = '网络连接错误，请检查网络连接后重试。';
    } finally {
        // 恢复输入和按钮
        messageInput.disabled = false;
        sendBtn.disabled = false;
        messageInput.focus();
        scrollToBottom();
    }
}

// 清空对话
function clearChat() {
    if (confirm('确定要清空所有对话吗？')) {
        chatContainer.innerHTML = '';
        chatHistory = [];
        // 清空当前选中的会话ID，但不清空 activeSessionId（因为可能还要继续使用）
        currentSessionId = null;
        emptyState.style.display = 'block';

        // 更新历史列表的选中状态（移除所有高亮）
        renderHistory();
    }
}

// 页面加载完成后初始化
window.addEventListener('load', () => {
    messageInput.focus();
    // 从localStorage加载当前会话ID
    activeSessionId = localStorage.getItem('currentSessionId');
    loadHistory();
});
