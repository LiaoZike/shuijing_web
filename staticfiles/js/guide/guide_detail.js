(function () {
    var lightbox = document.getElementById('guide-lightbox');
    var stage = document.getElementById('lightbox-stage');
    var viewport = document.getElementById('lightbox-viewport');
    var media = document.getElementById('lightbox-media');
    var img = document.getElementById('lightbox-img');
    var captionEl = document.getElementById('lightbox-caption');

    var scale = 1;
    var posX = 0;
    var posY = 0;

    var STEP = 0.35;
    var MIN = 1;
    var MAX = 8;

    var baseWidth = 0;
    var baseHeight = 0;

    function getStageSize() {
        var rect = viewport.getBoundingClientRect();
        return {
            width: rect.width,
            height: rect.height
        };
    }

    function computeFitSize(naturalWidth, naturalHeight) {
        var stageSize = getStageSize();

        // 預留一點邊距，避免貼滿太死
        var maxW = stageSize.width * 0.96;
        var maxH = stageSize.height * 0.96;

        var ratio = Math.min(maxW / naturalWidth, maxH / naturalHeight);

        return {
            width: naturalWidth * ratio,
            height: naturalHeight * ratio
        };
    }

    function clampPos() {
        var stageSize = getStageSize();
        var scaledWidth = baseWidth * scale;
        var scaledHeight = baseHeight * scale;

        var maxX = Math.max(0, (scaledWidth - stageSize.width) / 2);
        var maxY = Math.max(0, (scaledHeight - stageSize.height) / 2);

        posX = Math.min(maxX, Math.max(-maxX, posX));
        posY = Math.min(maxY, Math.max(-maxY, posY));
    }

    function applyTransform(animate) {
        media.style.transition = animate ? 'transform 0.18s ease' : 'none';
        media.style.transform =
            'translate(calc(-50% + ' + posX + 'px), calc(-50% + ' + posY + 'px)) scale(' + scale + ')';

        img.style.cursor = scale > 1 ? 'grab' : 'default';
    }

    function updateBaseImageSize() {
        if (!img.naturalWidth || !img.naturalHeight) return;

        var fit = computeFitSize(img.naturalWidth, img.naturalHeight);
        baseWidth = fit.width;
        baseHeight = fit.height;

        img.style.width = baseWidth + 'px';
        img.style.height = baseHeight + 'px';
    }

    window.resetTransform = function () {
        scale = 1;
        posX = 0;
        posY = 0;
        clampPos();
        applyTransform(true);
    };

    window.zoomIn = function () {
        scale = Math.min(scale + STEP, MAX);
        clampPos();
        applyTransform(true);
    };

    window.zoomOut = function () {
        scale = Math.max(scale - STEP, MIN);
        if (scale <= MIN) {
            scale = MIN;
            posX = 0;
            posY = 0;
        }
        clampPos();
        applyTransform(true);
    };

    function fitAndCenterImage() {
        updateBaseImageSize();
        resetTransform();
    }

    window.openLightbox = function (src, caption) {
        captionEl.textContent = caption || '';
        lightbox.classList.add('open');
        document.body.style.overflow = 'hidden';

        img.onload = function () {
            fitAndCenterImage();
        };

        img.src = src;
    };

    window.closeLightbox = function () {
        lightbox.classList.remove('open');
        document.body.style.overflow = '';
        img.src = '';
        scale = 1;
        posX = 0;
        posY = 0;
    };

    // 點黑底關閉
    lightbox.addEventListener('click', function (e) {
        const clickedToolbar = e.target.closest('.lightbox-toolbar');
        const clickedMedia = e.target.closest('#lightbox-media');

        if (!clickedToolbar && !clickedMedia) {
            closeLightbox();
        }
    });

    // 雙擊切換縮放
    img.addEventListener('dblclick', function (e) {
        e.stopPropagation();

        if (scale > 1) {
            resetTransform();
        } else {
            scale = 2.5;
            clampPos();
            applyTransform(true);
        }
    });

    // 滑鼠拖曳
    var isDragging = false;
    var dragStartX = 0;
    var dragStartY = 0;

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

    // 滾輪縮放（以游標位置附近為中心）
    viewport.addEventListener('wheel', function (e) {
        if (!lightbox.classList.contains('open')) return;

        e.preventDefault();

        var oldScale = scale;
        var delta = e.deltaY > 0 ? -0.2 : 0.2;
        var newScale = Math.min(Math.max(scale + delta, MIN), MAX);
        if (newScale === oldScale) return;

        var stageRect = viewport.getBoundingClientRect();
        var centerX = stageRect.left + stageRect.width / 2;
        var centerY = stageRect.top + stageRect.height / 2;

        var pointerOffsetX = e.clientX - centerX - posX;
        var pointerOffsetY = e.clientY - centerY - posY;

        posX -= pointerOffsetX * (newScale / oldScale - 1);
        posY -= pointerOffsetY * (newScale / oldScale - 1);

        scale = newScale;

        if (scale <= MIN) {
            scale = MIN;
            posX = 0;
            posY = 0;
        }

        clampPos();
        applyTransform(false);
    }, { passive: false });

    // 觸控
    var touchDragging = false;
    var touchStartX = 0;
    var touchStartY = 0;

    var pinchStartDist = 0;
    var pinchStartScale = 1;
    var pinchStartPosX = 0;
    var pinchStartPosY = 0;
    var pinchCenterX = 0;
    var pinchCenterY = 0;

    function getTouchDistance(t1, t2) {
        return Math.hypot(
            t1.clientX - t2.clientX,
            t1.clientY - t2.clientY
        );
    }

    function getTouchMidpoint(t1, t2) {
        return {
            x: (t1.clientX + t2.clientX) / 2,
            y: (t1.clientY + t2.clientY) / 2
        };
    }

    img.addEventListener('touchstart', function (e) {
        e.stopPropagation();

        if (e.touches.length === 1 && scale > 1) {
            touchDragging = true;
            touchStartX = e.touches[0].clientX - posX;
            touchStartY = e.touches[0].clientY - posY;
        } else if (e.touches.length === 2) {
            touchDragging = false;
            pinchStartDist = getTouchDistance(e.touches[0], e.touches[1]);
            pinchStartScale = scale;
            pinchStartPosX = posX;
            pinchStartPosY = posY;

            var mid = getTouchMidpoint(e.touches[0], e.touches[1]);
            pinchCenterX = mid.x;
            pinchCenterY = mid.y;
        }
    }, { passive: true });

    img.addEventListener('touchmove', function (e) {
        e.stopPropagation();

        if (e.touches.length === 1 && touchDragging) {
            posX = e.touches[0].clientX - touchStartX;
            posY = e.touches[0].clientY - touchStartY;
            clampPos();
            applyTransform(false);
        } else if (e.touches.length === 2) {
            var dist = getTouchDistance(e.touches[0], e.touches[1]);
            var newScale = Math.min(Math.max(pinchStartScale * (dist / pinchStartDist), MIN), MAX);

            var stageRect = viewport.getBoundingClientRect();
            var viewCenterX = stageRect.left + stageRect.width / 2;
            var viewCenterY = stageRect.top + stageRect.height / 2;

            var offsetX = pinchCenterX - viewCenterX - pinchStartPosX;
            var offsetY = pinchCenterY - viewCenterY - pinchStartPosY;

            scale = newScale;
            posX = pinchStartPosX - offsetX * (newScale / pinchStartScale - 1);
            posY = pinchStartPosY - offsetY * (newScale / pinchStartScale - 1);

            if (scale <= MIN) {
                scale = MIN;
                posX = 0;
                posY = 0;
            }

            clampPos();
            applyTransform(false);
        }
    }, { passive: true });

    img.addEventListener('touchend', function (e) {
        e.stopPropagation();

        if (e.touches.length === 0) {
            touchDragging = false;
            if (scale <= MIN) {
                resetTransform();
            }
        }
    }, { passive: true });

    // 視窗大小改變時重新計算適合大小
    window.addEventListener('resize', function () {
        if (!lightbox.classList.contains('open')) return;
        updateBaseImageSize();
        clampPos();
        applyTransform(false);
    });

    // 鍵盤
    document.addEventListener('keydown', function (e) {
        if (!lightbox.classList.contains('open')) return;

        if (e.key === 'Escape') closeLightbox();
        if (e.key === '+' || e.key === '=') zoomIn();
        if (e.key === '-') zoomOut();
        if (e.key === '0') resetTransform();
    });
})();