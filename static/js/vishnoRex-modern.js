/*!
 * VishnoRex Modern JavaScript Framework v2.0
 * Enhanced interactions and animations for the modern UI
 */

(function(window) {
    'use strict';

    // Main VishnoRex object
    const VishnoRex = {
        version: '2.0.0',
        modules: {},
        config: {
            animationDuration: 300,
            autoSaveDelay: 2000,
            toastDuration: 5000,
            debounceDelay: 300
        }
    };

    // Utility functions
    VishnoRex.utils = {
        // Debounce function
        debounce: function(func, wait, immediate) {
            let timeout;
            return function executedFunction(...args) {
                const later = () => {
                    timeout = null;
                    if (!immediate) func.apply(this, args);
                };
                const callNow = immediate && !timeout;
                clearTimeout(timeout);
                timeout = setTimeout(later, wait);
                if (callNow) func.apply(this, args);
            };
        },

        // Throttle function
        throttle: function(func, limit) {
            let inThrottle;
            return function(...args) {
                if (!inThrottle) {
                    func.apply(this, args);
                    inThrottle = true;
                    setTimeout(() => inThrottle = false, limit);
                }
            };
        },

        // Format currency
        formatCurrency: function(amount, currency = 'USD') {
            return new Intl.NumberFormat('en-US', {
                style: 'currency',
                currency: currency
            }).format(amount);
        },

        // Format date
        formatDate: function(date, options = {}) {
            const defaultOptions = {
                year: 'numeric',
                month: 'short',
                day: 'numeric'
            };
            return new Intl.DateTimeFormat('en-US', { ...defaultOptions, ...options }).format(new Date(date));
        },

        // Deep clone object
        deepClone: function(obj) {
            if (obj === null || typeof obj !== 'object') return obj;
            if (obj instanceof Date) return new Date(obj.getTime());
            if (obj instanceof Array) return obj.map(item => this.deepClone(item));
            if (typeof obj === 'object') {
                const clonedObj = {};
                for (const key in obj) {
                    if (obj.hasOwnProperty(key)) {
                        clonedObj[key] = this.deepClone(obj[key]);
                    }
                }
                return clonedObj;
            }
        },

        // Generate unique ID
        generateId: function(prefix = 'vr') {
            return `${prefix}_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
        },

        // Get CSRF token
        getCSRFToken: function() {
            const token = document.querySelector('meta[name="csrf-token"]');
            return token ? token.getAttribute('content') : '';
        }
    };

    // Event system
    VishnoRex.events = {
        listeners: {},

        on: function(event, callback) {
            if (!this.listeners[event]) {
                this.listeners[event] = [];
            }
            this.listeners[event].push(callback);
        },

        off: function(event, callback) {
            if (!this.listeners[event]) return;
            const index = this.listeners[event].indexOf(callback);
            if (index > -1) {
                this.listeners[event].splice(index, 1);
            }
        },

        emit: function(event, data) {
            if (!this.listeners[event]) return;
            this.listeners[event].forEach(callback => {
                try {
                    callback(data);
                } catch (error) {
                    console.error('Event callback error:', error);
                }
            });
        }
    };

    // HTTP client with enhanced error handling
    VishnoRex.http = {
        request: async function(url, options = {}) {
            const defaultOptions = {
                method: 'GET',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': VishnoRex.utils.getCSRFToken(),
                    'X-Requested-With': 'XMLHttpRequest'
                },
                credentials: 'same-origin'
            };

            const mergedOptions = { ...defaultOptions, ...options };
            
            if (mergedOptions.headers) {
                mergedOptions.headers = { ...defaultOptions.headers, ...options.headers };
            }

            try {
                VishnoRex.events.emit('http:start', { url, options: mergedOptions });
                
                const response = await fetch(url, mergedOptions);
                
                if (!response.ok) {
                    throw new Error(`HTTP ${response.status}: ${response.statusText}`);
                }

                const contentType = response.headers.get('content-type');
                let data;
                
                if (contentType && contentType.includes('application/json')) {
                    data = await response.json();
                } else {
                    data = await response.text();
                }

                VishnoRex.events.emit('http:success', { url, data, response });
                return { data, response };

            } catch (error) {
                VishnoRex.events.emit('http:error', { url, error });
                throw error;
            } finally {
                VishnoRex.events.emit('http:complete', { url });
            }
        },

        get: function(url, options = {}) {
            return this.request(url, { ...options, method: 'GET' });
        },

        post: function(url, data, options = {}) {
            return this.request(url, {
                ...options,
                method: 'POST',
                body: typeof data === 'string' ? data : JSON.stringify(data)
            });
        },

        put: function(url, data, options = {}) {
            return this.request(url, {
                ...options,
                method: 'PUT',
                body: typeof data === 'string' ? data : JSON.stringify(data)
            });
        },

        delete: function(url, options = {}) {
            return this.request(url, { ...options, method: 'DELETE' });
        }
    };

    // Loading states management
    VishnoRex.loading = {
        activeLoaders: new Set(),
        
        show: function(id = 'global') {
            this.activeLoaders.add(id);
            VishnoRex.events.emit('loading:show', { id });
            
            if (id === 'global') {
                const overlay = document.getElementById('loadingOverlay');
                if (overlay) {
                    overlay.classList.remove('d-none');
                    overlay.setAttribute('aria-hidden', 'false');
                }
            }
        },

        hide: function(id = 'global') {
            this.activeLoaders.delete(id);
            VishnoRex.events.emit('loading:hide', { id });
            
            if (id === 'global' && this.activeLoaders.size === 0) {
                const overlay = document.getElementById('loadingOverlay');
                if (overlay) {
                    overlay.classList.add('d-none');
                    overlay.setAttribute('aria-hidden', 'true');
                }
            }
        },

        isActive: function(id = 'global') {
            return this.activeLoaders.has(id);
        }
    };

    // Toast notification system
    VishnoRex.toast = {
        container: null,

        init: function() {
            if (!this.container) {
                this.container = document.createElement('div');
                this.container.className = 'toast-container';
                this.container.style.cssText = `
                    position: fixed;
                    top: 20px;
                    right: 20px;
                    z-index: 9999;
                    pointer-events: none;
                `;
                document.body.appendChild(this.container);
            }
        },

        show: function(message, type = 'info', duration = VishnoRex.config.toastDuration) {
            this.init();

            const toast = document.createElement('div');
            toast.className = `toast-item toast-${type}`;
            toast.style.cssText = `
                background: var(--white);
                border: 1px solid var(--gray-200);
                border-radius: var(--radius-lg);
                box-shadow: var(--shadow-xl);
                padding: var(--space-4);
                margin-bottom: var(--space-2);
                max-width: 400px;
                pointer-events: auto;
                transform: translateX(100%);
                transition: transform var(--transition-base);
                display: flex;
                align-items: center;
                gap: var(--space-3);
            `;

            const typeIcons = {
                success: 'bi-check-circle-fill text-success',
                error: 'bi-exclamation-triangle-fill text-danger',
                warning: 'bi-exclamation-triangle-fill text-warning',
                info: 'bi-info-circle-fill text-primary'
            };

            toast.innerHTML = `
                <i class="bi ${typeIcons[type] || typeIcons.info}"></i>
                <span class="flex-grow-1">${message}</span>
                <button type="button" class="btn-close btn-close-sm" onclick="this.parentElement.remove()"></button>
            `;

            this.container.appendChild(toast);

            // Animate in
            requestAnimationFrame(() => {
                toast.style.transform = 'translateX(0)';
            });

            // Auto remove
            if (duration > 0) {
                setTimeout(() => {
                    if (toast.parentElement) {
                        toast.style.transform = 'translateX(100%)';
                        setTimeout(() => toast.remove(), 300);
                    }
                }, duration);
            }

            return toast;
        },

        success: function(message, duration) {
            return this.show(message, 'success', duration);
        },

        error: function(message, duration) {
            return this.show(message, 'error', duration);
        },

        warning: function(message, duration) {
            return this.show(message, 'warning', duration);
        },

        info: function(message, duration) {
            return this.show(message, 'info', duration);
        }
    };

    // Form validation system
    VishnoRex.validation = {
        rules: {
            required: (value) => value && value.trim() !== '',
            email: (value) => /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(value),
            phone: (value) => /^[\+]?[1-9][\d]{0,15}$/.test(value.replace(/\s/g, '')),
            minLength: (value, min) => value && value.length >= min,
            maxLength: (value, max) => value && value.length <= max,
            numeric: (value) => /^\d+$/.test(value),
            alphanumeric: (value) => /^[a-zA-Z0-9]+$/.test(value)
        },

        validate: function(form) {
            const errors = {};
            const inputs = form.querySelectorAll('[data-validate]');

            inputs.forEach(input => {
                const rules = input.dataset.validate.split('|');
                const fieldName = input.name || input.id;
                const value = input.value;

                rules.forEach(rule => {
                    const [ruleName, ruleParam] = rule.split(':');
                    
                    if (this.rules[ruleName]) {
                        const isValid = ruleParam 
                            ? this.rules[ruleName](value, ruleParam)
                            : this.rules[ruleName](value);

                        if (!isValid) {
                            if (!errors[fieldName]) errors[fieldName] = [];
                            errors[fieldName].push(this.getErrorMessage(ruleName, ruleParam));
                        }
                    }
                });
            });

            return {
                isValid: Object.keys(errors).length === 0,
                errors: errors
            };
        },

        getErrorMessage: function(rule, param) {
            const messages = {
                required: 'This field is required',
                email: 'Please enter a valid email address',
                phone: 'Please enter a valid phone number',
                minLength: `Minimum length is ${param} characters`,
                maxLength: `Maximum length is ${param} characters`,
                numeric: 'Please enter numbers only',
                alphanumeric: 'Please enter letters and numbers only'
            };

            return messages[rule] || 'Invalid input';
        },

        showErrors: function(form, errors) {
            // Clear existing errors
            form.querySelectorAll('.field-error').forEach(error => error.remove());
            form.querySelectorAll('.is-invalid').forEach(input => input.classList.remove('is-invalid'));

            // Show new errors
            Object.keys(errors).forEach(fieldName => {
                const input = form.querySelector(`[name="${fieldName}"], #${fieldName}`);
                if (input) {
                    input.classList.add('is-invalid');
                    
                    const errorDiv = document.createElement('div');
                    errorDiv.className = 'field-error text-danger text-sm mt-1';
                    errorDiv.textContent = errors[fieldName][0];
                    
                    input.parentNode.appendChild(errorDiv);
                }
            });
        }
    };

    // Auto-save functionality
    VishnoRex.autoSave = {
        timers: {},
        
        enable: function(form, url, options = {}) {
            const formId = form.id || VishnoRex.utils.generateId('form');
            const delay = options.delay || VishnoRex.config.autoSaveDelay;

            const saveData = VishnoRex.utils.debounce(async () => {
                try {
                    const formData = new FormData(form);
                    const data = Object.fromEntries(formData.entries());
                    
                    await VishnoRex.http.post(url, data);
                    VishnoRex.events.emit('autosave:success', { formId, data });
                    
                } catch (error) {
                    VishnoRex.events.emit('autosave:error', { formId, error });
                }
            }, delay);

            form.addEventListener('input', saveData);
            form.addEventListener('change', saveData);

            this.timers[formId] = saveData;
        },

        disable: function(form) {
            const formId = form.id || 'unknown';
            if (this.timers[formId]) {
                delete this.timers[formId];
            }
        }
    };

    // Animation utilities
    VishnoRex.animate = {
        fadeIn: function(element, duration = VishnoRex.config.animationDuration) {
            element.style.opacity = '0';
            element.style.display = 'block';
            
            const startTime = performance.now();
            
            const animate = (currentTime) => {
                const elapsed = currentTime - startTime;
                const progress = Math.min(elapsed / duration, 1);
                
                element.style.opacity = progress.toString();
                
                if (progress < 1) {
                    requestAnimationFrame(animate);
                }
            };
            
            requestAnimationFrame(animate);
        },

        fadeOut: function(element, duration = VishnoRex.config.animationDuration) {
            const startTime = performance.now();
            const startOpacity = parseFloat(getComputedStyle(element).opacity);
            
            const animate = (currentTime) => {
                const elapsed = currentTime - startTime;
                const progress = Math.min(elapsed / duration, 1);
                
                element.style.opacity = (startOpacity * (1 - progress)).toString();
                
                if (progress < 1) {
                    requestAnimationFrame(animate);
                } else {
                    element.style.display = 'none';
                }
            };
            
            requestAnimationFrame(animate);
        },

        slideUp: function(element, duration = VishnoRex.config.animationDuration) {
            const startHeight = element.offsetHeight;
            element.style.overflow = 'hidden';
            element.style.transition = `height ${duration}ms ease-out`;
            element.style.height = startHeight + 'px';
            
            requestAnimationFrame(() => {
                element.style.height = '0px';
                
                setTimeout(() => {
                    element.style.display = 'none';
                    element.style.height = '';
                    element.style.overflow = '';
                    element.style.transition = '';
                }, duration);
            });
        },

        slideDown: function(element, duration = VishnoRex.config.animationDuration) {
            element.style.display = 'block';
            const targetHeight = element.scrollHeight;
            element.style.height = '0px';
            element.style.overflow = 'hidden';
            element.style.transition = `height ${duration}ms ease-out`;
            
            requestAnimationFrame(() => {
                element.style.height = targetHeight + 'px';
                
                setTimeout(() => {
                    element.style.height = '';
                    element.style.overflow = '';
                    element.style.transition = '';
                }, duration);
            });
        }
    };

    // Initialize framework
    VishnoRex.init = function() {
        // Setup global event listeners
        this.setupGlobalListeners();
        
        // Initialize toast system
        this.toast.init();
        
        // Setup HTTP interceptors
        this.setupHttpInterceptors();
        
        // Emit ready event
        this.events.emit('vishnoRex:ready');
        
        console.log(`VishnoRex Framework v${this.version} initialized`);
    };

    VishnoRex.setupGlobalListeners = function() {
        // Handle all form submissions with validation
        document.addEventListener('submit', (e) => {
            const form = e.target;
            if (form.dataset.validate !== undefined) {
                e.preventDefault();
                
                const validation = this.validation.validate(form);
                if (!validation.isValid) {
                    this.validation.showErrors(form, validation.errors);
                    return;
                }
                
                // If validation passes, continue with form submission
                this.events.emit('form:validated', { form, validation });
            }
        });

        // Handle loading states for AJAX requests
        document.addEventListener('click', (e) => {
            const button = e.target.closest('[data-loading]');
            if (button && !button.disabled) {
                button.disabled = true;
                button.classList.add('loading');
                
                // Re-enable button after a timeout (fallback)
                setTimeout(() => {
                    button.disabled = false;
                    button.classList.remove('loading');
                }, 10000);
            }
        });
    };

    VishnoRex.setupHttpInterceptors = function() {
        // Show loading on HTTP start
        this.events.on('http:start', () => {
            this.loading.show();
        });
        
        // Hide loading on HTTP complete
        this.events.on('http:complete', () => {
            this.loading.hide();
        });
        
        // Show error toast on HTTP error
        this.events.on('http:error', (data) => {
            this.toast.error(`Request failed: ${data.error.message}`);
        });
    };

    // Expose VishnoRex to global scope
    window.VishnoRex = VishnoRex;

    // Auto-initialize when DOM is ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', () => VishnoRex.init());
    } else {
        VishnoRex.init();
    }

})(window);
