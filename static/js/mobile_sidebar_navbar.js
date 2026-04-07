(function () {
    'use strict';

    var MOBILE_BREAKPOINT = 768;

    function isMobileViewport() {
        return window.innerWidth <= MOBILE_BREAKPOINT;
    }

    function getSchoolName(sidebar) {
        var title = sidebar.querySelector('.brand-title');
        if (title && title.textContent && title.textContent.trim()) {
            return title.textContent.trim();
        }
        return 'VishnoRex';
    }

    function ensureOverlay() {
        var overlay = document.getElementById('sidebarOverlay');
        if (overlay) {
            return overlay;
        }

        overlay = document.createElement('div');
        overlay.id = 'sidebarOverlay';
        overlay.className = 'sidebar-overlay';
        overlay.setAttribute('aria-hidden', 'true');
        document.body.appendChild(overlay);
        return overlay;
    }

    function ensureMobileNavbar(toggleButton, schoolName) {
        var navbar = document.querySelector('.mobile-top-navbar');
        if (!navbar) {
            navbar = document.createElement('div');
            navbar.className = 'mobile-top-navbar';
            navbar.setAttribute('role', 'banner');
            document.body.insertBefore(navbar, document.body.firstChild);
        }

        if (toggleButton.parentElement !== navbar) {
            navbar.insertBefore(toggleButton, navbar.firstChild);
        }

        var label = navbar.querySelector('.mobile-navbar-school-name');
        if (!label) {
            label = document.createElement('span');
            label.className = 'mobile-navbar-school-name';
            navbar.appendChild(label);
        }

        if (!label.textContent || !label.textContent.trim() || label.textContent.trim() === 'VishnoRex') {
            label.textContent = schoolName;
        }

        return navbar;
    }

    function init() {
        if (!document.body || document.body.dataset.mobileNavbarReady === '1') {
            return;
        }

        var toggleButton = document.getElementById('sidebarToggle');
        var sidebar = document.getElementById('enhanced-sidebar');

        if (!toggleButton || !sidebar) {
            return;
        }

        var schoolName = getSchoolName(sidebar);
        var overlay = ensureOverlay();
        ensureMobileNavbar(toggleButton, schoolName);

        document.body.classList.add('legacy-mobile-navbar-ready');
        document.body.dataset.mobileNavbarReady = '1';

        toggleButton.setAttribute('aria-controls', 'enhanced-sidebar');
        toggleButton.setAttribute('aria-expanded', 'false');
        toggleButton.setAttribute('aria-label', 'Toggle sidebar menu');

        function openSidebar() {
            sidebar.classList.add('show');
            document.body.classList.add('sidebar-open');
            overlay.classList.add('active');
            overlay.setAttribute('aria-hidden', 'false');
            toggleButton.setAttribute('aria-expanded', 'true');
        }

        function closeSidebar() {
            sidebar.classList.remove('show');
            document.body.classList.remove('sidebar-open');
            overlay.classList.remove('active');
            overlay.setAttribute('aria-hidden', 'true');
            toggleButton.setAttribute('aria-expanded', 'false');
        }

        function applyViewportState() {
            if (isMobileViewport()) {
                closeSidebar();
                sidebar.style.display = 'block';
            } else {
                closeSidebar();
                sidebar.style.display = 'block';
                sidebar.style.left = '0';
            }
        }

        toggleButton.addEventListener('click', function (event) {
            if (!isMobileViewport()) {
                return;
            }

            event.preventDefault();
            event.stopImmediatePropagation();

            if (sidebar.classList.contains('show')) {
                closeSidebar();
            } else {
                openSidebar();
            }
        }, true);

        overlay.addEventListener('click', function () {
            closeSidebar();
        });

        sidebar.querySelectorAll('.nav-link, a[href]').forEach(function (link) {
            link.addEventListener('click', function () {
                if (isMobileViewport()) {
                    closeSidebar();
                }
            });
        });

        document.addEventListener('keydown', function (event) {
            if (event.key === 'Escape' && isMobileViewport()) {
                closeSidebar();
            }
        });

        window.addEventListener('resize', applyViewportState);
        applyViewportState();
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
})();
