
(function () {
    document.body.classList.add('page-home');
    const nav = document.getElementById('mainNav');
    function onScroll() {
        nav.classList.toggle('scrolled', window.scrollY > 80);
    }
    window.addEventListener('scroll', onScroll, { passive: true });
    onScroll();
})();
(function () {
    const NOTICE_URL = document.querySelector('[data-notice-url]')?.dataset.noticeUrl || '/notices/';
    const EVENT_URL = document.querySelector('[data-event-url]')?.dataset.eventUrl || '/events/';

    window.cbSwitch = function (tab) {
        const tabN = document.getElementById('tab-notice');
        const tabE = document.getElementById('tab-event');
        const panelN = document.getElementById('panel-notice');
        const panelE = document.getElementById('panel-event');
        const allLink = document.getElementById('cb-all-link');

        if (tab === 'notice') {
            tabN.classList.add('active');
            tabE.classList.remove('active');
            panelN.classList.remove('cb-panel--hidden');
            panelE.classList.add('cb-panel--hidden');
            tabN.setAttribute('aria-selected', 'true');
            tabE.setAttribute('aria-selected', 'false');
            if (allLink) {
                allLink.textContent = '查看全部公告 ';
                allLink.insertAdjacentHTML('beforeend', '<i class="bi bi-arrow-right"></i>');
                allLink.href = NOTICE_URL;
            }
        } else {
            tabE.classList.add('active');
            tabN.classList.remove('active');
            panelE.classList.remove('cb-panel--hidden');
            panelN.classList.add('cb-panel--hidden');
            tabE.setAttribute('aria-selected', 'true');
            tabN.setAttribute('aria-selected', 'false');
            if (allLink) {
                allLink.textContent = '查看全部活動 ';
                allLink.insertAdjacentHTML('beforeend', '<i class="bi bi-arrow-right"></i>');
                allLink.href = EVENT_URL;
            }
        }
    };
})();