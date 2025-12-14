// ========== GESTION DES THÈMES ==========

class ThemeManager {
    constructor() {
        this.themes = {
            light: {
                primary: '#FF6B35',
                secondary: '#FF8C42',
                success: '#10B981',
                danger: '#EF4444',
                warning: '#F59E0B',
                info: '#3B82F6',
                bg: '#FFF8F5',
                text: '#1F2937',
                border: '#FED7AA'
            },
            dark: {
                primary: '#FF8C42',
                secondary: '#FFA07A',
                success: '#34D399',
                danger: '#F87171',
                warning: '#FBBF24',
                info: '#60A5FA',
                bg: '#1F1A17',
                text: '#FEF3E8',
                border: '#4A2C1A'
            }
        };

        this.currentTheme = localStorage.getItem('theme') || 'light';
        this.init();
    }

    init() {
        this.applyTheme(this.currentTheme);
        this.setupThemeToggle();
    }

    applyTheme(themeName) {
        const theme = this.themes[themeName];
        if (!theme) return;

        const root = document.documentElement;
        Object.keys(theme).forEach(key => {
            const cssVar = `--${key.replace(/([A-Z])/g, '-$1').toLowerCase()}`;
            root.style.setProperty(cssVar, theme[key]);
        });

        this.currentTheme = themeName;
        localStorage.setItem('theme', themeName);
        document.body.setAttribute('data-theme', themeName);
    }

    toggleTheme() {
        const newTheme = this.currentTheme === 'light' ? 'dark' : 'light';
        this.applyTheme(newTheme);
        return newTheme;
    }

    setupThemeToggle() {
        const toggle = document.querySelector('.theme-toggle');
        if (toggle) {
            toggle.addEventListener('click', () => this.toggleTheme());
            this.updateToggleIcon();
        }
    }

    updateToggleIcon() {
        const toggle = document.querySelector('.theme-toggle');
        if (toggle) {
            toggle.textContent = this.currentTheme === 'light' ? '🌙' : '☀️';
        }
    }

    getCurrentTheme() {
        return this.currentTheme;
    }

    getThemeColors() {
        return this.themes[this.currentTheme];
    }
}

// ========== NOTIFICATION SYSTEM ==========

class NotificationManager {
    constructor() {
        this.notifications = [];
        this.setupStyles();
    }

    setupStyles() {
        const style = document.createElement('style');
        style.textContent = `
            .notification {
                position: fixed;
                top: 20px;
                right: 20px;
                min-width: 300px;
                max-width: 400px;
                padding: 16px 20px;
                border-radius: 8px;
                box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
                animation: slideInRight 0.3s ease-out;
                z-index: 9999;
            }

            .notification.success {
                background-color: #f0fdf4;
                border-left: 4px solid #48bb78;
                color: #165e37;
            }

            .notification.error {
                background-color: #fef2f2;
                border-left: 4px solid #f56565;
                color: #7f1d1d;
            }

            .notification.warning {
                background-color: #fffbeb;
                border-left: 4px solid #ed8936;
                color: #92400e;
            }

            .notification.info {
                background-color: #f0f9ff;
                border-left: 4px solid #4299e1;
                color: #0c2d6b;
            }

            .notification-close {
                float: right;
                cursor: pointer;
                font-weight: bold;
                font-size: 1.2rem;
            }

            @keyframes slideInRight {
                from {
                    opacity: 0;
                    transform: translateX(30px);
                }
                to {
                    opacity: 1;
                    transform: translateX(0);
                }
            }

            @keyframes slideOutRight {
                from {
                    opacity: 1;
                    transform: translateX(0);
                }
                to {
                    opacity: 0;
                    transform: translateX(30px);
                }
            }
        `;
        document.head.appendChild(style);
    }

    show(message, type = 'info', duration = 5000) {
        const notification = document.createElement('div');
        notification.className = `notification ${type}`;
        notification.innerHTML = `
            ${message}
            <span class="notification-close">&times;</span>
        `;

        notification.querySelector('.notification-close').addEventListener('click', () => {
            this.remove(notification);
        });

        document.body.appendChild(notification);
        this.notifications.push(notification);

        if (duration) {
            setTimeout(() => this.remove(notification), duration);
        }

        return notification;
    }

