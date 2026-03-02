/**
 * GitHub Webhook Monitor - Frontend JavaScript
 * Handles event fetching, display, and auto-refresh
 */

// Configuration
const CONFIG = {
    REFRESH_INTERVAL: 15000, // 15 seconds
    API_ENDPOINTS: {
        EVENTS: '/events',
        CLEAR: '/events/clear',
        HEALTH: '/health'
    }
};

// State
const state = {
    events: [],
    autoRefresh: true,
    refreshTimer: null,
    lastUpdate: null
};

// DOM Elements
const elements = {
    eventsList: null,
    loadingState: null,
    emptyState: null,
    statusDot: null,
    statusText: null,
    lastUpdate: null,
    autoRefreshToggle: null,
    refreshBtn: null,
    clearBtn: null,
    // Stats
    pushCount: null,
    prCount: null,
    mergeCount: null,
    totalCount: null
};

function init() {
    // Get DOM elements
    elements.eventsList = document.getElementById('eventsList');
    elements.loadingState = document.getElementById('loadingState');
    elements.emptyState = document.getElementById('emptyState');
    elements.statusDot = document.getElementById('statusDot');
    elements.statusText = document.getElementById('statusText');
    elements.lastUpdate = document.getElementById('lastUpdate');
    elements.autoRefreshToggle = document.getElementById('autoRefreshToggle');
    elements.refreshBtn = document.getElementById('refreshBtn');
    elements.clearBtn = document.getElementById('clearBtn');
    elements.pushCount = document.getElementById('pushCount');
    elements.prCount = document.getElementById('prCount');
    elements.mergeCount = document.getElementById('mergeCount');
    elements.totalCount = document.getElementById('totalCount');

    // Set up event listeners
    setupEventListeners();

    // Initial fetch
    fetchEvents();

    // Start auto-refresh
    startAutoRefresh();

    console.log('✅ GitHub Webhook Monitor initialized');
}

/**
 * Set up event listeners
 */
function setupEventListeners() {
    // Auto-refresh toggle
    elements.autoRefreshToggle.addEventListener('change', (e) => {
        state.autoRefresh = e.target.checked;
        if (state.autoRefresh) {
            startAutoRefresh();
        } else {
            stopAutoRefresh();
        }
    });

    // Refresh button
    elements.refreshBtn.addEventListener('click', () => {
        fetchEvents();
    });

    // Clear button
    elements.clearBtn.addEventListener('click', () => {
        if (confirm('Are you sure you want to clear all events? This cannot be undone.')) {
            clearEvents();
        }
    });
}

/**
 * Fetch events from API
 */
async function fetchEvents() {
    try {
        updateStatus('loading', 'Fetching events...');

        const response = await fetch(CONFIG.API_ENDPOINTS.EVENTS);
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const events = await response.json();
        
        state.events = events;
        state.lastUpdate = new Date();

        updateUI();
        updateStatus('connected', 'Connected');
        updateLastUpdate();

        console.log(`✅ Fetched ${events.length} events`);

    } catch (error) {
        console.error('❌ Error fetching events:', error);
        updateStatus('error', 'Connection error');
        showError('Failed to fetch events. Please try again.');
    }
}

/**
 * Clear all events
 */
