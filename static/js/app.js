// Mapy Image Manager - Main Application JavaScript

// ===== TOAST NOTIFICATIONS =====
function showToast(message, type = 'info', duration = 4000) {
    const container = document.getElementById('toast-container');
    const toast = document.createElement('div');

    const typeClasses = {
        'success': 'toast-success',
        'error': 'toast-error',
        'warning': 'toast-warning',
        'info': 'toast-info'
    };

    toast.className = `toast ${typeClasses[type] || typeClasses['info']}`;
    toast.innerHTML = `
        <div class="flex-1">
            <p class="font-medium">${message}</p>
        </div>
        <button onclick="this.parentElement.remove()" class="text-lg opacity-70 hover:opacity-100">✕</button>
    `;

    container.appendChild(toast);

    setTimeout(() => {
        toast.classList.add('animate-fade-out');
        setTimeout(() => toast.remove(), 300);
    }, duration);
}

// ===== API HELPERS =====
async function apiCall(endpoint, method = 'GET', data = null) {
    const options = {
        method,
        headers: {
            'Content-Type': 'application/json'
        }
    };

    if (data && (method === 'POST' || method === 'PUT')) {
        options.body = JSON.stringify(data);
    }

    try {
        const response = await fetch(endpoint, options);
        const result = await response.json();

        if (!response.ok) {
            throw new Error(result.error || `HTTP ${response.status}`);
        }

        return result;
    } catch (error) {
        console.error('API Error:', error);
        throw error;
    }
}

// ===== IMAGE UTILITIES =====
function getImageUrl(imageUrl, fallback = '/static/images/placeholder.png') {
    if (!imageUrl || imageUrl === 'None') {
        return fallback;
    }
    return imageUrl;
}

function getStatusColor(status) {
    const colors = {
        'complete': '#10b981',  // green
        'partial': '#f59e0b',   // amber
        'pending': '#ef4444',   // red
        'no_image': '#6b7280'   // gray
    };
    return colors[status] || colors['pending'];
}

function getStatusLabel(status) {
    const labels = {
        'complete': 'Completo',
        'partial': 'Parcial',
        'pending': 'Pendiente',
        'no_image': 'Sin imagen'
    };
    return labels[status] || status;
}

// ===== PAGINATION HELPERS =====
function generatePaginationLinks(pagination) {
    const container = document.getElementById('pagination-container');
    if (!container) return;

    container.innerHTML = '';

    if (pagination.total_pages <= 1) {
        return;
    }

    // Previous button
    if (pagination.current_page > 1) {
        const prevBtn = createButton(
            '← Anterior',
            () => loadProducts(pagination.current_page - 1),
            'border border-gray-300 hover:bg-gray-100 text-gray-700'
        );
        container.appendChild(prevBtn);
    }

    // Page numbers with ellipsis
    const showEllipsis = pagination.total_pages > 7;

    for (let i = 1; i <= pagination.total_pages; i++) {
        let shouldShow = false;

        if (i === 1 || i === pagination.total_pages) {
            shouldShow = true;
        } else if (Math.abs(i - pagination.current_page) <= 2) {
            shouldShow = true;
        }

        if (shouldShow) {
            const isCurrent = i === pagination.current_page;
            const btn = createButton(
                String(i),
                () => loadProducts(i),
                isCurrent ? 'bg-blue-600 text-white font-semibold' : 'border border-gray-300 hover:bg-gray-100 text-gray-700'
            );
            container.appendChild(btn);
        } else if (showEllipsis && i === 2 && pagination.current_page > 4) {
            const ellipsis = document.createElement('span');
            ellipsis.textContent = '...';
            ellipsis.className = 'px-3 py-1 text-gray-600';
            container.appendChild(ellipsis);
        } else if (showEllipsis && i === pagination.total_pages - 1 && pagination.current_page < pagination.total_pages - 3) {
            const ellipsis = document.createElement('span');
            ellipsis.textContent = '...';
            ellipsis.className = 'px-3 py-1 text-gray-600';
            container.appendChild(ellipsis);
        }
    }

    // Next button
    if (pagination.current_page < pagination.total_pages) {
        const nextBtn = createButton(
            'Siguiente →',
            () => loadProducts(pagination.current_page + 1),
            'border border-gray-300 hover:bg-gray-100 text-gray-700'
        );
        container.appendChild(nextBtn);
    }
}

function createButton(text, onclick, classes) {
    const btn = document.createElement('button');
    btn.textContent = text;
    btn.onclick = onclick;
    btn.className = `px-3 py-1 rounded transition ${classes}`;
    return btn;
}

// ===== MODAL UTILITIES =====
function showModal(title, content, buttons = []) {
    const modal = document.createElement('div');
    modal.className = 'fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50';

    const dialog = document.createElement('div');
    dialog.className = 'bg-white rounded-lg shadow-xl max-w-lg w-full mx-4 max-h-96 overflow-y-auto';

    dialog.innerHTML = `
        <div class="sticky top-0 bg-white border-b border-gray-200 px-6 py-4 flex justify-between items-center">
            <h3 class="text-lg font-semibold text-gray-900">${title}</h3>
            <button onclick="this.closest('.fixed').remove()" class="text-gray-600 hover:text-gray-900 text-xl">✕</button>
        </div>
        <div class="p-6">
            ${content}
        </div>
        ${buttons.length > 0 ? `
            <div class="border-t border-gray-200 px-6 py-4 flex gap-2 justify-end">
                ${buttons.map(btn => `
                    <button onclick="${btn.onclick}" class="px-4 py-2 ${btn.class}">${btn.text}</button>
                `).join('')}
            </div>
        ` : ''}
    `;

    modal.appendChild(dialog);
    modal.onclick = (e) => {
        if (e.target === modal) modal.remove();
    };

    document.body.appendChild(modal);
    return modal;
}

