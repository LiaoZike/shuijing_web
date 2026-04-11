function openRichVideoModal(el) {
    const title = el.getAttribute('data-title');
    const desc = el.getAttribute('data-desc');
    const embedUrl = el.getAttribute('data-embed-url');
    const embedCode = el.getAttribute('data-embed-code');
    const oriUrl = el.getAttribute('data-ori-url');
    const videoFileUrl = el.getAttribute('data-video-url');

    document.getElementById('videoModalLabel').innerText = 'USR 計畫歷程';
    document.getElementById('videoModalInnerTitle').innerText = title || '';

    const mediaContainer = document.getElementById('videoModalMedia');
    const actionContainer = document.getElementById('videoModalAction');
    const scrollGuard = document.getElementById('videoModalScrollGuard');
    
    // 清除舊內容，但保留 Scroll Guard
    const existingMedia = mediaContainer.querySelectorAll(':not(#videoModalScrollGuard)');
    existingMedia.forEach(m => m.remove());
    
    actionContainer.innerHTML = '';
    actionContainer.style.display = 'none';

    // 重置防護罩狀態
    if (scrollGuard) {
        scrollGuard.style.display = 'flex';
        scrollGuard.style.pointerEvents = 'auto';
        scrollGuard.style.background = 'rgba(0,0,0,0)';
    }

    if (videoFileUrl) {
        const videoEl = document.createElement('video');
        videoEl.controls = true;
        videoEl.style.width = '100%';
        videoEl.style.maxHeight = '70vh';
        videoEl.style.background = '#000';
        videoEl.innerHTML = `<source src="${videoFileUrl}" type="video/mp4">`;
        mediaContainer.appendChild(videoEl);
    } else if (embedCode && embedCode.trim() !== '') {
        const wrap = document.createElement('div');
        wrap.style.width = '100%';
        wrap.style.aspectRatio = '16/9';
        wrap.style.background = '#000';
        wrap.innerHTML = embedCode;
        mediaContainer.appendChild(wrap);
        
        const iframe = wrap.querySelector('iframe');
        if (iframe) {
            iframe.style.width = '100%';
            iframe.style.height = '100%';
            iframe.style.border = 'none';
            iframe.style.display = 'block';
            iframe.setAttribute('allowfullscreen', '');
        }
    } else if (embedUrl) {
        const videoId = embedUrl.split('/embed/')[1]?.split('?')[0];
        const ytWrap = document.createElement('div');
        ytWrap.id = 'yt-player-container';
        ytWrap.style.width = '100%';
        ytWrap.style.aspectRatio = '16/9';
        mediaContainer.appendChild(ytWrap);

        if (!window.YT) {
            const tag = document.createElement('script');
            tag.src = 'https://www.youtube.com/iframe_api';
            document.head.appendChild(tag);
            window.onYouTubeIframeAPIReady = () => {
                new YT.Player('yt-player-container', {
                    videoId: videoId, width: '100%', height: '100%', playerVars: { rel: 0 }
                });
            };
        } else {
            new YT.Player('yt-player-container', {
                videoId: videoId, width: '100%', height: '100%', playerVars: { rel: 0 }
            });
        }
    }

    document.getElementById('videoModalDesc').innerText = desc || '';

    const imagesTemplate = el.querySelector('.video-images-data');
    const imagesContainer = document.getElementById('videoModalImages');
    imagesContainer.innerHTML = '';
    if (imagesTemplate && imagesTemplate.innerHTML.trim() !== '') {
        imagesContainer.innerHTML = imagesTemplate.innerHTML;
    }

    var myModal = new bootstrap.Modal(document.getElementById('videoModal'));
    myModal.show();
}

function closeRichVideoModal() {
    // 關閉時清空媒體，防止背景播放
    const mediaContainer = document.getElementById('videoModalMedia');
    const existingMedia = mediaContainer.querySelectorAll(':not(#videoModalScrollGuard)');
    existingMedia.forEach(m => m.remove());
    document.body.style.overflow = '';
}

document.addEventListener('DOMContentLoaded', function () {
    const videoModalEl = document.getElementById('videoModal');
    if (videoModalEl) {
        const scrollGuard = document.getElementById('videoModalScrollGuard');
        const modalBody = videoModalEl.querySelector('.modal-body');
        const tip = scrollGuard?.querySelector('.scroll-tip');

        if (scrollGuard && modalBody) {
            // 1. 滾動轉發：滑鼠在防護罩上捲動時，直接轉發給 modal-body
            scrollGuard.addEventListener('wheel', function (e) {
                modalBody.scrollTop += e.deltaY;
                if (e.deltaY !== 0) {
                    e.preventDefault();
                }
            }, { passive: false });

            // 2. 點擊解鎖：點擊後消失，方便操作影片
            scrollGuard.addEventListener('click', function () {
                scrollGuard.style.pointerEvents = 'none';
                scrollGuard.style.background = 'rgba(0,0,0,0)';
                if (tip) tip.style.opacity = '0';
            });

            // 3. 提示效果
            scrollGuard.addEventListener('mouseenter', function() {
                if (scrollGuard.style.pointerEvents !== 'none') {
                    if (tip) tip.style.opacity = '1';
                }
            });
            scrollGuard.addEventListener('mouseleave', function() {
                if (tip) tip.style.opacity = '0';
            });
        }

        videoModalEl.addEventListener('shown.bs.modal', function () {
            document.body.style.overflow = 'hidden';
        });
        
        videoModalEl.addEventListener('hidden.bs.modal', function () {
            closeRichVideoModal();
        });
    }
});