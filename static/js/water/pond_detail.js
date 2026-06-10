/**
 * pond_detail.js
 * 感測器 & 閘門地圖互動 + 編輯模式管理 + 歷史數據圖表 + 自訂警戒值切換
 * 全面非同步 (AJAX) 優化
 */
(function () {
    'use strict';

    const pondMap = document.getElementById('pondMap');
    const btnEditMode = document.getElementById('btnEditMode');
    const workbench = document.getElementById('sensorWorkbench');
    const btnCloseWorkbench = document.getElementById('btnCloseWorkbench');
    const pinsContainer = document.getElementById('pinsContainer');
    const workbenchList = document.getElementById('workbenchList');
    const ajaxStatus = document.getElementById('ajaxStatus');

    // Threshold elements
    const thresholdTargetSelect = document.getElementById('thresholdTargetSelect');
    const thresholdsForm = document.getElementById('thresholdsForm');
    const thresholdStatusBadge = document.getElementById('thresholdStatusBadge');
    const btnRestoreThresholds = document.getElementById('btnRestoreThresholds');
    const formTargetSensorId = document.getElementById('formTargetSensorId');
    const thresholdsDataEl = document.getElementById('thresholdsData');

    // History elements
    const historySensorSelect = document.getElementById('historySensorSelect');
    const historyMetricSelect = document.getElementById('historyMetricSelect');
    const historyTimeSelect = document.getElementById('historyTimeSelect');
    const btnExportCSV = document.getElementById('btnExportCSV');
    const btnGenerateMock = document.getElementById('btnGenerateMock');
    const historyTableBody = document.getElementById('historyTableBody');
    const chartEmptyState = document.getElementById('chartEmptyState');
    const historyStartDate = document.getElementById('historyStartDate');
    const historyEndDate = document.getElementById('historyEndDate');
    const customDateContainer = document.getElementById('customDateContainer');

    // Initialize custom date pickers
    if (historyStartDate && historyEndDate) {
        const today = new Date();
        const todayStr = today.toISOString().split('T')[0];
        const sevenDaysAgo = new Date();
        sevenDaysAgo.setDate(sevenDaysAgo.getDate() - 7);
        const sevenDaysAgoStr = sevenDaysAgo.toISOString().split('T')[0];

        if (!historyStartDate.value) historyStartDate.value = sevenDaysAgoStr;
        if (!historyEndDate.value) historyEndDate.value = todayStr;
    }

    let isEditMode = false;
    let draggedElement = null;
    let dragType = null; // 'sensor' or 'gate'
    let dragOffset = { x: 0, y: 0 };
    let statusTimeout = null;
    let thresholdsData = {};

    if (thresholdsDataEl) {
        try {
            thresholdsData = JSON.parse(thresholdsDataEl.textContent);
        } catch (e) {
            console.error('Failed to parse thresholds data', e);
        }
    }

    // ========== 編輯模式切換 ==========

    function toggleEditMode(forceState) {
        isEditMode = typeof forceState === 'boolean' ? forceState : !isEditMode;

        if (pondMap) {
            pondMap.classList.toggle('edit-mode', isEditMode);
        }

        if (btnEditMode) {
            btnEditMode.classList.toggle('active', isEditMode);
        }

        if (workbench) {
            workbench.classList.toggle('is-open', isEditMode);
            if (isEditMode) {
                // 平滑滾動到管理面板
                setTimeout(() => {
                    workbench.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
                }, 100);
            }
        }

        // 更新感測器與閘門的游標
        document.querySelectorAll('.sensor-pin, .map-gate').forEach(el => {
            el.style.cursor = isEditMode ? 'grab' : '';
        });
    }

    if (btnEditMode) {
        btnEditMode.addEventListener('click', () => toggleEditMode());
    }

    if (btnCloseWorkbench) {
        btnCloseWorkbench.addEventListener('click', () => toggleEditMode(false));
    }

    // ========== AJAX 狀態指示器 ==========

    function showAjaxStatus(type, message) {
        if (!ajaxStatus) return;

        ajaxStatus.className = `ajax-status ${type}`;

        let iconHtml = '';
        if (type === 'syncing') {
            iconHtml = '<span class="spinner-border spinner-border-sm" role="status" style="width:0.8rem; height:0.8rem; border-width:0.12em;"></span>';
        } else if (type === 'success') {
            iconHtml = '<i class="bi bi-check-circle-fill"></i>';
        } else if (type === 'error') {
            iconHtml = '<i class="bi bi-exclamation-circle-fill"></i>';
        }

        ajaxStatus.innerHTML = `${iconHtml} <span>${message}</span>`;
        ajaxStatus.style.display = 'inline-flex';
        ajaxStatus.style.opacity = '1';

        if (statusTimeout) clearTimeout(statusTimeout);

        if (type === 'success') {
            statusTimeout = setTimeout(() => {
                ajaxStatus.style.transition = 'opacity 0.4s, transform 0.4s';
                ajaxStatus.style.opacity = '0';
                setTimeout(() => {
                    ajaxStatus.style.display = 'none';
                    ajaxStatus.style.transition = '';
                }, 400);
            }, 3000);
        }
    }

    // ========== AJAX 請求工具 ==========

    function ajaxAction(fields) {
        const formData = new FormData();
        fields.csrfmiddlewaretoken = getCookie('csrftoken');
        
        for (const [key, value] of Object.entries(fields)) {
            formData.append(key, value);
        }

        return fetch(window.location.href, {
            method: 'POST',
            body: formData,
            headers: {
                'X-Requested-With': 'XMLHttpRequest'
            }
        })
        .then(response => {
            if (!response.ok) {
                return response.json().then(data => {
                    throw new Error(data.message || '網路錯誤或伺服器回應異常');
                }).catch(() => {
                    throw new Error('伺服器異常，請重試');
                });
            }
            return response.json();
        });
    }

    function getCookie(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (const cookie of cookies) {
                const c = cookie.trim();
                if (c.startsWith(name + '=')) {
                    cookieValue = decodeURIComponent(c.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }

    let isDraggingOccurred = false;

    // ========== 感測器與閘門拖拽 ==========

    function setupDragging() {
        // 感測器
        document.querySelectorAll('.sensor-pin').forEach(pin => {
            pin.removeEventListener('mousedown', onDragStart);
            pin.removeEventListener('touchstart', onTouchStart);
            pin.removeEventListener('click', onPinClick);
            
            pin.addEventListener('mousedown', onDragStart);
            pin.addEventListener('touchstart', onTouchStart, { passive: false });
            pin.addEventListener('click', onPinClick);
        });

        // 閘門
        document.querySelectorAll('.map-gate').forEach(gate => {
            gate.removeEventListener('mousedown', onGateDragStart);
            gate.removeEventListener('touchstart', onGateTouchStart);
            gate.addEventListener('mousedown', onGateDragStart);
            gate.addEventListener('touchstart', onGateTouchStart, { passive: false });
        });
    }

    function onPinClick(e) {
        if (isDraggingOccurred) return; // 如果發生拖動，不視為純點擊選取
        
        const wrapper = e.currentTarget.closest('.sensor-wrapper');
        if (!wrapper) return;
        
        const sensorId = wrapper.dataset.sensorId;
        if (sensorId && thresholdTargetSelect) {
            thresholdTargetSelect.value = sensorId;
            thresholdTargetSelect.dispatchEvent(new Event('change'));
            
            const thresholdsSection = document.getElementById('thresholdsSection');
            if (thresholdsSection) {
                // 重啟高亮綠色呼吸光動畫
                thresholdsSection.classList.remove('highlight-flash');
                void thresholdsSection.offsetWidth; // 強制瀏覽器重繪 (Reflow)
                thresholdsSection.classList.add('highlight-flash');
                
                // 行動版/平板寬度下平滑滾動到設定區
                if (window.innerWidth < 1200) {
                    thresholdsSection.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
                }
            }
        }
    }

    function onDragStart(e) {
        if (!isEditMode) return;
        e.preventDefault();
        draggedElement = e.currentTarget.closest('.sensor-wrapper');
        dragType = 'sensor';
        startDrag(e.clientX, e.clientY);
    }


    function onTouchStart(e) {
        if (!isEditMode) return;
        e.preventDefault();
        draggedElement = e.currentTarget.closest('.sensor-wrapper');
        dragType = 'sensor';
        startDrag(e.touches[0].clientX, e.touches[0].clientY);
    }

    function onGateDragStart(e) {
        if (!isEditMode) return;
        e.preventDefault();
        draggedElement = e.currentTarget;
        dragType = 'gate';
        startDrag(e.clientX, e.clientY);
    }

    function onGateTouchStart(e) {
        if (!isEditMode) return;
        e.preventDefault();
        draggedElement = e.currentTarget;
        dragType = 'gate';
        startDrag(e.touches[0].clientX, e.touches[0].clientY);
    }

    function startDrag(clientX, clientY) {
        if (!draggedElement) return;

        isDraggingOccurred = false; // 初始化拖動標記

        const rect = draggedElement.getBoundingClientRect();
        dragOffset.x = clientX - rect.left - rect.width / 2;
        dragOffset.y = clientY - rect.top - rect.height / 2;

        if (dragType === 'sensor') {
            const pin = draggedElement.querySelector('.sensor-pin');
            if (pin) pin.classList.add('dragging');
            document.addEventListener('mousemove', onDragMove);
            document.addEventListener('mouseup', onDragEnd);
            document.addEventListener('touchmove', onTouchMove, { passive: false });
            document.addEventListener('touchend', onTouchEnd);
        } else {
            draggedElement.classList.add('dragging');
            document.addEventListener('mousemove', onGateDragMove);
            document.addEventListener('mouseup', onGateDragEnd);
            document.addEventListener('touchmove', onGateTouchMove, { passive: false });
            document.addEventListener('touchend', onGateTouchEnd);
        }
    }

    function moveElement(clientX, clientY) {
        if (!draggedElement || !pondMap) return;

        isDraggingOccurred = true; // 發生移動，設定為拖動中

        const mapRect = pondMap.getBoundingClientRect();
        const x = clientX - mapRect.left - dragOffset.x;
        const y = clientY - mapRect.top - dragOffset.y;

        const pctX = Math.max(1, Math.min(99, (x / mapRect.width) * 100));
        const pctY = Math.max(1, Math.min(99, (y / mapRect.height) * 100));

        draggedElement.style.left = pctX + '%';
        draggedElement.style.top = pctY + '%';
        
        if (dragType === 'sensor') {
            draggedElement.classList.toggle('tooltip-down', pctY < 35);
            const sensorId = draggedElement.dataset.sensorId;
            updatePosInputs(sensorId, Math.round(pctX), Math.round(pctY));
        }
    }

    function onDragMove(e) { moveElement(e.clientX, e.clientY); }
    function onTouchMove(e) { e.preventDefault(); moveElement(e.touches[0].clientX, e.touches[0].clientY); }

    function onDragEnd() {
        if (draggedElement) {
            const pin = draggedElement.querySelector('.sensor-pin');
            if (pin) pin.classList.remove('dragging');
            saveSensorAjax(draggedElement.dataset.sensorId);
        }
        draggedElement = null;
        document.removeEventListener('mousemove', onDragMove);
        document.removeEventListener('mouseup', onDragEnd);
        document.removeEventListener('touchmove', onTouchMove);
        document.removeEventListener('touchend', onTouchEnd);
    }

    function onTouchEnd() { onDragEnd(); }

    // 閘門拖拽移動
    function onGateDragMove(e) { moveElement(e.clientX, e.clientY); }
    function onGateTouchMove(e) { e.preventDefault(); moveElement(e.touches[0].clientX, e.touches[0].clientY); }

    function onGateDragEnd() {
        if (draggedElement) {
            draggedElement.classList.remove('dragging');
            saveGatesAjax();
        }
        draggedElement = null;
        document.removeEventListener('mousemove', onGateDragMove);
        document.removeEventListener('mouseup', onGateDragEnd);
        document.removeEventListener('touchmove', onGateTouchMove);
        document.removeEventListener('touchend', onGateTouchEnd);
    }

    function onGateTouchEnd() { onGateDragEnd(); }

    function saveGatesAjax() {
        const inlet = document.querySelector('.map-gate--in');
        const outlet = document.querySelector('.map-gate--out');
        if (!inlet || !outlet) return;

        const inlet_x = parseFloat(inlet.style.left);
        const inlet_y = parseFloat(inlet.style.top);
        const outlet_x = parseFloat(outlet.style.left);
        const outlet_y = parseFloat(outlet.style.top);

        showAjaxStatus('syncing', '正在同步閘門位置...');
        ajaxAction({
            action: 'update_gates',
            inlet_x: Math.round(inlet_x),
            inlet_y: Math.round(inlet_y),
            outlet_x: Math.round(outlet_x),
            outlet_y: Math.round(outlet_y)
        })
        .then(data => {
            showAjaxStatus('success', '閘門配置已儲存');
        })
        .catch(err => {
            showAjaxStatus('error', err.message);
        });
    }

    // ========== 座標同步輸入框 ==========

    function updatePosInputs(sensorId, x, y) {
        document.querySelectorAll(`.input-pos[data-sensor-id="${sensorId}"]`).forEach(input => {
            if (input.dataset.axis === 'x') input.value = x;
            if (input.dataset.axis === 'y') input.value = y;
        });
    }

    // ========== 儲存變更 (AJAX) ==========

    function saveSensorAjax(sensorId) {
        const row = document.querySelector(`.wb-row[data-sensor-id="${sensorId}"]`);
        if (!row) return;

        const nameInput = row.querySelector('.input-name');
        const typeSelect = row.querySelector('.select-type');
        const activeCheckbox = row.querySelector('.input-active');
        const xInput = row.querySelector(`.input-pos[data-axis="x"]`);
        const yInput = row.querySelector(`.input-pos[data-axis="y"]`);

        const name = nameInput ? nameInput.value.trim() : '';
        const type = typeSelect ? typeSelect.value : 'multi';
        const active = activeCheckbox ? activeCheckbox.checked : true;
        const x = xInput ? parseInt(xInput.value) || 50 : 50;
        const y = yInput ? parseInt(yInput.value) || 50 : 50;

        showAjaxStatus('syncing', '正在同步感測器變更...');

        ajaxAction({
            action: 'update_sensor',
            sensor_id: sensorId,
            sensor_name: name,
            sensor_type: type,
            x_position: x,
            y_position: y,
            is_active: active ? 'on' : 'off'
        })
        .then(data => {
            showAjaxStatus('success', '感測器配置已儲存');
            
            // 同步更新地圖上的 Pin 與 Tooltip 資訊
            const wrapper = document.querySelector(`.sensor-wrapper[data-sensor-id="${sensorId}"]`);
            if (wrapper) {
                wrapper.dataset.x = x;
                wrapper.dataset.y = y;
                wrapper.style.left = x + '%';
                wrapper.style.top = y + '%';
                wrapper.classList.toggle('tooltip-down', y < 35);

                const pin = wrapper.querySelector('.sensor-pin');
                if (pin) {
                    pin.classList.toggle('sensor-pin--off', !active);
                }

                const tooltipName = wrapper.querySelector('.tooltip-sensor-name');
                if (tooltipName && name) tooltipName.textContent = name;

                const tooltipType = wrapper.querySelector('.tooltip-type');
                if (tooltipType && typeSelect) {
                    tooltipType.textContent = typeSelect.options[typeSelect.selectedIndex].text;
                }
            }

            // 更新警戒值對象下拉選單的名稱
            if (thresholdTargetSelect) {
                const option = thresholdTargetSelect.querySelector(`option[value="${sensorId}"]`);
                if (option) {
                    const tag = option.textContent.includes('自訂警戒值') ? '自訂警戒值' : '套用預設';
                    option.textContent = `📟 感測器: ${name} (${tag})`;
                }
            }
            if (historySensorSelect) {
                const option = historySensorSelect.querySelector(`option[value="${sensorId}"]`);
                if (option) option.textContent = name;
            }
        })
        .catch(err => {
            showAjaxStatus('error', err.message);
        });
    }

    // ========== 地圖點擊新增 (AJAX) ==========

    if (pondMap) {
        pondMap.addEventListener('click', function (e) {
            if (!isEditMode) return;

            // 只有點到空白區域才新增
            const target = e.target;
            if (!target.classList.contains('map-water') &&
                !target.classList.contains('map-grid') &&
                target !== pondMap &&
                !target.closest('.map-edit-bar')) return;

            const rect = pondMap.getBoundingClientRect();
            const pctX = Math.max(2, Math.min(98, ((e.clientX - rect.left) / rect.width) * 100));
            const pctY = Math.max(2, Math.min(98, ((e.clientY - rect.top) / rect.height) * 100));

            const name = prompt('為新感測器命名：');
            if (!name || !name.trim()) return;

            showAjaxStatus('syncing', '正在新增感測器...');

            ajaxAction({
                action: 'add_sensor',
                sensor_name: name.trim(),
                sensor_type: 'multi',
                x_position: Math.round(pctX),
                y_position: Math.round(pctY),
            })
            .then(data => {
                showAjaxStatus('success', '感測器已成功建立');
                
                // 動態在前端插入感測器 Pin 與工作區行
                appendSensorToMap(data.sensor);
                appendSensorToWorkbench(data.sensor);
                updateSensorIndexes();

                // 新增至對象下拉選單與圖表篩選
                if (thresholdTargetSelect && data.sensor) {
                    const option = document.createElement('option');
                    option.value = data.sensor.id;
                    option.textContent = `📟 感測器 ${document.querySelectorAll('#pinsContainer .sensor-wrapper').length}: ${data.sensor.name} (套用預設)`;
                    thresholdTargetSelect.appendChild(option);
                    
                    // 初始化局部 thresholdsData 字典
                    thresholdsData[String(data.sensor.id)] = {
                        name: data.sensor.name,
                        is_custom: false,
                        values: JSON.parse(JSON.stringify(thresholdsData['default'].values))
                    };
                }
                if (historySensorSelect && data.sensor) {
                    const option = document.createElement('option');
                    option.value = data.sensor.id;
                    option.textContent = data.sensor.name;
                    historySensorSelect.appendChild(option);
                }
            })
            .catch(err => {
                showAjaxStatus('error', err.message);
            });
        });
    }

    function appendSensorToMap(s) {
        if (!pinsContainer) return;

        const wrapper = document.createElement('div');
        wrapper.className = 'sensor-wrapper';
        if (s.y_position < 35) {
            wrapper.classList.add('tooltip-down');
        }
        wrapper.dataset.sensorId = s.id;
        wrapper.dataset.x = s.x_position;
        wrapper.dataset.y = s.y_position;
        wrapper.style.left = s.x_position + '%';
        wrapper.style.top = s.y_position + '%';

        let metricsHtml = '<p class="tooltip-empty">尚無感測資料</p>';
        if (s.reading) {
            metricsHtml = `
                <div class="tooltip-metrics">
                    <span><i class="bi bi-thermometer-half"></i> ${parseFloat(s.reading.temperature || 0).toFixed(1)}°C</span>
                    <span><i class="bi bi-droplet"></i> pH ${parseFloat(s.reading.ph || 0).toFixed(2)}</span>
                    <span><i class="bi bi-wind"></i> DO ${parseFloat(s.reading.dissolved_oxygen || 0).toFixed(1)}</span>
                </div>
            `;
        }

        wrapper.innerHTML = `
            <button type="button"
                    class="sensor-pin sensor-pin--${s.status.tone} ${s.is_active ? '' : 'sensor-pin--off'}"
                    aria-label="感測器: ${s.name}">
                <span class="pin-pulse"></span>
                <strong class="pin-number">0</strong>
            </button>
            <div class="sensor-tooltip">
                <div class="tooltip-header">
                    <span class="tooltip-idx">0</span>
                    <strong class="tooltip-sensor-name">${s.name}</strong>
                    <span class="tooltip-type">${s.sensor_type_display}</span>
                </div>
                <div class="tooltip-body">
                    ${metricsHtml}
                </div>
                <div class="tooltip-status tooltip-status--${s.status.tone}">
                    ${s.status.label}
                </div>
            </div>
        `;

        pinsContainer.appendChild(wrapper);

        const emptyState = document.getElementById('mapEmptyState');
        if (emptyState) emptyState.style.display = 'none';

        // 重新為新產生的 Pin 綁定拖拽事件
        setupDragging();
    }

    function appendSensorToWorkbench(s) {
        if (!workbenchList) return;

        const row = document.createElement('div');
        row.className = 'wb-row';
        row.dataset.sensorId = s.id;

        const typeChoices = [
            ['multi', '多合一感測器'],
            ['do', '溶氧感測器'],
            ['ph', 'pH 感測器'],
            ['chem', '氨氮/亞硝酸鹽'],
            ['temp', '溫度感測器']
        ];
        let optionsHtml = '';
        for (const [val, label] of typeChoices) {
            optionsHtml += `<option value="${val}" ${s.sensor_type === val ? 'selected' : ''}>${label}</option>`;
        }

        const postUrl = window.location.origin + '/water/api/upload/';

        row.innerHTML = `
            <div class="wb-main">
                <span class="wb-idx">0</span>
                <div class="wb-info">
                    <input type="text" class="input-name input-wb-field" value="${s.name}"
                           data-sensor-id="${s.id}" placeholder="感測器名稱" required>
                    <select class="select-type input-wb-field" data-sensor-id="${s.id}">
                        ${optionsHtml}
                    </select>
                    <div class="sensor-api-info" style="font-size: 0.85rem; color: var(--text-2); margin-top: 6px; border-top: 1px dashed rgba(15,118,110,0.12); padding-top: 6px; line-height: 1.5;">
                        <div style="font-weight: 700; color: var(--primary); display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 4px;">
                            <span>🔑 上傳金鑰 (secret_token)</span>
                            <button type="button" class="btn-regenerate-token btn-regenerate-token--wb" data-sensor-id="${s.id}" style="background: #0f766e; color: #fff; border: none; padding: 2px 8px; border-radius: 4px; font-size: 0.72rem; font-weight: 700; cursor: pointer; transition: background 150ms;">
                                <i class="bi bi-arrow-clockwise"></i> 重刷
                            </button>
                        </div>
                        <code class="api-token-display" style="background: rgba(15,118,110,0.06); padding: 2px 6px; border-radius: 4px; font-weight: 700; color: #0f766e; display: block; width: fit-content; margin: 4px 0; user-select: all; font-family: monospace;">${s.secret_token}</code>
                        <div style="font-weight: 700; color: var(--primary);">📮 POST URL</div>
                        <code style="background: rgba(15,118,110,0.06); padding: 2px 6px; border-radius: 4px; color: #334155; display: block; font-size: 0.75rem; word-break: break-all; user-select: all; font-family: monospace; margin: 4px 0;">${postUrl}</code>
                        
                        <details class="sensor-post-details" style="margin-top: 8px; border-top: 1px dashed rgba(15,118,110,0.12); padding-top: 6px; cursor: pointer;">
                            <summary style="font-size: 0.8rem; font-weight: 700; color: var(--primary); outline: none;">📋 檢視 API POST 說明與 JSON 範例</summary>
                            <div style="font-size: 0.78rem; color: var(--text-2); background: rgba(15, 118, 110, 0.04); border-radius: 6px; padding: 8px; margin-top: 6px; line-height: 1.45; cursor: default;" onclick="event.stopPropagation();">
                                <p style="margin: 0 0 6px 0; font-weight: 700;"><i class="bi bi-info-circle"></i> 請使用 <strong>HTTP POST</strong> 方法發送資料：</p>
                                <div style="margin-bottom: 6px;">
                                    <strong>Headers:</strong>
                                    <code style="display: block; background: rgba(0,0,0,0.04); padding: 2px 6px; border-radius: 4px; font-family: monospace; font-size: 0.72rem; margin-top: 2px;">Content-Type: application/json</code>
                                </div>
                                <div>
                                    <strong>JSON Payload:</strong>
                                    <pre class="api-json-display" style="margin: 4px 0 0 0; background: rgba(0,0,0,0.04); padding: 8px; border-radius: 4px; font-family: monospace; font-size: 0.72rem; overflow-x: auto; line-height: 1.25; color: #0d5f58;">{
  "secret_token": "${s.secret_token}",
  "temperature": 26.5,
  "ph": 7.8,
  "dissolved_oxygen": 6.2,
  "salinity": 15.0
}</pre>
                                </div>
                            </div>
                        </details>
                    </div>
                </div>
                <div class="wb-active-control">
                    <label class="checkbox-container">
                        <input type="checkbox" class="input-active input-wb-field" data-sensor-id="${s.id}"
                               ${s.is_active ? 'checked' : ''}>
                        <span class="checkmark"></span>
                        <span class="checkbox-label">啟用</span>
                    </label>
                </div>
            </div>
            <div class="wb-edit">
                <div class="wb-pos">
                    <label>X</label>
                    <input type="number" class="input-pos input-wb-field" value="${s.x_position}"
                           data-sensor-id="${s.id}" data-axis="x"
                           min="0" max="100">
                    <label>Y</label>
                    <input type="number" class="input-pos input-wb-field" value="${s.y_position}"
                           data-sensor-id="${s.id}" data-axis="y"
                           min="0" max="100">
                </div>
                <button type="button" class="btn-delete-sensor" data-sensor-id="${s.id}" title="刪除">
                    <i class="bi bi-trash3"></i>
                </button>
            </div>
        `;

        workbenchList.appendChild(row);

        const emptyState = document.getElementById('workbenchEmptyState');
        if (emptyState) emptyState.style.display = 'none';
    }

    function updateSensorIndexes() {
        const pins = document.querySelectorAll('#pinsContainer .sensor-wrapper');
        pins.forEach((pin, idx) => {
            const num = idx + 1;
            const numberEl = pin.querySelector('.pin-number');
            const tooltipIdxEl = pin.querySelector('.tooltip-idx');
            if (numberEl) numberEl.textContent = num;
            if (tooltipIdxEl) tooltipIdxEl.textContent = num;
        });

        const rows = document.querySelectorAll('#workbenchList .wb-row');
        rows.forEach((row, idx) => {
            const num = idx + 1;
            const idxEl = row.querySelector('.wb-idx');
            if (idxEl) idxEl.textContent = num;
        });

        if (pins.length === 0) {
            const mapEmpty = document.getElementById('mapEmptyState');
            if (mapEmpty) mapEmpty.style.display = 'flex';
            const wbEmpty = document.getElementById('workbenchEmptyState');
            if (wbEmpty) wbEmpty.style.display = 'block';
        }
    }

    // ========== 欄位即時編輯與雙向連動 ==========

    document.addEventListener('change', function (e) {
        const field = e.target.closest('.input-wb-field');
        if (!field) return;

        const sensorId = field.dataset.sensorId;
        if (!sensorId) return;

        // 如果是 X 或 Y 欄位，即時更新地圖上的 Pin 位置
        if (field.classList.contains('input-pos')) {
            const row = document.querySelector(`.wb-row[data-sensor-id="${sensorId}"]`);
            if (row) {
                const xInput = row.querySelector('.input-pos[data-axis="x"]');
                const yInput = row.querySelector('.input-pos[data-axis="y"]');
                const x = Math.max(0, Math.min(100, parseInt(xInput.value) || 50));
                const y = Math.max(0, Math.min(100, parseInt(yInput.value) || 50));
                
                // 修正輸入框的值防止溢出
                xInput.value = x;
                yInput.value = y;

                const wrapper = document.querySelector(`.sensor-wrapper[data-sensor-id="${sensorId}"]`);
                if (wrapper) {
                    wrapper.style.left = x + '%';
                    wrapper.style.top = y + '%';
                }
            }
        }

        saveSensorAjax(sensorId);
    });

    // ========== 刪除感測器 (AJAX) ==========

    document.addEventListener('click', function (e) {
        const btn = e.target.closest('.btn-delete-sensor');
        if (!btn) return;

        const sensorId = btn.dataset.sensorId;
        if (!confirm('確認刪除此感測器？')) return;

        showAjaxStatus('syncing', '正在刪除感測器...');

        ajaxAction({
            action: 'delete_sensor',
            sensor_id: sensorId,
        })
        .then(data => {
            showAjaxStatus('success', '感測器已成功刪除');

            // 從 DOM 中移除 Pin 與工作區行
            const wrapper = document.querySelector(`.sensor-wrapper[data-sensor-id="${sensorId}"]`);
            if (wrapper) wrapper.remove();

            const row = document.querySelector(`.wb-row[data-sensor-id="${sensorId}"]`);
            if (row) row.remove();

            // 從下拉選單與圖表過濾中移除
            if (thresholdTargetSelect) {
                const option = thresholdTargetSelect.querySelector(`option[value="${sensorId}"]`);
                if (option) option.remove();
                delete thresholdsData[sensorId];
                
                // 若剛好選中被刪除的感測器，切回預設
                if (thresholdTargetSelect.value === sensorId) {
                    thresholdTargetSelect.value = 'default';
                    thresholdTargetSelect.dispatchEvent(new Event('change'));
                }
            }
            if (historySensorSelect) {
                const option = historySensorSelect.querySelector(`option[value="${sensorId}"]`);
                if (option) option.remove();
                if (historySensorSelect.value === sensorId) {
                    historySensorSelect.value = 'all';
                    historySensorSelect.dispatchEvent(new Event('change'));
                }
            }

            // 重新整理序號與空狀態
            updateSensorIndexes();
        })
        .catch(err => {
            showAjaxStatus('error', err.message);
        });
    });


    // ========== 重新產生金鑰 (AJAX) ==========

    document.addEventListener('click', function (e) {
        const btn = e.target.closest('.btn-regenerate-token');
        if (!btn) return;

        const sensorId = btn.dataset.sensorId;
        if (!sensorId) return;

        if (!confirm('確認要重刷此感測器的上傳金鑰 (secret_token) 嗎？\n舊金鑰將立即失效，硬體發送端也必須同步更新！')) return;

        showAjaxStatus('syncing', '正在重刷上傳金鑰...');

        ajaxAction({
            action: 'regenerate_token',
            sensor_id: sensorId,
        })
        .then(data => {
            showAjaxStatus('success', '上傳金鑰已成功更新');

            const newToken = data.sensor.secret_token;

            // 1. 更新 Workbench 顯示的金鑰與 JSON 範例
            const row = document.querySelector(`.wb-row[data-sensor-id="${sensorId}"]`);
            if (row) {
                const tokenCode = row.querySelector('.api-token-display');
                if (tokenCode) tokenCode.textContent = newToken;

                const jsonPre = row.querySelector('.api-json-display');
                if (jsonPre) {
                    jsonPre.textContent = `{
  "secret_token": "${newToken}",
  "temperature": 26.5,
  "ph": 7.8,
  "dissolved_oxygen": 6.2,
  "salinity": 15.0
}`;
                }
            }

            // 2. 更新感測器大卡片 API info 顯示的金鑰與 JSON 範例
            const card = document.querySelector(`.sensor-metric-card .btn-regenerate-token[data-sensor-id="${sensorId}"]`);
            if (card) {
                const cardBox = card.closest('.sensor-card-api-box');
                if (cardBox) {
                    const tokenCode = cardBox.querySelector('.api-token-display');
                    if (tokenCode) tokenCode.textContent = newToken;

                    const jsonPre = cardBox.querySelector('.api-json-display');
                    if (jsonPre) {
                        jsonPre.textContent = `{
  "secret_token": "${newToken}",
  "temperature": 26.5,
  "ph": 7.8,
  "dissolved_oxygen": 6.2,
  "salinity": 15.0
}`;
                    }
                }
            }
        })
        .catch(err => {
            showAjaxStatus('error', err.message);
        });
    });


    // ========== 警戒值編輯對象切換 ==========

    if (thresholdTargetSelect) {
        thresholdTargetSelect.addEventListener('change', function () {
            const target = this.value;
            if (formTargetSensorId) formTargetSensorId.value = target;

            const targetData = thresholdsData[target];
            if (targetData) {
                // 填充對應的數值到輸入框
                for (const [key, val] of Object.entries(targetData.values)) {
                    const minInput = document.getElementById(`input_${key}_min`);
                    const maxInput = document.getElementById(`input_${key}_max`);
                    if (minInput) minInput.value = val.min !== null && val.min !== undefined ? val.min : '';
                    if (maxInput) maxInput.value = val.max !== null && val.max !== undefined ? val.max : '';
                }

                // 更新 Badge 與還原預設按鈕
                if (target === 'default') {
                    if (thresholdStatusBadge) {
                        thresholdStatusBadge.textContent = '套用池區預設';
                        thresholdStatusBadge.classList.remove('is-custom');
                    }
                    if (btnRestoreThresholds) btnRestoreThresholds.style.display = 'none';
                } else {
                    if (targetData.is_custom) {
                        if (thresholdStatusBadge) {
                            thresholdStatusBadge.textContent = '個別感測器自訂';
                            thresholdStatusBadge.classList.add('is-custom');
                        }
                        if (btnRestoreThresholds) btnRestoreThresholds.style.display = 'inline-flex';
                    } else {
                        if (thresholdStatusBadge) {
                            thresholdStatusBadge.textContent = '套用池區預設';
                            thresholdStatusBadge.classList.remove('is-custom');
                        }
                        if (btnRestoreThresholds) btnRestoreThresholds.style.display = 'none';
                    }
                }
            }
        });
    }

    // 還原為池區預設警戒值 (一鍵重設)
    if (btnRestoreThresholds) {
        btnRestoreThresholds.addEventListener('click', function () {
            const target = thresholdTargetSelect ? thresholdTargetSelect.value : 'default';
            if (target === 'default') return;

            if (!confirm('確認要將此感測器的警戒值改為標準警戒值嗎？')) return;

            showAjaxStatus('syncing', '正在修改警戒值...');
            ajaxAction({
                action: 'delete_custom_thresholds',
                sensor_id: target
            })
            .then(data => {
                showAjaxStatus('success', '已成功改為標準警戒值');

                // 本地資料同步為 default 值
                thresholdsData[target].is_custom = false;
                thresholdsData[target].values = JSON.parse(JSON.stringify(thresholdsData['default'].values));

                // 重新派發 change 事件更新 UI 輸入框與 Badge
                if (thresholdTargetSelect) thresholdTargetSelect.dispatchEvent(new Event('change'));

                // 更新下拉選單的選項顯示文字
                const option = thresholdTargetSelect.querySelector(`option[value="${target}"]`);
                if (option) {
                    option.textContent = option.textContent.replace('自訂警戒值', '套用預設');
                }
            })
            .catch(err => {
                showAjaxStatus('error', err.message);
            });
        });
    }

    // 警戒值表單 AJAX 送出
    if (thresholdsForm) {
        thresholdsForm.addEventListener('submit', function (e) {
            e.preventDefault();
            const target = thresholdTargetSelect ? thresholdTargetSelect.value : 'default';

            const payload = {
                action: 'save_thresholds',
                sensor_id: target
            };

            const inputs = thresholdsForm.querySelectorAll('.input-threshold');
            inputs.forEach(input => {
                payload[input.name] = input.value;
            });

            showAjaxStatus('syncing', '正在儲存警戒值...');
            ajaxAction(payload)
            .then(data => {
                showAjaxStatus('success', '警戒值已儲存');

                // 同步更新本地 thresholdsData 字典
                if (target !== 'default') {
                    thresholdsData[target].is_custom = true;
                }

                for (const key of Object.keys(thresholdsData[target].values)) {
                    const minVal = document.getElementById(`input_${key}_min`).value;
                    const maxVal = document.getElementById(`input_${key}_max`).value;
                    thresholdsData[target].values[key] = {
                        min: minVal !== '' ? parseFloat(minVal) : null,
                        max: maxVal !== '' ? parseFloat(maxVal) : null
                    };
                }

                // 刷新 UI 的 Badge 與選項文字
                if (thresholdTargetSelect) thresholdTargetSelect.dispatchEvent(new Event('change'));

                if (target !== 'default' && thresholdTargetSelect) {
                    const option = thresholdTargetSelect.querySelector(`option[value="${target}"]`);
                    if (option && option.textContent.includes('套用預設')) {
                        option.textContent = option.textContent.replace('套用預設', '自訂警戒值');
                    }
                }
            })
            .catch(err => {
                showAjaxStatus('error', err.message);
            });
        });
    }


    // ========== 歷史數據圖表與表格 (Chart.js) ==========

    let historyChart = null;

    function initHistoryChart() {
        const ctx = document.getElementById('historyChart');
        if (!ctx) return;

        historyChart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: [],
                datasets: [{
                    label: '',
                    data: [],
                    borderColor: '#0f766e',
                    backgroundColor: 'rgba(15, 118, 110, 0.04)',
                    borderWidth: 2.5,
                    tension: 0.2,
                    fill: true,
                    pointBackgroundColor: '#0f766e',
                    pointBorderColor: '#ffffff',
                    pointBorderWidth: 1.5,
                    pointRadius: 4.5,
                    pointHoverRadius: 7
                }]
            },
            options: {
                animation: false,
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: false
                    },
                    tooltip: {
                        mode: 'index',
                        intersect: false,
                        padding: 12,
                        backgroundColor: 'rgba(17, 37, 34, 0.95)',
                        titleColor: '#fff',
                        titleFont: { size: 12, weight: 'bold' },
                        bodyColor: '#e0f2fe',
                        bodyFont: { size: 12 },
                        borderColor: 'rgba(15, 118, 110, 0.3)',
                        borderWidth: 1,
                        displayColors: false
                    }
                },
                scales: {
                    x: {
                        grid: {
                            color: 'rgba(15, 118, 110, 0.04)'
                        },
                        ticks: {
                            font: { size: 10, weight: '600' },
                            color: '#627974'
                        }
                    },
                    y: {
                        grid: {
                            color: 'rgba(15, 118, 110, 0.04)'
                        },
                        ticks: {
                            font: { size: 10, weight: '600' },
                            color: '#627974'
                        }
                    }
                }
            }
        });
    }

    function fetchHistoryData() {
        if (!historySensorSelect || !historyMetricSelect || !historyTimeSelect) return;

        const sensorId = historySensorSelect.value;
        const metricKey = historyMetricSelect.value;
        const timeRange = historyTimeSelect.value;

        let start_date = '';
        let end_date = '';
        if (customDateContainer) {
            if (timeRange === 'custom') {
                customDateContainer.style.display = 'inline-flex';
                if (historyStartDate) start_date = historyStartDate.value;
                if (historyEndDate) end_date = historyEndDate.value;
            } else {
                customDateContainer.style.display = 'none';
            }
        }

        let queryParams = `sensor_id=${sensorId}&time_range=${timeRange}`;
        if (timeRange === 'custom') {
            queryParams += `&start_date=${start_date}&end_date=${end_date}`;
        }

        // 動態刷新 CSV 匯出下載網址
        if (btnExportCSV) {
            const baseUrl = window.location.pathname.replace(/\/$/, '') + '/export-csv/';
            btnExportCSV.href = `${baseUrl}?${queryParams}`;
        }

        const apiUrl = window.location.pathname.replace(/\/$/, '') + '/history/';
        const fetchUrl = `${apiUrl}?${queryParams}`;

        fetch(fetchUrl)
        .then(response => {
            if (!response.ok) throw new Error('撈取歷史數據錯誤');
            return response.json();
        })
        .then(res => {
            if (res.status === 'success') {
                updateHistoryUI(res.data, metricKey);
            }
        })
        .catch(err => {
            console.error('Fetch history error:', err);
        });
    }

    function updateHistoryUI(data, metricKey) {
        if (!historyTableBody) return;
        historyTableBody.innerHTML = '';

        if (data.length === 0) {
            if (chartEmptyState) chartEmptyState.style.display = 'flex';
            if (historyChart) {
                historyChart.data.labels = [];
                historyChart.data.datasets[0].data = [];
                historyChart.update();
            }
            historyTableBody.innerHTML = `<tr><td colspan="8" style="text-align: center; color: var(--muted); font-style: italic; padding: 36px 0;">該時間區段與篩選條件下尚無檢測數據</td></tr>`;
            return;
        }

        if (chartEmptyState) chartEmptyState.style.display = 'none';

        // 畫布資料需要時間由舊到新排序
        const chartData = [...data].reverse();
        const timeRange = historyTimeSelect ? historyTimeSelect.value : '7d';
        const labels = chartData.map(d => {
            const date = new Date(d.measured_at);
            if (timeRange === '24h') {
                return `${String(date.getHours()).padStart(2, '0')}:${String(date.getMinutes()).padStart(2, '0')}`;
            } else {
                return `${date.getMonth() + 1}/${date.getDate()} ${String(date.getHours()).padStart(2, '0')}:${String(date.getMinutes()).padStart(2, '0')}`;
            }
        });
        const values = chartData.map(d => d[metricKey]);

        // 更新 Chart.js 設定
        if (historyChart) {
            const metricOpts = {
                dissolved_oxygen: { label: '溶氧量 (mg/L)', color: '#0ea5e9' },
                ph: { label: 'pH 值', color: '#10b981' },
                temperature: { label: '溫度 (°C)', color: '#ef4444' },
                ammonia_nitrogen: { label: '氨氮 (mg/L)', color: '#f59e0b' },
                nitrite: { label: '亞硝酸鹽 (mg/L)', color: '#8b5cf6' },
                stability_index: { label: '穩定度 (%)', color: '#0f766e' }
            };

            const opt = metricOpts[metricKey] || { label: '數值', color: '#0f766e' };
            historyChart.data.labels = labels;
            historyChart.data.datasets[0].label = opt.label;
            historyChart.data.datasets[0].data = values;
            historyChart.data.datasets[0].borderColor = opt.color;
            historyChart.data.datasets[0].pointBackgroundColor = opt.color;
            historyChart.data.datasets[0].backgroundColor = opt.color + '0A'; // opacity 0.04
            historyChart.update();
        }

        // 填充表格 (保持最新數據在最上方，即原本 data 的順序)
        data.forEach(row => {
            const tr = document.createElement('tr');
            tr.innerHTML = `
                <td>${row.measured_at}</td>
                <td><span class="threshold-status-badge">${row.sensor_name}</span></td>
                <td>${row.temperature !== null && row.temperature !== undefined ? row.temperature.toFixed(1) + ' °C' : '–'}</td>
                <td>${row.ph !== null && row.ph !== undefined ? row.ph.toFixed(2) : '–'}</td>
                <td>${row.dissolved_oxygen !== null && row.dissolved_oxygen !== undefined ? row.dissolved_oxygen.toFixed(1) + ' mg/L' : '–'}</td>
                <td>${row.ammonia_nitrogen !== null && row.ammonia_nitrogen !== undefined ? row.ammonia_nitrogen.toFixed(3) + ' mg/L' : '–'}</td>
                <td>${row.nitrite !== null && row.nitrite !== undefined ? row.nitrite.toFixed(3) + ' mg/L' : '–'}</td>
                <td>${row.salinity !== null && row.salinity !== undefined ? row.salinity.toFixed(1) + ' ppt' : '–'}</td>
            `;
            historyTableBody.appendChild(tr);
        });
    }

    if (historySensorSelect) historySensorSelect.addEventListener('change', fetchHistoryData);
    if (historyMetricSelect) historyMetricSelect.addEventListener('change', fetchHistoryData);
    if (historyTimeSelect) historyTimeSelect.addEventListener('change', fetchHistoryData);
    if (historyStartDate) historyStartDate.addEventListener('change', fetchHistoryData);
    if (historyEndDate) historyEndDate.addEventListener('change', fetchHistoryData);

    // 隨機產生測試數據
    if (btnGenerateMock) {
        btnGenerateMock.addEventListener('click', function () {
            const generateUrl = window.location.pathname.replace(/\/$/, '') + '/generate-mock-readings/';
            showAjaxStatus('syncing', '正在產生測試數據...');

            fetch(generateUrl, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': getCookie('csrftoken')
                }
            })
            .then(response => response.json())
            .then(res => {
                if (res.status === 'success') {
                    showAjaxStatus('success', res.message);
                    fetchHistoryData(); // 自動重載歷史圖表表格
                } else {
                    showAjaxStatus('error', res.message);
                }
            })
            .catch(err => {
                showAjaxStatus('error', '發送請求失敗，請重試');
            });
        });
    }


    // ========== MutationObserver ==========

    if (pondMap) {
        const observer = new MutationObserver(setupDragging);
        observer.observe(pondMap, { childList: true, subtree: true });
    }

    // ========== 初始化 ==========

    setupDragging();
    updateSensorIndexes();
    initHistoryChart();
    fetchHistoryData();

    // 預設觸發一次警戒值對象選擇，渲染預設數值
    if (thresholdTargetSelect) {
        thresholdTargetSelect.dispatchEvent(new Event('change'));
    }

    // 30 秒自動重新整理頁面以撈取最新數據 (僅在非編輯且無 Modal 時觸發)
    setInterval(function() {
        if (!isEditMode && !document.querySelector('.modal.show')) {
            let url = new URL(window.location.href);
            url.searchParams.set('refresh', 'true');
            window.location.href = url.toString();
        }
    }, 30000);
})();