async function clearEvents() {
    try {
        const response = await fetch(CONFIG.API_ENDPOINTS.CLEAR, {
            method: 'POST'
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const result = await response.json();
        console.log(`✅ Cleared ${result.deleted_count} events`);

        // Refresh to show empty state
        fetchEvents();

    } catch (error) {
        console.error('❌ Error clearing events:', error);
        showError('Failed to clear events. Please try again.');
    }
}

/**
 * Update UI with current events
 */
function updateUI() {
    const hasEvents = state.events.length > 0;

    // Show/hide states
    if (hasEvents) {
        elements.loadingState.style.display = 'none';
        elements.emptyState.style.display = 'none';
        elements.eventsList.style.display = 'block';
        renderEvents();
    } else {
        elements.loadingState.style.display = 'none';
        elements.emptyState.style.display = 'block';
        elements.eventsList.style.display = 'none';
    }
    updateStats();
}

/**
 * Render events to DOM
 */
function renderEvents() {
    elements.eventsList.innerHTML = '';

    state.events.forEach((event, index) => {
        const eventItem = createEventElement(event, index);
        elements.eventsList.appendChild(eventItem);
    });
}

/**
 * Create event element
 */
function createEventElement(event, index) {
    const div = document.createElement('div');
    div.className = `event-item ${event.action.toLowerCase()}`;
    div.style.animationDelay = `${index * 0.05}s`;

    const actionIcon = getActionIcon(event.action);
    
    div.innerHTML = `
        <div class="event-message">${event.message}</div>
        <div class="event-meta">
            <span class="event-badge ${event.action.toLowerCase()}">
                ${actionIcon} ${event.action.replace('_', ' ')}
            </span>
            <span>👤 ${event.author}</span>
            ${event.raw.from_branch ? `<span>🔀 ${event.raw.from_branch} → ${event.raw.to_branch}</span>` : `<span>🌿 ${event.raw.to_branch}</span>`}
        </div>
    `;

    return div;
}

/**
 * Get icon for action type
 */
function getActionIcon(action) {
    const icons = {
        'PUSH': '⬆️',
        'PULL_REQUEST': '🔀',
        'MERGE': '✅'
    };
    return icons[action] || '📌';
}

/**
 * Update statistics
 */
function updateStats() {
    let pushes = 0;
    let pullRequests = 0;
    let merges = 0;

    state.events.forEach(event => {
        switch (event.action) {
            case 'PUSH':
                pushes++;
                break;
            case 'PULL_REQUEST':
                pullRequests++;
                break;
            case 'MERGE':
                merges++;
                break;
        }
    });

    // Animate counter updates
    animateValue(elements.pushCount, parseInt(elements.pushCount.textContent) || 0, pushes);
    animateValue(elements.prCount, parseInt(elements.prCount.textContent) || 0, pullRequests);
    animateValue(elements.mergeCount, parseInt(elements.mergeCount.textContent) || 0, merges);
    animateValue(elements.totalCount, parseInt(elements.totalCount.textContent) || 0, state.events.length);
}

/**
 * Animate counter from start to end value
 */
function animateValue(element, start, end, duration = 500) {
    if (start === end) return;

    const range = end - start;
    const increment = range / (duration / 16);
    let current = start;

    const timer = setInterval(() => {
        current += increment;
        if ((increment > 0 && current >= end) || (increment < 0 && current <= end)) {
            current = end;
            clearInterval(timer);
        }
        element.textContent = Math.floor(current);
    }, 16);
}

/**
 * Update status indicator
 */
function updateStatus(status, text) {
    elements.statusDot.className = `status-dot ${status}`;
    elements.statusText.textContent = text;
}

/**
 * Update last update time
 */
function updateLastUpdate() {
    if (!state.lastUpdate) {
        elements.lastUpdate.textContent = 'Never';
        return;
    }

    const now = new Date();
    const diff = Math.floor((now - state.lastUpdate) / 1000); // seconds

    let timeText;
    if (diff < 60) {
        timeText = 'Just now';
    } else if (diff < 3600) {
        const minutes = Math.floor(diff / 60);
        timeText = `${minutes} minute${minutes > 1 ? 's' : ''} ago`;
    } else {
        const hours = Math.floor(diff / 3600);
        timeText = `${hours} hour${hours > 1 ? 's' : ''} ago`;
    }

    elements.lastUpdate.textContent = timeText;
}

/**
 * Start auto-refresh timer
 */
function startAutoRefresh() {
    if (state.refreshTimer) {
        clearInterval(state.refreshTimer);
    }

    state.refreshTimer = setInterval(() => {
        if (state.autoRefresh) {
            console.log('🔄 Auto-refreshing events...');
            fetchEvents();
        }
    }, CONFIG.REFRESH_INTERVAL);

    console.log(`✅ Auto-refresh started (${CONFIG.REFRESH_INTERVAL / 1000}s interval)`);
}

/**
 * Stop auto-refresh timer
 */
function stopAutoRefresh() {
    if (state.refreshTimer) {
        clearInterval(state.refreshTimer);
        state.refreshTimer = null;
        console.log('⏸️ Auto-refresh stopped');
    }
}

/**
 * Show error message
 */
function showError(message) {
    const notification = document.createElement('div');
    notification.className = 'error-notification';
    notification.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        background: rgba(239, 68, 68, 0.9);
        color: white;
        padding: 1rem 1.5rem;
        border-radius: 0.5rem;
        box-shadow: 0 10px 15px -3px rgb(0 0 0 / 0.1);
        z-index: 1000;
        animation: slideIn 0.3s ease;
    `;
    notification.textContent = message;

    document.body.appendChild(notification);

    // Remove after 5 seconds
    setTimeout(() => {
        notification.style.animation = 'slideOut 0.3s ease';
        setTimeout(() => {
            document.body.removeChild(notification);
        }, 300);
    }, 5000);
}

/**
 * Update last update time periodically
 */
setInterval(updateLastUpdate, 10000); // Update every 10 seconds

// Initialize when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
} else {
    init();
}