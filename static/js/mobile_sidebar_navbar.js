(function () {
    'use strict';

    var MOBILE_BREAKPOINT = 991;

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

    function getMobileNavbarHeight() {
        var styles = getComputedStyle(document.documentElement);
        var value = styles.getPropertyValue('--mobile-navbar-total-height') || styles.getPropertyValue('--mobile-navbar-height');
        var parsed = parseInt(value, 10);
        return Number.isFinite(parsed) ? parsed : 64;
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

        var logoutButton = navbar.querySelector('.mobile-navbar-logout');
        if (!logoutButton) {
            logoutButton = document.createElement('button');
            logoutButton.type = 'button';
            logoutButton.className = 'mobile-navbar-logout';
            logoutButton.setAttribute('aria-label', 'Logout from admin panel');
            logoutButton.setAttribute('title', 'Logout');
            logoutButton.innerHTML = '<i class="bi bi-box-arrow-right" aria-hidden="true"></i>';
            navbar.appendChild(logoutButton);
        }

        if (!logoutButton.dataset.bound) {
            logoutButton.addEventListener('click', function () {
                if (typeof window.logout === 'function') {
                    window.logout();
                    return;
                }

                if (window.confirm('Are you sure you want to logout?')) {
                    window.location.href = '/logout';
                }
            });
            logoutButton.dataset.bound = '1';
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

        function enforceScrollableSidebarLayout() {
            var navbarHeight = getMobileNavbarHeight();

            sidebar.style.setProperty('display', 'flex', 'important');
            sidebar.style.setProperty('flex-direction', 'column', 'important');
            sidebar.style.setProperty('overflow', 'hidden', 'important');
            sidebar.style.setProperty('overflow-x', 'hidden', 'important');

            if (isMobileViewport()) {
                sidebar.style.setProperty('top', navbarHeight + 'px', 'important');
                sidebar.style.setProperty('height', 'calc(100dvh - ' + navbarHeight + 'px)', 'important');
                sidebar.style.setProperty('max-height', 'calc(100dvh - ' + navbarHeight + 'px)', 'important');
            } else {
                sidebar.style.setProperty('top', '0', 'important');
                sidebar.style.setProperty('height', '100vh', 'important');
                sidebar.style.setProperty('max-height', '100vh', 'important');
            }

            var sidebarContent = sidebar.querySelector('.sidebar-content');
            if (sidebarContent) {
                sidebarContent.style.setProperty('flex', '1 1 auto', 'important');
                sidebarContent.style.setProperty('min-height', '0', 'important');
                sidebarContent.style.setProperty('overflow-y', 'auto', 'important');
                sidebarContent.style.setProperty('overflow-x', 'hidden', 'important');
                sidebarContent.style.setProperty('padding-bottom', 'calc(0.75rem + env(safe-area-inset-bottom, 0px))', 'important');
            }

            var sidebarFooter = sidebar.querySelector('.sidebar-footer');
            if (sidebarFooter) {
                sidebarFooter.style.setProperty('position', 'static', 'important');
                sidebarFooter.style.setProperty('bottom', 'auto', 'important');
                sidebarFooter.style.setProperty('margin-top', '0', 'important');
            }
        }

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
            enforceScrollableSidebarLayout();

            if (isMobileViewport()) {
                closeSidebar();
                sidebar.style.setProperty('display', 'flex', 'important');
            } else {
                closeSidebar();
                sidebar.style.setProperty('display', 'flex', 'important');
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
