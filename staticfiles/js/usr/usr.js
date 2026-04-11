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
    mediaContainer.innerHTML = '';
    actionContainer.innerHTML = '';
    actionContainer.style.display = 'none';

    if (videoFileUrl) {
        mediaContainer.innerHTML = `
            <video controls style="width:100%; max-height:70vh; background:#000;">
                <source src="${videoFileUrl}" type="video/mp4">
            </video>`;
    } else if (embedCode && embedCode.trim() !== '') {
        mediaContainer.innerHTML = `<div style="width:100%; aspect-ratio:16/9; background:#000;">${embedCode}</div>`;
        const iframe = mediaContainer.querySelector('iframe');
        if (iframe) {
            iframe.style.width = '100%';
            iframe.style.height = '100%';
            iframe.style.border = 'none';
            iframe.style.display = 'block';
            iframe.setAttribute('allowfullscreen', '');
        }
    } else if (embedUrl) {
        const videoId = embedUrl.split('/embed/')[1]?.split('?')[0];
        mediaContainer.innerHTML = `<div id="yt-player-container" style="width:100%; aspect-ratio:16/9;"></div>`;
        if (!window.YT) {
            const tag = document.createElement('script');
            tag.src = 'https://www.youtube.com/iframe_api';
            document.head.appendChild(tag);
            window.onYouTubeIframeAPIReady = () => {
                new YT.Player('yt-player-container', {
                    videoId: videoId,
                    width: '100%',
                    height: '100%',
                    playerVars: { rel: 0 }
                });
            };
        } else {
            new YT.Player('yt-player-container', {
                videoId: videoId,
                width: '100%',
                height: '100%',
                playerVars: { rel: 0 }
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
    document.getElementById('videoModalMedia').innerHTML = '';
    document.body.style.overflow = '';
}

document.addEventListener('DOMContentLoaded', function () {
    var videoModalEl = document.getElementById('videoModal');
    if (videoModalEl) {
        videoModalEl.addEventListener('shown.bs.modal', function () {
            document.body.style.overflow = 'hidden';
        });
        videoModalEl.addEventListener('hidden.bs.modal', function () {
            closeRichVideoModal();
        });
    }
});