(function () {
    var lightbox = document.getElementById('guide-lightbox');
    var stage = document.getElementById('lightbox-stage');
    var img = document.getElementById('lightbox-img');

    var scale = 1;
    var posX = 0, posY = 0;
    var STEP = 0.5;
    var MIN = 1, MAX = 8;

    function applyTransform(animate) {
        if (!animate) img.style.transition = 'none';
        else img.style.transition = 'transform 0.15s ease';
        img.style.transform = 'translate(' + posX + 'px, ' + posY + 'px) scale(' + scale + ')';
        stage.style.cursor = 'pointer';
    }
    function clampPos() {
        // 限制拖移範圍不超出圖片邊界
        var rect = img.getBoundingClientRect();
        var stageRect = stage.getBoundingClientRect();
        var maxX = Math.max(0, (rect.width - stageRect.width) / 2);
        var maxY = Math.max(0, (rect.height - stageRect.height) / 2);
        posX = Math.min(maxX, Math.max(-maxX, posX));
        posY = Math.min(maxY, Math.max(-maxY, posY));
    }

    window.resetTransform = function () {
        scale = 1; posX = 0; posY = 0;
        img.style.cursor = 'zoom-in';
        stage.style.cursor = 'pointer';
        applyTransform(true);
    };

    window.zoomIn = function () {
        scale = Math.min(scale + STEP, MAX);
        clampPos();
        applyTransform(true);
    };

    window.zoomOut = function () {
        scale = Math.max(scale - STEP, MIN);
        if (scale === MIN) { posX = 0; posY = 0; }
        clampPos();
        applyTransform(true);
    };

    window.openLightbox = function (src, caption) {
        img.src = src;
        document.getElementById('lightbox-caption').textContent = caption;
        lightbox.classList.add('open');
        document.body.style.overflow = 'hidden';
        resetTransform();
    };

    window.closeLightbox = function () {
        lightbox.classList.remove('open');
        document.body.style.overflow = '';
        resetTransform();
    };

    // 點背景關閉
    lightbox.addEventListener('click', function (e) {
        if (e.target === lightbox || e.target === stage) closeLightbox();
    });

    img.addEventListener('click', function (e) {
        e.stopPropagation();
    });
    // 雙擊放大/還原
    img.addEventListener('dblclick', function (e) {
        if (scale > 1) {
            resetTransform();
        } else {
            scale = 2.5;
            applyTransform(true);
        }
        e.stopPropagation();
    });

    // 滑鼠拖移
    var isDragging = false, dragStartX = 0, dragStartY = 0;

    img.addEventListener('mousedown', function (e) {
        if (scale <= 1) return;
        isDragging = true;
        dragStartX = e.clientX - posX;
        dragStartY = e.clientY - posY;
        img.classList.add('dragging');
        e.preventDefault();
    });

    document.addEventListener('mousemove', function (e) {
        if (!isDragging) return;
        posX = e.clientX - dragStartX;
        posY = e.clientY - dragStartY;
        clampPos();
        applyTransform(false);
    });

    document.addEventListener('mouseup', function () {
        if (!isDragging) return;
        isDragging = false;
        img.classList.remove('dragging');
        img.style.cursor = scale > 1 ? 'grab' : 'default';
    });

    // 滾輪縮放（以游標位置為中心）
    stage.addEventListener('wheel', function (e) {
        e.preventDefault();
        var delta = e.deltaY > 0 ? -0.15 : 0.15;
        var newScale = Math.min(Math.max(scale + delta, MIN), MAX);
        if (newScale === scale) return;

        var rect = img.getBoundingClientRect();
        var offsetX = e.clientX - (rect.left + rect.width / 2);
        var offsetY = e.clientY - (rect.top + rect.height / 2);

        posX += offsetX * (1 - newScale / scale);
        posY += offsetY * (1 - newScale / scale);
        scale = newScale;

        if (scale <= MIN) { posX = 0; posY = 0; }
        clampPos();
        applyTransform(false);
    }, { passive: false });

    // 手機捏合縮放
    var initDist = 0, initScale = 1;
    var initMidX = 0, initMidY = 0, initPosX = 0, initPosY = 0;
    var touch1Start = {}, touch2Start = {};

    img.addEventListener('touchstart', function (e) {
        if (e.touches.length === 2) {
            initDist = Math.hypot(
                e.touches[0].clientX - e.touches[1].clientX,
                e.touches[0].clientY - e.touches[1].clientY
            );
            initScale = scale;
            initMidX = (e.touches[0].clientX + e.touches[1].clientX) / 2;
            initMidY = (e.touches[0].clientY + e.touches[1].clientY) / 2;
            initPosX = posX;
            initPosY = posY;
        } else if (e.touches.length === 1 && scale > 1) {
            isDragging = true;
            dragStartX = e.touches[0].clientX - posX;
            dragStartY = e.touches[0].clientY - posY;
        }
        e.stopPropagation();
    }, { passive: true });

    img.addEventListener('touchmove', function (e) {
        if (e.touches.length === 2) {
            var dist = Math.hypot(
                e.touches[0].clientX - e.touches[1].clientX,
                e.touches[0].clientY - e.touches[1].clientY
            );
            scale = Math.min(Math.max(initScale * (dist / initDist), MIN), MAX);
            clampPos();
            applyTransform(false);
        } else if (e.touches.length === 1 && isDragging) {
            posX = e.touches[0].clientX - dragStartX;
            posY = e.touches[0].clientY - dragStartY;
            clampPos();
            applyTransform(false);
        }
        e.stopPropagation();
    }, { passive: true });

    img.addEventListener('touchend', function (e) {
        isDragging = false;
        if (scale <= MIN) resetTransform();
        e.stopPropagation();
    }, { passive: true });

    // ESC 關閉
    document.addEventListener('keydown', function (e) {
        if (!lightbox.classList.contains('open')) return;
        if (e.key === 'Escape') closeLightbox();
        if (e.key === '+' || e.key === '=') zoomIn();
        if (e.key === '-') zoomOut();
        if (e.key === '0') resetTransform();
    });
})();