    remove(notification) {
        notification.style.animation = 'slideOutRight 0.3s ease-out';
        setTimeout(() => {
            notification.remove();
            this.notifications = this.notifications.filter(n => n !== notification);
        }, 300);
    }

    success(message, duration) {
        return this.show(message, 'success', duration);
    }

    error(message, duration) {
        return this.show(message, 'error', duration);
    }

    warning(message, duration) {
        return this.show(message, 'warning', duration);
    }

    info(message, duration) {
        return this.show(message, 'info', duration);
    }

    clearAll() {
        this.notifications.forEach(notification => {
            notification.remove();
        });
        this.notifications = [];
    }
}

// ========== STORAGE MANAGER ==========

class StorageManager {
    static set(key, value, isSession = false) {
        const storage = isSession ? sessionStorage : localStorage;
        try {
            storage.setItem(key, JSON.stringify(value));
            return true;
        } catch (e) {
            console.error('Storage error:', e);
            return false;
        }
    }

    static get(key, isSession = false) {
        const storage = isSession ? sessionStorage : localStorage;
        try {
            const item = storage.getItem(key);
            return item ? JSON.parse(item) : null;
        } catch (e) {
            console.error('Storage error:', e);
            return null;
        }
    }

    static remove(key, isSession = false) {
        const storage = isSession ? sessionStorage : localStorage;
        try {
            storage.removeItem(key);
            return true;
        } catch (e) {
            console.error('Storage error:', e);
            return false;
        }
    }

    static clear(isSession = false) {
        const storage = isSession ? sessionStorage : localStorage;
        try {
            storage.clear();
            return true;
        } catch (e) {
            console.error('Storage error:', e);
            return false;
        }
    }
}

// ========== API MANAGER ==========

class APIManager {
    static async fetch(url, options = {}) {
        try {
            const response = await fetch(url, {
                headers: {
                    'Content-Type': 'application/json',
                    ...options.headers
                },
                ...options
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            return await response.json();
        } catch (error) {
            console.error('API error:', error);
            throw error;
        }
    }

    static async get(url) {
        return this.fetch(url, { method: 'GET' });
    }

    static async post(url, data) {
        return this.fetch(url, {
            method: 'POST',
            body: JSON.stringify(data)
        });
    }

    static async put(url, data) {
        return this.fetch(url, {
            method: 'PUT',
            body: JSON.stringify(data)
        });
    }

    static async delete(url) {
        return this.fetch(url, { method: 'DELETE' });
    }
}

// ========== ANALYTICS TRACKER ==========

class AnalyticsTracker {
    constructor() {
        this.events = [];
        this.sessionStart = Date.now();
    }

    trackEvent(eventName, data = {}) {
        const event = {
            name: eventName,
            timestamp: new Date().toISOString(),
            data: data,
            sessionTime: Date.now() - this.sessionStart
        };
        this.events.push(event);
        console.log('Event tracked:', event);
        return event;
    }

    trackPageView(page) {
        return this.trackEvent('pageview', { page });
    }

    trackClick(elementId) {
        return this.trackEvent('click', { elementId });
    }

    trackFormSubmit(formId) {
        return this.trackEvent('form_submit', { formId });
    }

    getEvents() {
        return this.events;
    }

    getSessionDuration() {
        return Date.now() - this.sessionStart;
    }

    exportEvents() {
        return JSON.stringify(this.events, null, 2);
    }

    clearEvents() {
        this.events = [];
    }
}

// ========== INITIALISATION GLOBALE ==========

let themeManager;
let notificationManager;
let analytics;

document.addEventListener('DOMContentLoaded', () => {
    themeManager = new ThemeManager();
    notificationManager = new NotificationManager();
    analytics = new AnalyticsTracker();

    // Exposer globalement
    window.ThemeManager = themeManager;
    window.NotificationManager = notificationManager;
    window.StorageManager = StorageManager;
    window.APIManager = APIManager;
    window.AnalyticsTracker = analytics;
});

// Raccourcis globaux
window.notify = {
    success: (msg, duration) => notificationManager.success(msg, duration),
    error: (msg, duration) => notificationManager.error(msg, duration),
    warning: (msg, duration) => notificationManager.warning(msg, duration),
    info: (msg, duration) => notificationManager.info(msg, duration)
};

window.theme = {
    toggle: () => themeManager.toggleTheme(),
    get: () => themeManager.getCurrentTheme(),
    set: (name) => themeManager.applyTheme(name)
};
