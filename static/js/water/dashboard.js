/**
 * Water Dashboard Interactive Features
 * - Edit mode toggle
 * - Map-based sensor adding and dragging
 * - Sensor position sync
 */

document.addEventListener('DOMContentLoaded', function() {
    const pondMap = document.getElementById('pondMap');
    const btnEditMode = document.getElementById('btnEditMode');
    const mapEditHint = document.getElementById('mapEditHint');
    const sensorWorkbench = document.getElementById('sensorWorkbench');
    
    let isEditMode = false;
    let draggedSensor = null;
    let dragOffset = { x: 0, y: 0 };

    // ===== EDIT MODE TOGGLE =====
    if (btnEditMode) {
        btnEditMode.addEventListener('click', function() {
            isEditMode = !isEditMode;
            btnEditMode.classList.toggle('active', isEditMode);
            pondMap.classList.toggle('edit-mode', isEditMode);
            mapEditHint.style.display = isEditMode ? 'block' : 'none';
        });
    }

    // ===== MAP CLICK TO ADD SENSOR =====
    if (pondMap) {
        pondMap.addEventListener('click', function(e) {
            if (!isEditMode || e.target !== pondMap) return;
            
            const rect = pondMap.getBoundingClientRect();
            const x = ((e.clientX - rect.left) / rect.width) * 100;
            const y = ((e.clientY - rect.top) / rect.height) * 100;
            
            // Clamp to valid range
            const clampX = Math.max(5, Math.min(95, x));
            const clampY = Math.max(5, Math.min(95, y));
            
            // Create form and submit to add sensor
            addSensorAtPosition(clampX, clampY);
        });
    }

    // ===== SENSOR DRAGGING =====
    function setupSensorDragging() {
        const sensors = pondMap.querySelectorAll('.sensor-pin');
        
        sensors.forEach(sensor => {
            sensor.addEventListener('mousedown', function(e) {
                if (!isEditMode) return;
                
                e.preventDefault();
                draggedSensor = sensor;
                
                const rect = pondMap.getBoundingClientRect();
                const sensorRect = sensor.getBoundingClientRect();
                
                dragOffset.x = e.clientX - sensorRect.left;
                dragOffset.y = e.clientY - sensorRect.top;
                
                sensor.classList.add('dragging');
                document.addEventListener('mousemove', onDragMove);
                document.addEventListener('mouseup', onDragEnd);
            });
        });
    }

    function onDragMove(e) {
        if (!draggedSensor) return;
        
        const rect = pondMap.getBoundingClientRect();
        let x = ((e.clientX - rect.left - dragOffset.x + 21) / rect.width) * 100;
        let y = ((e.clientY - rect.top - dragOffset.y + 21) / rect.height) * 100;
        
        x = Math.max(0, Math.min(100, x));
        y = Math.max(0, Math.min(100, y));
        
        draggedSensor.style.left = x + '%';
        draggedSensor.style.top = y + '%';
        
        // Update table inputs in real-time
        const sensorId = draggedSensor.closest('.sensor-wrapper')?.dataset.sensorId;
        if (sensorId) {
            const row = document.querySelector(`.sensor-row[data-sensor-id="${sensorId}"]`);
            if (row) {
                row.querySelector('.input-pos-x').value = Math.round(x);
                row.querySelector('.input-pos-y').value = Math.round(y);
            }
        }
    }

    function onDragEnd() {
        if (draggedSensor) {
            draggedSensor.classList.remove('dragging');
            
            // Auto-save on drag end
            const sensorId = draggedSensor.closest('.sensor-wrapper')?.dataset.sensorId;
            if (sensorId) {
                const row = document.querySelector(`.sensor-row[data-sensor-id="${sensorId}"]`);
                if (row && row.querySelector('.btn-save-row')) {
                    // Optionally auto-save: row.querySelector('.btn-save-row').click();
                }
            }
        }
        
        draggedSensor = null;
        document.removeEventListener('mousemove', onDragMove);
        document.removeEventListener('mouseup', onDragEnd);
    }

    // ===== DELETE SENSOR =====
    document.querySelectorAll('.btn-delete-sensor').forEach(btn => {
        btn.addEventListener('click', function(e) {
            e.preventDefault();
            
            if (confirm('確定刪除此感測器？')) {
                const sensorId = this.dataset.sensorId;
                const form = this.closest('.sensor-row');
                
                // Create hidden form to delete
                const deleteForm = document.createElement('form');
                deleteForm.method = 'POST';
                deleteForm.innerHTML = `
                    ${document.querySelector('[name="csrfmiddlewaretoken"]').outerHTML}
                    <input type="hidden" name="action" value="delete_sensor">
                    <input type="hidden" name="pond_id" value="${form.querySelector('[name="pond_id"]').value}">
                    <input type="hidden" name="sensor_id" value="${sensorId}">
                `;
                document.body.appendChild(deleteForm);
                deleteForm.submit();
            }
        });
    });

    // ===== INPUT SYNC: TABLE TO MAP =====
    document.querySelectorAll('.input-pos-x, .input-pos-y').forEach(input => {
        input.addEventListener('change', function() {
            const row = this.closest('.sensor-row');
            if (!row) return;
            
            const sensorId = row.dataset.sensorId;
            const x = row.querySelector('.input-pos-x').value;
            const y = row.querySelector('.input-pos-y').value;
            
            const sensorPin = pondMap.querySelector(`.sensor-wrapper[data-sensor-id="${sensorId}"] .sensor-pin`);
            if (sensorPin) {
                sensorPin.style.left = x + '%';
                sensorPin.style.top = y + '%';
            }
        });
    });

    // ===== HELPER FUNCTIONS =====
    function addSensorAtPosition(x, y) {
        // Create and submit form to add sensor
        const form = document.createElement('form');
        form.method = 'POST';
        form.innerHTML = `
            ${document.querySelector('[name="csrfmiddlewaretoken"]').outerHTML}
            <input type="hidden" name="action" value="add_sensor">
            <input type="hidden" name="pond_id" value="${document.querySelector('[name="pond_id"]')?.value || ''}">
            <input type="hidden" name="sensor_name" value="感測器 ${Date.now()}">
            <input type="hidden" name="sensor_type" value="multi">
            <input type="hidden" name="x_position" value="${Math.round(x)}">
            <input type="hidden" name="y_position" value="${Math.round(y)}">
        `;
        document.body.appendChild(form);
        form.submit();
    }

    // Initial setup
    setupSensorDragging();

    // Re-setup after any form submission that reloads
    const observer = new MutationObserver(function() {
        setupSensorDragging();
    });
    
    if (pondMap) {
        observer.observe(pondMap, { childList: true, subtree: true });
    }
});
