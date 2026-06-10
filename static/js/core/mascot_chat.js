(function () {
  const mascot = document.getElementById("shuijingMascot");
  const panel = document.getElementById("mascotChatPanel");
  if (!mascot || !panel) return;

  const form = panel.querySelector("[data-chat-form]");
  const input = panel.querySelector("[data-chat-input]");
  const log = panel.querySelector("[data-chat-log]");
  const closeBtn = panel.querySelector("[data-chat-close]");
  const clearBtn = panel.querySelector("[data-chat-clear]");
  const sendBtn = panel.querySelector("[data-chat-send]");
  const chips = panel.querySelectorAll("[data-chat-prompt]");
  const chatApi = panel.dataset.chatApi;
  const clearApi = panel.dataset.clearApi;

  function openPanel() {
    panel.hidden = false;
    panel.classList.add("is-open");
    mascot.classList.add("is-chat-open");
    mascot.setAttribute("aria-expanded", "true");
    window.setTimeout(() => input && input.focus(), 80);
  }

  function closePanel() {
    panel.classList.remove("is-open");
    mascot.classList.remove("is-chat-open");
    mascot.setAttribute("aria-expanded", "false");
    window.setTimeout(() => {
      if (!panel.classList.contains("is-open")) panel.hidden = true;
    }, 180);
  }

  function togglePanel() {
    if (panel.hidden || !panel.classList.contains("is-open")) {
      openPanel();
    } else {
      closePanel();
    }
  }

  function scrollLog() {
    log.scrollTop = log.scrollHeight;
  }

  function removeEmpty() {
    const empty = log.querySelector("[data-chat-empty]");
    if (empty) empty.remove();
  }

  function addMessage(label, text, type) {
    removeEmpty();
    const item = document.createElement("div");
    item.className = `mascot-chat-message ${type}`;

    const who = document.createElement("div");
    who.className = "mascot-chat-message-label";
    who.textContent = label;

    const body = document.createElement("div");
    body.className = "mascot-chat-message-body";
    body.innerHTML = formatMessage(text);

    item.append(who, body);
    log.appendChild(item);
    scrollLog();
    return item;
  }

  function formatMessage(text) {
    if (!text) return "";

    // 1. 先抽取並解析 [DASHBOARD]...[/DASHBOARD] 區塊，避免被 HTML 轉義破壞
    let dashboardPlaceholderCount = 0;
    const dashboards = [];
    let processedText = text.replace(/\[DASHBOARD\]([\s\S]*?)\[\/DASHBOARD\]/g, (match, content) => {
      const id = `__DASHBOARD_PLACEHOLDER_${dashboardPlaceholderCount}__`;
      dashboardPlaceholderCount++;
      
      // 解析 content 中的每一行
      const lines = content.split("\n").map(l => l.trim()).filter(l => l.length > 0);
      let html = '<div class="chat-dashboard-container">';
      
      lines.forEach(line => {
        // 解析格式: Pond: 名稱 | Status: 狀態 | Species: 魚種 | Temp: 溫度 | pH: pH | DO: 溶氧 | Sal: 鹽度
        const parts = line.split("|").reduce((acc, part) => {
          const colonIdx = part.indexOf(":");
          if (colonIdx !== -1) {
            const key = part.substring(0, colonIdx).trim().toLowerCase();
            const val = part.substring(colonIdx + 1).trim();
            acc[key] = val;
          }
          return acc;
        }, {});
        
        if (!parts.pond) return;
        
        const pondName = parts.pond;
        const status = parts.status || "normal";
        const species = parts.species || "未註明";
        const temp = parts.temp || "--";
        const ph = parts.ph || "--";
        const doVal = parseFloat(parts.do) || 0;
        const doStr = parts.do || "--";
        const sal = parts.sal || "--";
        
        let statusClass = "good";
        let statusLabel = "穩定";
        if (status === "warn") {
          statusClass = "warn";
          statusLabel = "需留意";
        } else if (status === "low_oxygen" || status === "danger") {
          statusClass = "danger";
          statusLabel = "危險/缺氧";
        } else if (status === "no_recent_data") {
          statusClass = "muted";
          statusLabel = "無資料";
        }
        
        // 溶氧進度條比例與顏色
        let doPct = Math.min(100, (doVal / 10) * 100);
        let doBarColor = "var(--good, #059669)";
        if (doVal < 4) {
          doBarColor = "var(--warning, #dc2626)";
        } else if (doVal < 5) {
          doBarColor = "#f59e0b"; // amber
        }
        
        html += `
          <div class="chat-pond-card chat-pond-card--${statusClass}">
            <div class="chat-pond-header">
              <div class="chat-pond-title-wrap">
                <span class="chat-pond-name"><i class="bi bi-water"></i> ${pondName}</span>
                <span class="chat-pond-species">${species}</span>
              </div>
              <span class="chat-pond-badge chat-pond-badge--${statusClass}">${statusLabel}</span>
            </div>
            
            <div class="chat-pond-metrics-grid">
              <div class="chat-metric-item">
                <span class="chat-metric-label">溫度</span>
                <span class="chat-metric-val">${temp}°C</span>
              </div>
              <div class="chat-metric-item">
                <span class="chat-metric-label">pH 值</span>
                <span class="chat-metric-val">pH ${ph}</span>
              </div>
              <div class="chat-metric-item">
                <span class="chat-metric-label">鹽度</span>
                <span class="chat-metric-val">${sal} ppt</span>
              </div>
            </div>
            
            <div class="chat-pond-do-section">
              <div class="chat-do-header">
                <span class="chat-do-label"><i class="bi bi-wind"></i> 溶氧量 (DO)</span>
                <span class="chat-do-val">${doStr} mg/L</span>
              </div>
              <div class="chat-do-bar-bg">
                <div class="chat-do-bar-fill" style="width: ${doPct}%; background-color: ${doBarColor};"></div>
              </div>
            </div>
          </div>
        `;
      });
      
      html += '</div>';
      dashboards.push({ id, html });
      return id;
    });

    // 2. 進行原有的 HTML 轉義與 Inline Markdown 解析
    const escaped = String(processedText)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;");

    const lines = escaped.split("\n");
    let inTable = false;
    let tableHtml = "";
    const processedLines = [];

    for (let i = 0; i < lines.length; i++) {
      const line = lines[i].trim();
      if (line.startsWith("|") && line.endsWith("|")) {
        if (!inTable) {
          inTable = true;
          tableHtml = '<div class="table-responsive"><table class="chat-table">';
        }
        
        const cells = line.split("|").slice(1, -1).map(c => c.trim());
        if (cells.every(c => /^:-*|-*:-*|-*:$/.test(c) || c === "")) {
          continue;
        }
        
        tableHtml += "<tr>";
        cells.forEach(cell => {
          const tag = tableHtml.includes("<tr><tr>") || tableHtml.includes("</tr><tr>") ? "td" : "th";
          tableHtml += `<${tag}>${parseInlineMarkdown(cell)}</${tag}>`;
        });
        tableHtml += "</tr>";
      } else {
        if (inTable) {
          inTable = false;
          tableHtml += "</table></div>";
          processedLines.push(tableHtml);
          tableHtml = "";
        }
        processedLines.push(parseInlineMarkdown(line));
      }
    }
    if (inTable) {
      tableHtml += "</table></div>";
      processedLines.push(tableHtml);
    }

    let finalHtml = processedLines.join("<br>");

    // 3. 還原 DASHBOARD 區塊 HTML
    dashboards.forEach(db => {
      const escapedId = db.id.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
      finalHtml = finalHtml.replace(escapedId, db.html);
      finalHtml = finalHtml.replace(db.id, db.html);
    });

    return finalHtml;
  }

  function parseInlineMarkdown(text) {
    return text
      .replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>")
      .replace(/\*(.+?)\*/g, "<em>$1</em>")
      .replace(/`(.+?)`/g, "<code>$1</code>");
  }

  function saveMessage(label, text, role) {
    try {
      const history = JSON.parse(localStorage.getItem("shuijing_chat_history") || "[]");
      history.push({ label, text, role });
      localStorage.setItem("shuijing_chat_history", JSON.stringify(history.slice(-25)));
    } catch (e) {
      console.error("Error saving message:", e);
    }
  }

  function loadHistory() {
    try {
      const history = JSON.parse(localStorage.getItem("shuijing_chat_history") || "[]");
      if (history.length > 0) {
        removeEmpty();
        history.forEach(item => {
          const msgItem = document.createElement("div");
          msgItem.className = `mascot-chat-message ${item.role}`;

          const who = document.createElement("div");
          who.className = "mascot-chat-message-label";
          who.textContent = item.label;

          const body = document.createElement("div");
          body.className = "mascot-chat-message-body";
          body.innerHTML = formatMessage(item.text);

          msgItem.append(who, body);
          log.appendChild(msgItem);
        });
        scrollLog();
      }
    } catch (e) {
      console.error("Error loading chat history:", e);
    }
  }

  function clearHistory() {
    try {
      localStorage.removeItem("shuijing_chat_history");
    } catch (e) {
      console.error("Error clearing chat history:", e);
    }
  }

  function addTyping() {
    removeEmpty();
    const item = document.createElement("div");
    item.className = "mascot-chat-message bot typing";
    item.innerHTML = '<div class="mascot-chat-message-label">水井龜</div><div class="mascot-chat-message-body"><span></span><span></span><span></span></div>';
    log.appendChild(item);
    scrollLog();
    return item;
  }

  async function sendMessage(text) {
    const message = text.trim();
    if (!message || !chatApi) return;

    addMessage("你", message, "user");
    saveMessage("你", message, "user");
    input.value = "";
    sendBtn.disabled = true;
    const typing = addTyping();

    try {
      const response = await fetch(chatApi, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message }),
      });
      const data = await response.json();
      typing.remove();
      if (response.ok) {
        const botReply = data.reply || "我目前沒有找到合適的回覆。";
        addMessage("水井龜", botReply, "bot");
        saveMessage("水井龜", botReply, "bot");
      } else {
        const errMsg = data.error || "聊天服務暫時無法回應。";
        addMessage("系統", errMsg, "error");
        saveMessage("系統", errMsg, "error");
      }
    } catch (error) {
      typing.remove();
      const connErrMsg = `連線失敗：${error.message}`;
      addMessage("系統", connErrMsg, "error");
      saveMessage("系統", connErrMsg, "error");
    } finally {
      sendBtn.disabled = false;
      input.focus();
    }
  }

  mascot.addEventListener("click", (event) => {
    event.preventDefault();
    togglePanel();
  });

  mascot.addEventListener("keydown", (event) => {
    if (event.key === "Enter" || event.key === " ") {
      event.preventDefault();
      togglePanel();
    }
  });

  closeBtn.addEventListener("click", closePanel);

  form.addEventListener("submit", (event) => {
    event.preventDefault();
    sendMessage(input.value);
  });

  clearBtn.addEventListener("click", async () => {
    clearBtn.disabled = true;
    try {
      if (clearApi) {
        await fetch(clearApi, { method: "POST" });
      }
      clearHistory();
      log.innerHTML = '<div class="mascot-chat-empty" data-chat-empty><div class="mascot-chat-empty-title">需要水井村資訊嗎？</div><div>可以問我活動、公告、USR 成果或 AIoT 專案。</div></div>';
    } finally {
      clearBtn.disabled = false;
      input.focus();
    }
  });

  chips.forEach((chip) => {
    chip.addEventListener("click", () => {
      openPanel();
      sendMessage(chip.dataset.chatPrompt || chip.textContent || "");
    });
  });

  document.addEventListener("keydown", (event) => {
    if (event.key === "Escape" && panel.classList.contains("is-open")) {
      closePanel();
    }
  });

  // 頁面加載時自動恢復本地對話紀錄
  loadHistory();
})();
