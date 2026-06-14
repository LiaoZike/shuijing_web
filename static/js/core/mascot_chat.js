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
  
  const micBtn = document.getElementById("mascotMicBtn");
  const cancelMicBtn = document.getElementById("mascotCancelMicBtn");
  const waitingBanner = document.getElementById("mascotWaitingBanner");
  const waitingText = waitingBanner ? waitingBanner.querySelector(".mascot-waiting-banner-text") : null;
  
  const chatApi = panel.dataset.chatApi;
  const clearApi = panel.dataset.clearApi;
  const voiceApi = panel.dataset.voiceApi;

  function checkAndExecuteNavigation(text) {
    if (!text) return text;
    const navRegex = /\[NAVIGATE\]([\s\S]*?)\[\/NAVIGATE\]/;
    const match = text.match(navRegex);
    if (match) {
      const content = match[1];
      const lines = content.split("\n").map(l => l.trim()).filter(l => l.length > 0);
      let url = "";
      let delay = 900;
      lines.forEach(line => {
        const colonIdx = line.indexOf(":");
        if (colonIdx !== -1) {
          const key = line.substring(0, colonIdx).trim().toLowerCase();
          const val = line.substring(colonIdx + 1).trim();
          if (key === "url") {
            url = val;
          } else if (key === "delay") {
            delay = parseInt(val) || 900;
          }
        }
      });
      if (url) {
        const cleanText = text.replace(navRegex, "").trim();
        setTimeout(() => {
          window.location.href = url;
        }, delay);
        return cleanText;
      }
    }
    return text;
  }

  const defaultInputPlaceholder = input ? (input.getAttribute("placeholder") || "") : "";
  // 語音輸入變數
  let mediaRecorder = null;
  let audioChunks = [];
  let isRecording = false;
  let isCancelled = false;
  let recordTimeout = null;
  let recordCountdownInterval = null;
  let transcribingInterval = null;
  let activeStream = null;

  // ── Chart.js 畫圖輔助函數 ──
  function hexToRgb(hex) {
    const shorthandRegex = /^#?([a-f\d])([a-f\d])([a-f\d])$/i;
    hex = hex.replace(shorthandRegex, (m, r, g, b) => r + r + g + g + b + b);
    const result = /^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i.exec(hex);
    return result ? `${parseInt(result[1], 16)}, ${parseInt(result[2], 16)}, ${parseInt(result[3], 16)}` : "15, 118, 110";
  }

  function initChart(canvas, data) {
    if (typeof Chart === "undefined") {
      console.error("Chart.js is not loaded.");
      return;
    }
    const ctx = canvas.getContext('2d');
    const colors = [
      { border: '#0f766e', bg: 'rgba(15, 118, 110, 0.15)', bgSolid: '#0f766e' },
      { border: '#f59e0b', bg: 'rgba(245, 158, 11, 0.15)', bgSolid: '#f59e0b' },
      { border: '#3b82f6', bg: 'rgba(59, 130, 246, 0.15)', bgSolid: '#3b82f6' },
      { border: '#10b981', bg: 'rgba(16, 185, 129, 0.15)', bgSolid: '#10b981' },
      { border: '#ec4899', bg: 'rgba(236, 72, 153, 0.15)', bgSolid: '#ec4899' },
    ];
    
    const datasets = data.datasets.map((ds, idx) => {
      const colorSet = colors[idx % colors.length];
      const isLine = data.type === 'line';
      let bg = colorSet.bg;
      if (isLine) {
        const gradient = ctx.createLinearGradient(0, 0, 0, 160);
        const rgb = hexToRgb(colorSet.border);
        gradient.addColorStop(0, `rgba(${rgb}, 0.3)`);
        gradient.addColorStop(1, `rgba(${rgb}, 0)`);
        bg = gradient;
      } else if (data.type === 'doughnut') {
        const sliceColors = data.labels.map((_, sIdx) => colors[sIdx % colors.length].bgSolid);
        return {
          label: ds.label,
          data: ds.values,
          backgroundColor: sliceColors,
          borderColor: '#ffffff',
          borderWidth: 2,
          hoverOffset: 6
        };
      }
      
      return {
        label: ds.label,
        data: ds.values,
        borderColor: colorSet.border,
        backgroundColor: bg,
        borderWidth: 2.5,
        fill: isLine,
        tension: 0.35,
        pointBackgroundColor: colorSet.border,
        pointBorderColor: '#ffffff',
        pointBorderWidth: 1.5,
        pointRadius: 4,
        pointHoverRadius: 6,
        barThickness: data.type === 'bar' ? 16 : undefined,
        borderRadius: data.type === 'bar' ? 4 : undefined,
      };
    });

    const config = {
      type: data.type === 'bar' || data.type === 'line' || data.type === 'doughnut' ? data.type : 'bar',
      data: {
        labels: data.labels,
        datasets: datasets
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: {
            display: data.type !== 'doughnut',
            position: 'top',
            labels: {
              boxWidth: 12,
              font: { size: 11, weight: 'bold' },
              color: '#4d3d26'
            }
          },
          tooltip: {
            padding: 8,
            titleFont: { size: 12, weight: 'bold' },
            bodyFont: { size: 12 },
            cornerRadius: 8
          }
        },
        scales: data.type === 'doughnut' ? undefined : {
          y: {
            beginAtZero: true,
            grid: { color: 'rgba(0, 0, 0, 0.05)' },
            ticks: { color: '#7b6a52', font: { size: 10 } }
          },
          x: {
            grid: { display: false },
            ticks: { color: '#7b6a52', font: { size: 10 } }
          }
        }
      }
    };
    new Chart(ctx, config);
  }

  function initializeChartsInMessage(element) {
    element.querySelectorAll(".chat-chart-card").forEach(card => {
      if (card.classList.contains("is-initialized")) return;
      const configStr = card.getAttribute("data-chart-config");
      if (configStr) {
        try {
          const config = JSON.parse(decodeURIComponent(configStr));
          const canvas = card.querySelector(".chat-chart-canvas");
          requestAnimationFrame(() => {
            initChart(canvas, config);
            card.classList.add("is-initialized");
          });
        } catch (e) {
          console.error("Failed to render chart:", e);
        }
      }
    });
  }

  function showWaiting(text, isGrey = false, options = {}) {
    if (!waitingBanner) return;
    if (waitingText) {
      waitingText.textContent = text;
    }
    if (isGrey) {
      waitingBanner.classList.add("is-grey");
    } else {
      waitingBanner.classList.remove("is-grey");
    }
    waitingBanner.hidden = false;
    
    if (options.immediate) {
      waitingBanner.classList.add("is-active");
    } else {
      waitingBanner.offsetHeight; // force reflow
      waitingBanner.classList.add("is-active");
    }
  }

  function hideWaiting() {
    if (!waitingBanner) return;
    waitingBanner.classList.remove("is-active");
    setTimeout(function () {
      if (!waitingBanner.classList.contains("is-active")) {
        waitingBanner.hidden = true;
        waitingBanner.classList.remove("is-grey");
      }
    }, 300);
  }

  function openPanel() {
    panel.hidden = false;
    panel.classList.add("is-open");
    mascot.classList.add("is-chat-open");
    mascot.setAttribute("aria-expanded", "true");
    window.setTimeout(() => {
      scrollLog();
      updateScrollBottomButton();
    }, 80);
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
    updateScrollBottomButton();
  }

  function isLogNearBottom() {
    return log.scrollHeight - log.scrollTop - log.clientHeight < 80;
  }

  const scrollBottomBtn = document.createElement("button");
  scrollBottomBtn.type = "button";
  scrollBottomBtn.className = "chat-scroll-bottom";
  scrollBottomBtn.setAttribute("aria-label", "回到最新訊息");
  scrollBottomBtn.title = "回到最新訊息";
  scrollBottomBtn.innerHTML = '<i class="bi bi-arrow-down"></i>';
  panel.appendChild(scrollBottomBtn);

  function updateScrollBottomButton() {
    scrollBottomBtn.classList.toggle("is-visible", panel.classList.contains("is-open") && !isLogNearBottom());
  }

  scrollBottomBtn.addEventListener("click", () => {
    log.scrollTo({ top: log.scrollHeight, behavior: "smooth" });
    window.setTimeout(updateScrollBottomButton, 220);
  });

  log.addEventListener("scroll", updateScrollBottomButton, { passive: true });

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
    
    initializeChartsInMessage(item);
    return item;
  }

  function normalizeMessageText(value) {
    return String(value || "")
      .replace(/&lt;br\s*\/?&gt;/gi, "\n")
      .replace(/<br\s*\/?>/gi, "\n");
  }

  function formatMessage(text) {
    if (!text) return "";

    // 0. 先抽取並解析 [CHART]...[/CHART] 區塊，避免被 HTML 轉義破壞
    let chartPlaceholderCount = 0;
    const charts = [];
    let processedText = normalizeMessageText(text).replace(/\[CHART\]([\s\S]*?)\[\/CHART\]/g, (match, content) => {
      const id = `__CHART_PLACEHOLDER_${chartPlaceholderCount}__`;
      chartPlaceholderCount++;
      
      const lines = content.split("\n").map(l => l.trim()).filter(l => l.length > 0);
      let type = "bar";
      let title = "";
      let labels = [];
      let datasets = [];
      
      lines.forEach(line => {
        const colonIdx = line.indexOf(":");
        if (colonIdx === -1) return;
        const key = line.substring(0, colonIdx).trim().toLowerCase();
        const val = line.substring(colonIdx + 1).trim();
        
        if (key === "type") {
          type = val.toLowerCase();
        } else if (key === "title") {
          title = val;
        } else if (key === "x-axis") {
          labels = val.split(",").map(s => s.trim());
        } else if (key === "dataset") {
          const parts = val.split("|").reduce((acc, part) => {
            const subColonIdx = part.indexOf(":");
            if (subColonIdx !== -1) {
              const subKey = part.substring(0, subColonIdx).trim().toLowerCase();
              const subVal = part.substring(subColonIdx + 1).trim();
              acc[subKey] = subVal;
            } else {
              acc["name"] = part.trim();
            }
            return acc;
          }, {});
          
          const label = parts.name || parts.dataset || "數據";
          const valuesStr = parts.values || "";
          const values = valuesStr.split(",").map(v => parseFloat(v.trim()) || 0);
          datasets.push({ label, values });
        }
      });
      
      const chartConfig = { type, title, labels, datasets };
      const html = `
        <div class="chat-chart-card" data-chart-config="${encodeURIComponent(JSON.stringify(chartConfig))}">
          <div class="chat-chart-title"><i class="bi bi-bar-chart-line-fill"></i> ${title || '數據圖表'}</div>
          <div class="chat-chart-body">
            <canvas class="chat-chart-canvas"></canvas>
          </div>
        </div>
      `;
      charts.push({ id, html });
      return id;
    });

    // 1. 先抽取並解析 [DASHBOARD]...[/DASHBOARD] 區塊，避免被 HTML 轉義破壞
    let dashboardPlaceholderCount = 0;
    const dashboards = [];
    processedText = processedText.replace(/\[DASHBOARD\]([\s\S]*?)\[\/DASHBOARD\]/g, (match, content) => {
      const id = `__DASHBOARD_PLACEHOLDER_${dashboardPlaceholderCount}__`;
      dashboardPlaceholderCount++;
      
      const lines = content.split("\n").map(l => l.trim()).filter(l => l.length > 0);
      let html = '<div class="chat-dashboard-container">';
      
      lines.forEach(line => {
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
        
        let doPct = Math.min(100, (doVal / 10) * 100);
        let doBarColor = "var(--good, #059669)";
        if (doVal < 4) {
          doBarColor = "var(--warning, #dc2626)";
        } else if (doVal < 5) {
          doBarColor = "#f59e0b";
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
    let tableRows = [];
    let listTag = "";
    const processedLines = [];

    function isMarkdownTableDivider(cells) {
      return cells.every(c => /^:?-+:?$/.test(c) || c === "");
    }

    function buildMascotTableCards(rows) {
      const headers = rows[0] || [];
      const bodyRows = rows.length > 1 ? rows.slice(1) : rows;

      if (!bodyRows.length) return "";

      const cards = bodyRows.map((row, rowIndex) => {
        const normalizedHeaders = headers.length ? headers : row.map((_, index) => `欄位 ${index + 1}`);
        const titleIndex = row.findIndex(cell => cell && cell.trim());
        const titleLabel = normalizedHeaders[titleIndex] || `資料 ${rowIndex + 1}`;
        const titleValue = titleIndex >= 0 ? row[titleIndex] : `資料 ${rowIndex + 1}`;

        const fields = normalizedHeaders.map((header, index) => {
          if (index === titleIndex && normalizedHeaders.length > 1) return "";
          const value = row[index] || "";
          if (!header && !value) return "";
          return `
            <div class="mascot-table-field">
              <span class="mascot-table-label">${parseInlineMarkdown(header || `欄位 ${index + 1}`)}</span>
              <span class="mascot-table-value">${parseInlineMarkdown(value || "-")}</span>
            </div>
          `;
        }).join("");

        return `
          <section class="mascot-table-card">
            <div class="mascot-table-card-title">
              <span class="mascot-table-card-title-label">${parseInlineMarkdown(titleLabel)}</span>
              <strong>${parseInlineMarkdown(titleValue)}</strong>
            </div>
            <div class="mascot-table-card-grid">${fields}</div>
          </section>
        `;
      }).join("");

      return `<div class="mascot-table-cards">${cards}</div>`;
    }

    function flushTableRows() {
      if (!tableRows.length) return;
      processedLines.push(buildMascotTableCards(tableRows));
      tableRows = [];
    }

    function flushList() {
      if (!listTag) return;
      processedLines.push(`</${listTag}>`);
      listTag = "";
    }

    function pushListItem(tag, content) {
      if (listTag && listTag !== tag) flushList();
      if (!listTag) {
        listTag = tag;
        processedLines.push(`<${tag} class="chat-markdown-list">`);
      }
      processedLines.push(`<li>${parseInlineMarkdown(content)}</li>`);
    }

    for (let i = 0; i < lines.length; i++) {
      const line = lines[i].trim();
      if (line.startsWith("|") && line.endsWith("|")) {
        flushList();
        const cells = line.split("|").slice(1, -1).map(c => c.trim());
        // 🟢 修正的表格分隔線正則表達式，完美支援 ---, :---, ---:, :---:
        if (isMarkdownTableDivider(cells)) {
          continue;
        }

        tableRows.push(cells);
      } else {
        flushTableRows();
        if (!line) {
          flushList();
          continue;
        }

        const heading = line.match(/^(#{1,6})\s*(.+)$/);
        const unordered = line.match(/^[-*+]\s+(.+)$/);
        const ordered = line.match(/^\d+[.)]\s+(.+)$/);

        if (heading) {
          flushList();
          const level = Math.min(3, heading[1].length + 1);
          processedLines.push(`<h${level} class="chat-markdown-heading">${parseInlineMarkdown(heading[2])}</h${level}>`);
        } else if (/^(-{3,}|\*{3,}|_{3,})$/.test(line)) {
          flushList();
          processedLines.push('<hr class="chat-markdown-divider">');
        } else if (unordered) {
          pushListItem("ul", unordered[1]);
        } else if (ordered) {
          pushListItem("ol", ordered[1]);
        } else if (line.startsWith("&gt;")) {
          flushList();
          processedLines.push(`<blockquote class="chat-markdown-quote">${parseInlineMarkdown(line.replace(/^&gt;\s?/, ""))}</blockquote>`);
        } else if (/^__(CHART|DASHBOARD)_PLACEHOLDER_\d+__$/.test(line)) {
          flushList();
          processedLines.push(line);
        } else {
          flushList();
          processedLines.push(`<p>${parseInlineMarkdown(line)}</p>`);
        }
      }
    }
    flushTableRows();
    flushList();

    let finalHtml = processedLines.join("");

    // 3. 還原 DASHBOARD 區塊 HTML
    dashboards.forEach(db => {
      const escapedId = db.id.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
      finalHtml = finalHtml.replace(escapedId, db.html);
      finalHtml = finalHtml.replace(db.id, db.html);
    });

    // 4. 還原 CHART 區塊 HTML
    charts.forEach(c => {
      const escapedId = c.id.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
      finalHtml = finalHtml.replace(escapedId, c.html);
      finalHtml = finalHtml.replace(c.id, c.html);
    });

    return finalHtml;
  }

  function parseInlineMarkdown(text) {
    return text
      .replace(/\[([^\]]+)\]\(\s*([^)]+?)\s*\)(?:\s*\(\s*\2\s*\))?/g, function(match, label, href) {
        const cleanHref = href.trim();
        return `<a href="${cleanHref}" target="_blank" rel="noopener noreferrer">${label}</a>`;
      })
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
        initializeChartsInMessage(log);
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

    let waitMsg = "水井龜正在幫您分析水質資料...";
    if (message.includes("活動")) {
      waitMsg = "水井龜正在為您查詢最新活動資訊...";
    } else if (message.includes("公告")) {
      waitMsg = "水井龜正在抓取最新網站公告...";
    } else if (message.includes("警報")) {
      waitMsg = "水井龜正在檢測目前是否有感測器警報...";
    } else if (message.includes("功能健檢") || message.includes("穩定")) {
      waitMsg = "水井龜正在為您評估魚池穩定度指標...";
    } else if (message.includes("歷史") || message.includes("趨勢")) {
      waitMsg = "水井龜正在繪製精美的水質歷史趨勢圖...";
    }
    showWaiting(waitMsg);

    try {
      const response = await fetch(chatApi, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message }),
      });
      const data = await response.json();
      typing.remove();
      hideWaiting();
      if (response.ok) {
        let botReply = data.reply || "我目前沒有找到合適的回覆。";
        botReply = checkAndExecuteNavigation(botReply);
        addMessage("水井龜", botReply, "bot");
        saveMessage("水井龜", botReply, "bot");
      } else {
        const errMsg = data.error || "聊天服務暫時無法回應。";
        addMessage("系統", errMsg, "error");
        saveMessage("系統", errMsg, "error");
      }
    } catch (error) {
      typing.remove();
      hideWaiting();
      const connErrMsg = `連線失敗：${error.message}`;
      addMessage("系統", connErrMsg, "error");
      saveMessage("系統", connErrMsg, "error");
    } finally {
      sendBtn.disabled = false;
      input.focus();
    }
  }

  // ── 語音錄音與 ASR 功能 ──
  async function startRecording() {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      activeStream = stream;
      audioChunks = [];
      isCancelled = false;

      let mimeType = "audio/webm";
      if (MediaRecorder.isTypeSupported("audio/webm;codecs=opus")) {
        mimeType = "audio/webm;codecs=opus";
      } else if (MediaRecorder.isTypeSupported("audio/ogg;codecs=opus")) {
        mimeType = "audio/ogg;codecs=opus";
      } else if (MediaRecorder.isTypeSupported("audio/wav")) {
        mimeType = "audio/wav";
      }

      mediaRecorder = new MediaRecorder(stream, { mimeType });

      mediaRecorder.ondataavailable = (event) => {
        if (event.data && event.data.size > 0) {
          audioChunks.push(event.data);
        }
      };

      mediaRecorder.onstop = async () => {
        stream.getTracks().forEach(track => track.stop());
        activeStream = null;

        if (isCancelled) {
          resetMicUI();
          return;
        }

        setMicState("transcribing");

        const audioBlob = new Blob(audioChunks, { type: mediaRecorder.mimeType || "audio/webm" });
        await sendAudioToASR(audioBlob);
      };

      mediaRecorder.start();
      isRecording = true;
      setMicState("recording");

      let remaining = 20;
      if (input) {
        input.placeholder = `🎙️ 聆聽中... 還可以說 ${remaining} 秒`;
      }
      recordCountdownInterval = setInterval(() => {
        remaining -= 1;
        if (remaining <= 0) {
          if (recordCountdownInterval) {
            clearInterval(recordCountdownInterval);
            recordCountdownInterval = null;
          }
        } else if (input) {
          input.placeholder = `🎙️ 聆聽中... 還可以說 ${remaining} 秒`;
        }
      }, 1000);

      recordTimeout = setTimeout(() => {
        if (isRecording) stopRecording();
      }, 20000);

    } catch (err) {
      console.error("Error accessing microphone:", err);
      addMessage("系統", "無法存取麥克風，請確認瀏覽器權限或確認麥克風是否已啟用。", "error");
      resetMicUI();
    }
  }

  function stopRecording() {
    if (mediaRecorder && mediaRecorder.state !== "inactive") {
      mediaRecorder.stop();
    }
    isRecording = false;
    if (recordTimeout) {
      clearTimeout(recordTimeout);
      recordTimeout = null;
    }
    if (recordCountdownInterval) {
      clearInterval(recordCountdownInterval);
      recordCountdownInterval = null;
    }
  }

  function cancelRecording() {
    isCancelled = true;
    if (mediaRecorder && mediaRecorder.state !== "inactive") {
      mediaRecorder.stop();
    }
    if (activeStream) {
      activeStream.getTracks().forEach(track => track.stop());
      activeStream = null;
    }
    isRecording = false;
    if (recordTimeout) {
      clearTimeout(recordTimeout);
      recordTimeout = null;
    }
    if (recordCountdownInterval) {
      clearInterval(recordCountdownInterval);
      recordCountdownInterval = null;
    }
  }

  async function sendAudioToASR(blob) {
    if (!voiceApi) {
      addMessage("系統", "語音辨識 API 尚未配置，請聯繫管理員。", "error");
      resetMicUI();
      return;
    }

    const formData = new FormData();
    formData.append("audio", blob, "voice.webm");
    
    // Get CSRF Token
    let csrfToken = null;
    if (document.cookie && document.cookie !== "") {
      const cookies = document.cookie.split(";");
      for (let i = 0; i < cookies.length; i++) {
        const cookie = cookies[i].trim();
        if (cookie.substring(0, 10) === "csrftoken=") {
          csrfToken = decodeURIComponent(cookie.substring(10));
          break;
        }
      }
    }

    try {
      const response = await fetch(voiceApi, {
        method: "POST",
        headers: { "X-CSRFToken": csrfToken },
        body: formData
      });

      const data = await response.json();
      if (response.ok && data.text) {
        const recognizedText = data.text.trim();
        if (recognizedText) {
          showVoicePreviewAndSend(recognizedText);
        } else {
          addMessage("系統", "語音辨識結果為空，請重試。", "error");
        }
      } else {
        const errorMsg = data.error || "語音辨識失敗，請重試或以打字輸入。";
        addMessage("系統", errorMsg, "error");
      }
    } catch (err) {
      console.error("Error calling voice ASR API:", err);
      addMessage("系統", "無法連線至語音辨識服務，請檢查網路或確認後台 ASR 設定。", "error");
    } finally {
      resetMicUI();
    }
  }

  function showVoicePreviewAndSend(text) {
    const existingPreview = panel.querySelector(".voice-asr-preview");
    if (existingPreview) existingPreview.remove();

    const preview = document.createElement("div");
    preview.className = "voice-asr-preview";
    preview.innerHTML = `<i class="bi bi-mic-fill"></i> <span>${text}</span>`;
    form.parentElement.insertBefore(preview, form);

    setTimeout(() => {
      preview.classList.add("is-fading");
      setTimeout(() => preview.remove(), 400);
    }, 800);

    sendMessage(text);
  }

  function setMicState(state) {
    if (!micBtn) return;
    if (state === "recording") {
      micBtn.classList.add("is-recording");
      micBtn.classList.remove("is-loading");
      micBtn.title = "結束並送出辨識";
      if (cancelMicBtn) cancelMicBtn.hidden = false;
      showWaiting("正在錄音中，請直接說話。按 X 可取消錄音。", true, { immediate: true });
      if (input) {
        input.placeholder = "🎙️ 聆聽中... 還可以說 20 秒";
        input.disabled = true;
      }
      if (sendBtn) sendBtn.disabled = true;
      if (clearBtn) clearBtn.disabled = true;
    } else if (state === "transcribing") {
      micBtn.classList.remove("is-recording");
      micBtn.classList.add("is-loading");
      micBtn.disabled = true;
      micBtn.title = "語音辨識中";
      if (cancelMicBtn) cancelMicBtn.hidden = true;
      
      const icon = micBtn.querySelector("i");
      if (icon) {
        icon.className = "bi bi-arrow-clockwise mascot-spin";
      }

      showWaiting("🎙️ 水井龜正在幫您辨識語音，請稍候...", true, { immediate: true });
      
      let dots = 0;
      if (input) {
        input.placeholder = "⚡ 正在辨識中";
      }
      transcribingInterval = setInterval(() => {
        dots = (dots + 1) % 4;
        if (input) {
          input.placeholder = "⚡ 正在辨識中" + ".".repeat(dots);
        }
      }, 400);
    }
  }

  function resetMicUI() {
    if (!micBtn) return;
    micBtn.classList.remove("is-recording");
    micBtn.classList.remove("is-loading");
    micBtn.disabled = false;
    micBtn.title = "語音輸入（台語/國語）";
    if (cancelMicBtn) cancelMicBtn.hidden = true;
    if (input) {
      input.placeholder = defaultInputPlaceholder;
      input.disabled = false;
    }
    if (sendBtn) sendBtn.disabled = false;
    if (clearBtn) clearBtn.disabled = false;
    isRecording = false;
    isCancelled = false;
    if (recordCountdownInterval) {
      clearInterval(recordCountdownInterval);
      recordCountdownInterval = null;
    }
    if (transcribingInterval) {
      clearInterval(transcribingInterval);
      transcribingInterval = null;
    }
    hideWaiting();
    
    const icon = micBtn.querySelector("i");
    if (icon) {
      icon.className = "bi bi-mic-fill";
    }
  }

  // Event Listeners
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
    if (!window.confirm("確定要清除目前的 AI 對話紀錄嗎？")) {
      input.focus();
      return;
    }
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

  if (cancelMicBtn) {
    cancelMicBtn.addEventListener("click", (e) => {
      e.preventDefault();
      cancelRecording();
    });
  }

  if (micBtn) {
    const isSupported = !!(navigator.mediaDevices && window.MediaRecorder);
    if (!isSupported) {
      micBtn.style.opacity = "0.5";
      micBtn.title = "語音輸入（目前連線環境不支援）";
    } else {
      micBtn.addEventListener("click", (e) => {
        e.preventDefault();
        if (!isRecording) {
          startRecording();
        } else {
          stopRecording();
        }
      });
    }
  }

  // 頁面加載時自動恢復本地對話紀錄
  loadHistory();
  loadHistory();
})();
