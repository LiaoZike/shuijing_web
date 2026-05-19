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
    const escaped = String(text || "")
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;");
    return escaped
      .replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>")
      .replace(/\n/g, "<br>");
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
        addMessage("水井龜", data.reply || "我目前沒有找到合適的回覆。", "bot");
      } else {
        addMessage("系統", data.error || "聊天服務暫時無法回應。", "error");
      }
    } catch (error) {
      typing.remove();
      addMessage("系統", `連線失敗：${error.message}`, "error");
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
})();
