/**
 * pond_list.js
 * 池區列表頁面的互動功能
 * - 卡片悸動效果
 * - 狀態顏色提示
 */

document.addEventListener('DOMContentLoaded', function() {
    const pondCards = document.querySelectorAll('.pond-card');
    
    // 添加卡片懸停效果（已通過CSS實現，這裡可擴展JavaScript互動）
    pondCards.forEach(card => {
        // 可添加更多互動效果
        card.addEventListener('mouseenter', function() {
            // 例如：播放微妙的動畫
        });
    });

    // 刪除確認
    const deleteButtons = document.querySelectorAll('.btn-delete');
    deleteButtons.forEach(btn => {
        btn.addEventListener('click', function(e) {
            const pondName = this.closest('.pond-card').querySelector('.card-title').textContent;
            if (!confirm(`確認刪除魚池 "${pondName}" 嗎？此操作無法復原。`)) {
                e.preventDefault();
                return false;
            }
        });
    });
});