// ===== LOCAL STORAGE HELPERS =====
function savePreference(key, value) {
    try {
        localStorage.setItem(`mapy_${key}`, JSON.stringify(value));
    } catch (e) {
        console.warn('localStorage not available:', e);
    }
}

function getPreference(key, defaultValue = null) {
    try {
        const value = localStorage.getItem(`mapy_${key}`);
        return value ? JSON.parse(value) : defaultValue;
    } catch (e) {
        console.warn('localStorage not available:', e);
        return defaultValue;
    }
}

// ===== FORMAT HELPERS =====
function formatPrice(price) {
    if (!price) return '₲0';
    return '₲' + parseFloat(price).toLocaleString('es-PY', {
        minimumFractionDigits: 0,
        maximumFractionDigits: 0
    });
}

function formatDate(dateString) {
    const date = new Date(dateString);
    return date.toLocaleDateString('es-PY', {
        year: 'numeric',
        month: 'short',
        day: 'numeric'
    });
}

function truncateText(text, length = 50) {
    if (!text) return '';
    return text.length > length ? text.substring(0, length) + '...' : text;
}

// ===== FORM HELPERS =====
function isValidEmail(email) {
    return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);
}

function isValidUrl(url) {
    try {
        new URL(url);
        return true;
    } catch {
        return false;
    }
}

function getFormData(formId) {
    const form = document.getElementById(formId);
    if (!form) return {};

    const formData = new FormData(form);
    const data = {};

    for (let [key, value] of formData.entries()) {
        data[key] = value;
    }

    return data;
}

// ===== ARRAY/OBJECT HELPERS =====
function chunk(array, size) {
    const chunks = [];
    for (let i = 0; i < array.length; i += size) {
        chunks.push(array.slice(i, i + size));
    }
    return chunks;
}

function groupBy(array, key) {
    return array.reduce((acc, item) => {
        const group = item[key];
        if (!acc[group]) acc[group] = [];
        acc[group].push(item);
        return acc;
    }, {});
}

// ===== DEBOUNCE HELPER =====
function debounce(func, delay) {
    let timeoutId;
    return function (...args) {
        clearTimeout(timeoutId);
        timeoutId = setTimeout(() => func.apply(this, args), delay);
    };
}

// ===== THROTTLE HELPER =====
function throttle(func, limit) {
    let inThrottle;
    return function (...args) {
        if (!inThrottle) {
            func.apply(this, args);
            inThrottle = true;
            setTimeout(() => inThrottle = false, limit);
        }
    };
}

// ===== KEYBOARD SHORTCUTS =====
document.addEventListener('keydown', (e) => {
    // Ctrl/Cmd + K for search
    if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
        e.preventDefault();
        const searchInput = document.getElementById('search-input');
        if (searchInput) searchInput.focus();
    }

    // Esc to close modals
    if (e.key === 'Escape') {
        const modals = document.querySelectorAll('.fixed[role="dialog"], [id$="-modal"]');
        modals.forEach(modal => {
            if (!modal.classList.contains('hidden')) {
                modal.classList.add('hidden');
            }
        });
    }
});

// ===== PAGE LOAD ANALYTICS =====
document.addEventListener('DOMContentLoaded', () => {
    console.log('Mapy Image Manager loaded');

    // Track navigation
    document.querySelectorAll('nav a').forEach(link => {
        link.addEventListener('click', (e) => {
            console.log('Navigation:', e.target.href);
        });
    });
});

// ===== ERROR BOUNDARY =====
window.addEventListener('error', (event) => {
    console.error('Global error:', event.error);
    showToast('Ocurrió un error inesperado', 'error');
});

window.addEventListener('unhandledrejection', (event) => {
    console.error('Unhandled promise rejection:', event.reason);
    showToast('Error: ' + event.reason, 'error');
});

// ===== IDLE TIMEOUT =====
let idleTimer = null;
let idleState = false;

function resetIdleTimer() {
    clearTimeout(idleTimer);

    idleTimer = setTimeout(() => {
        idleState = true;
        console.log('User is idle');
    }, 15 * 60 * 1000); // 15 minutes
}

document.addEventListener('mousemove', resetIdleTimer);
document.addEventListener('keypress', resetIdleTimer);
document.addEventListener('scroll', resetIdleTimer);
document.addEventListener('touchstart', resetIdleTimer);

resetIdleTimer();

// ===== EXPORT FUNCTION =====
async function exportCurrentData() {
    try {
        const response = await fetch('/api/export');
        if (response.ok) {
            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = 'Catalogo_Mapy_Updated.xlsx';
            document.body.appendChild(a);
            a.click();
            window.URL.revokeObjectURL(url);
            document.body.removeChild(a);
            showToast('Exportación completada', 'success');
        }
    } catch (error) {
        console.error('Export error:', error);
        showToast('Error al exportar', 'error');
    }
}

// ===== INITIALIZATION =====
console.log('Mapy Image Manager utilities loaded');
