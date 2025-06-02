/**
 * Advanced Trading System - Main JavaScript
 * Optimized for Raspberry Pi 4
 */

// Globális változók
let chartInstances = {};
let websocketConnections = {};
let updateIntervals = {};

// Oldal betöltésekor
document.addEventListener('DOMContentLoaded', function() {
    // Inicializálja a tooltipeket
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function(tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });

    // Inicializálja a popovert
    const popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
    popoverTriggerList.map(function(popoverTriggerEl) {
        return new bootstrap.Popover(popoverTriggerEl);
    });

    // Értesítések olvasottnak jelölése
    setupNotificationHandlers();

    // Automatikus frissítések beállítása
    setupAutoRefresh();

    // Grafikonok inicializálása
    initializeCharts();

    // Űrlapok validálása
    setupFormValidation();

    // Táblázatok rendezése és szűrése
    setupDataTables();

    // Mobilbarát optimalizációk
    setupMobileOptimizations();
});

/**
 * Értesítések kezelőinek beállítása
 */
function setupNotificationHandlers() {
    // Egyetlen értesítés olvasottnak jelölése
    document.querySelectorAll('.mark-notification-read').forEach(button => {
        button.addEventListener('click', function(e) {
            e.preventDefault();
            const notificationId = this.getAttribute('data-notification-id');
            
            fetch(`/api/notifications/mark-read/${notificationId}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCsrfToken()
                }
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    // Frissíti az értesítés megjelenését
                    const notificationElement = document.querySelector(`.notification-item[data-notification-id="${notificationId}"]`);
                    if (notificationElement) {
                        notificationElement.classList.add('read');
                        // Csökkenti a számlálót
                        updateNotificationCounter(-1);
                    }
                }
            })
            .catch(error => console.error('Error marking notification as read:', error));
        });
    });

    // Összes értesítés olvasottnak jelölése
    const markAllReadButton = document.querySelector('.mark-all-notifications-read');
    if (markAllReadButton) {
        markAllReadButton.addEventListener('click', function(e) {
            e.preventDefault();
            
            fetch('/api/notifications/mark-all-read', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCsrfToken()
                }
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    // Frissíti az összes értesítés megjelenését
                    document.querySelectorAll('.notification-item').forEach(item => {
                        item.classList.add('read');
                    });
                    // Nullázza a számlálót
                    updateNotificationCounter(-999); // Nagy negatív szám, hogy biztosan 0 legyen
                }
            })
            .catch(error => console.error('Error marking all notifications as read:', error));
        });
    }
}

/**
 * Értesítés számláló frissítése
 * @param {number} change - A változás mértéke (lehet negatív)
 */
function updateNotificationCounter(change) {
    const counter = document.querySelector('.notifications-menu .badge');
    if (counter) {
        let count = parseInt(counter.textContent) || 0;
        count += change;
        count = Math.max(0, count); // Nem lehet negatív
        counter.textContent = count;
        
        // Ha nincs több értesítés, elrejti a számlálót
        if (count === 0) {
            counter.style.display = 'none';
        } else {
            counter.style.display = 'inline-block';
        }
    }
}

/**
 * Automatikus frissítések beállítása
 */
function setupAutoRefresh() {
    // Rendszer állapot frissítése
    if (document.querySelector('.system-status-card')) {
        updateIntervals.systemStatus = setInterval(updateSystemStatus, 10000); // 10 másodpercenként
    }
    
    // Piaci adatok frissítése
    if (document.querySelector('.market-data-card')) {
        updateIntervals.marketData = setInterval(updateMarketData, 30000); // 30 másodpercenként
    }
    
    // Portfólió adatok frissítése
    if (document.querySelector('.portfolio-summary-card')) {
        updateIntervals.portfolioData = setInterval(updatePortfolioData, 60000); // 60 másodpercenként
    }
    
    // Értesítések frissítése
    updateIntervals.notifications = setInterval(updateNotifications, 30000); // 30 másodpercenként
}

/**
 * Rendszer állapot frissítése
 */
function updateSystemStatus() {
    fetch('/api/system/status')
        .then(response => response.json())
        .then(data => {
            // CPU használat frissítése
            const cpuElement = document.querySelector('.info-box:contains("CPU") .info-box-number');
            const cpuProgressBar = document.querySelector('.info-box:contains("CPU") .progress-bar');
            if (cpuElement && cpuProgressBar) {
                cpuElement.textContent = data.cpu_usage.toFixed(1) + '%';
                cpuProgressBar.style.width = data.cpu_usage + '%';
            }
            
            // Memória használat frissítése
            const memoryElement = document.querySelector('.info-box:contains("Memória") .info-box-number');
            const memoryProgressBar = document.querySelector('.info-box:contains("Memória") .progress-bar');
            if (memoryElement && memoryProgressBar) {
                memoryElement.textContent = data.memory_usage.toFixed(1) + '%';
                memoryProgressBar.style.width = data.memory_usage + '%';
            }
            
            // Tárhely használat frissítése
            const diskElement = document.querySelector('.info-box:contains("Tárhely") .info-box-number');
            const diskProgressBar = document.querySelector('.info-box:contains("Tárhely") .progress-bar');
            if (diskElement && diskProgressBar) {
                diskElement.textContent = data.disk_usage.toFixed(1) + '%';
                diskProgressBar.style.width = data.disk_usage + '%';
            }
            
            // Trading Engine állapot frissítése
            const statusBadge = document.querySelector('.system-status-card .badge');
            if (statusBadge) {
                statusBadge.classList.remove('bg-success', 'bg-danger');
                statusBadge.classList.add(data.trading_engine_status === 'running' ? 'bg-success' : 'bg-danger');
                statusBadge.textContent = data.trading_engine_status;
            }
        })
        .catch(error => console.error('Error updating system status:', error));
}

/**
 * Piaci adatok frissítése
 */
function updateMarketData() {
    fetch('/api/market/list')
        .then(response => response.json())
        .then(data => {
            const marketTable = document.querySelector('.market-data-card table tbody');
            if (!marketTable) return;
            
            // Táblázat frissítése
            marketTable.innerHTML = '';
            
            data.forEach(market => {
                const row = document.createElement('tr');
                row.innerHTML = `
                    <td>${market.symbol}</td>
                    <td>$${market.price.toFixed(2)}</td>
                    <td class="${market.change >= 0 ? 'text-success' : 'text-danger'}">
                        ${market.change.toFixed(2)}%
                    </td>
                    <td>
                        <div class="sparkline" data-change="${market.change}"></div>
                    </td>
                `;
                
                marketTable.appendChild(row);
            });
            
            // Sparkline grafikonok újragenerálása
            generateSparklines();
        })
        .catch(error => console.error('Error updating market data:', error));
}

/**
 * Sparkline grafikonok generálása
 */
function generateSparklines() {
    document.querySelectorAll('.sparkline').forEach(element => {
        const change = parseFloat(element.getAttribute('data-change'));
        const color = change >= 0 ? 'rgba(40, 167, 69, 1)' : 'rgba(220, 53, 69, 1)';
        
        // Szimulált adatok
        const data = [];
        for (let i = 0; i < 20; i++) {
            const value = 100 + (Math.sin(i/3) * 5) + (change * i / 10);
            data.push(value);
        }
        
        // Törli a meglévő tartalmat
        element.innerHTML = '';
        
        // Létrehozza az új canvas elemet
        const canvas = document.createElement('canvas');
        canvas.height = 30;
        element.appendChild(canvas);
        
        // Létrehozza a grafikont
        const ctx = canvas.getContext('2d');
        new Chart(ctx, {
            type: 'line',
            data: {
                labels: Array.from({length: 20}, (_, i) => ''),
                datasets: [{
                    data: data,
                    borderColor: color,
                    backgroundColor: 'transparent',
                    borderWidth: 1.5,
                    pointRadius: 0
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: false
                    },
                    tooltip: {
                        enabled: false
                    }
                },
                scales: {
                    x: {
                        display: false
                    },
                    y: {
                        display: false
                    }
                }
            }
        });
    });
}

/**
 * Portfólió adatok frissítése
 */
function updatePortfolioData() {
    fetch('/api/portfolio/summary')
        .then(response => response.json())
        .then(data => {
            // Portfólió érték frissítése
            const valueElement = document.querySelector('.portfolio-summary-card .info-box-number');
            if (valueElement) {
                valueElement.textContent = '$' + data.total_value.toFixed(2);
            }
            
            // Portfólió változás frissítése
            const changeElement = document.querySelector('.portfolio-summary-card .info-box:contains("változás") .info-box-number');
            if (changeElement) {
                changeElement.textContent = data.total_pnl_percent.toFixed(2) + '%';
                
                // Szín frissítése
                const iconElement = changeElement.closest('.info-box').querySelector('.info-box-icon');
                if (iconElement) {
                    iconElement.classList.remove('bg-success', 'bg-danger');
                    iconElement.classList.add(data.total_pnl_percent >= 0 ? 'bg-success' : 'bg-danger');
                    
                    const icon = iconElement.querySelector('i');
                    if (icon) {
                        icon.classList.remove('fa-arrow-up', 'fa-arrow-down');
                        icon.classList.add(data.total_pnl_percent >= 0 ? 'fa-arrow-up' : 'fa-arrow-down');
                    }
                }
            }
            
            // Portfólió grafikon frissítése
            updatePortfolioChart();
        })
        .catch(error => console.error('Error updating portfolio data:', error));
}

/**
 * Portfólió grafikon frissítése
 */
function updatePortfolioChart() {
    fetch('/api/portfolio/history')
        .then(response => response.json())
        .then(data => {
            const chartInstance = chartInstances.portfolioChart;
            if (!chartInstance) return;
            
            // Adatok frissítése
            chartInstance.data.labels = data.map(item => item.date);
            chartInstance.data.datasets[0].data = data.map(item => item.value);
            
            // Grafikon frissítése
            chartInstance.update();
        })
        .catch(error => console.error('Error updating portfolio chart:', error));
}

/**
 * Értesítések frissítése
 */
function updateNotifications() {
    fetch('/api/notifications?unread_only=true&limit=5')
        .then(response => response.json())
        .then(data => {
            // Értesítések számának frissítése
            const count = data.length;
            const badge = document.querySelector('.notifications-menu .badge');
            if (badge) {
                badge.textContent = count;
                badge.style.display = count > 0 ? 'inline-block' : 'none';
            }
            
            // Értesítések listájának frissítése
            const notificationsList = document.querySelector('.notifications-menu .dropdown-menu .notifications-list');
            if (!notificationsList) return;
            
            notificationsList.innerHTML = '';
            
            if (count > 0) {
                data.forEach(notification => {
                    let icon = '';
                    let bgClass = '';
                    
                    switch (notification.type) {
                        case 'info':
                            icon = 'fa-info-circle';
                            bgClass = 'bg-info';
                            break;
                        case 'warning':
                            icon = 'fa-exclamation-triangle';
                            bgClass = 'bg-warning';
                            break;
                        case 'error':
                            icon = 'fa-times-circle';
                            bgClass = 'bg-danger';
                            break;
                        case 'success':
                            icon = 'fa-check-circle';
                            bgClass = 'bg-success';
                            break;
                    }
                    
                    const time = new Date(notification.timestamp).toLocaleTimeString();
                    
                    const notificationItem = document.createElement('div');
                    notificationItem.innerHTML = `
                        <a href="#" class="dropdown-item">
                            <div class="media">
                                <div class="media-left">
                                    <i class="fas ${icon} ${bgClass}"></i>
                                </div>
                                <div class="media-body">
                                    <p class="text-sm">${notification.message}</p>
                                    <p class="text-sm text-muted"><i class="far fa-clock mr-1"></i> ${time}</p>
                                </div>
                            </div>
                        </a>
                        <div class="dropdown-divider"></div>
                    `;
                    
                    notificationsList.appendChild(notificationItem.firstElementChild);
                    notificationsList.appendChild(notificationItem.lastElementChild);
                });
                
                const footerLink = document.createElement('a');
                footerLink.href = '/notifications';
                footerLink.className = 'dropdown-item dropdown-footer';
                footerLink.textContent = 'Összes értesítés';
                notificationsList.appendChild(footerLink);
            } else {
                const emptyItem = document.createElement('a');
                emptyItem.href = '#';
                emptyItem.className = 'dropdown-item';
                emptyItem.innerHTML = '<p class="text-center">Nincsenek új értesítések</p>';
                notificationsList.appendChild(emptyItem);
            }
        })
        .catch(error => console.error('Error updating notifications:', error));
}

/**
 * Grafikonok inicializálása
 */
function initializeCharts() {
    // Portfólió grafikon
    const portfolioChartElement = document.getElementById('portfolioChart');
    if (portfolioChartElement) {
        const ctx = portfolioChartElement.getContext('2d');
        chartInstances.portfolioChart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: Array.from({length: 30}, (_, i) => {
                    const d = new Date();
                    d.setDate(d.getDate() - 29 + i);
                    return d.toLocaleDateString();
                }),
                datasets: [{
                    label: 'Portfólió érték',
                    data: Array.from({length: 30}, (_, i) => {
                        // Szimulált adatok
                        return 10000 * (1 + (Math.sin(i/5) * 0.02) + (i/100));
                    }),
                    borderColor: 'rgba(54, 162, 235, 1)',
                    backgroundColor: 'rgba(54, 162, 235, 0.2)',
                    borderWidth: 2,
                    tension: 0.4,
                    fill: true
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    y: {
                        beginAtZero: false
                    }
                }
            }
        });
    }
    
    // Teljesítmény grafikon
    const performanceChartElement = document.getElementById('performanceChart');
    if (performanceChartElement) {
        const ctx = performanceChartElement.getContext('2d');
        chartInstances.performanceChart = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: ['Grid Trading', 'DCA', 'Momentum', 'Mean Reversion', 'Arbitrage', 'ML Prediction'],
                datasets: [{
                    label: 'Profit (%)',
                    data: [2.5, 1.8, -0.5, 0.0, 0.0, 0.0],
                    backgroundColor: [
                        'rgba(75, 192, 192, 0.2)',
                        'rgba(54, 162, 235, 0.2)',
                        'rgba(255, 99, 132, 0.2)',
                        'rgba(255, 206, 86, 0.2)',
                        'rgba(153, 102, 255, 0.2)',
                        'rgba(255, 159, 64, 0.2)'
                    ],
                    borderColor: [
                        'rgba(75, 192, 192, 1)',
                        'rgba(54, 162, 235, 1)',
                        'rgba(255, 99, 132, 1)',
                        'rgba(255, 206, 86, 1)',
                        'rgba(153, 102, 255, 1)',
                        'rgba(255, 159, 64, 1)'
                    ],
                    borderWidth: 1
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    y: {
                        beginAtZero: true
                    }
                }
            }
        });
    }
    
    // Rendszer erőforrás grafikon
    const resourceChartElement = document.getElementById('resourceChart');
    if (resourceChartElement) {
        const ctx = resourceChartElement.getContext('2d');
        chartInstances.resourceChart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: Array.from({length: 24}, (_, i) => {
                    const d = new Date();
                    d.setHours(d.getHours() - 23 + i);
                    return d.toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'});
                }),
                datasets: [
                    {
                        label: 'CPU (%)',
                        data: Array.from({length: 24}, () => Math.floor(Math.random() * 50) + 10),
                        borderColor: 'rgba(54, 162, 235, 1)',
                        backgroundColor: 'rgba(54, 162, 235, 0.1)',
                        borderWidth: 2,
                        tension: 0.4,
                        fill: true
                    },
                    {
                        label: 'Memória (%)',
                        data: Array.from({length: 24}, () => Math.floor(Math.random() * 30) + 30),
                        borderColor: 'rgba(75, 192, 192, 1)',
                        backgroundColor: 'rgba(75, 192, 192, 0.1)',
                        borderWidth: 2,
                        tension: 0.4,
                        fill: true
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    y: {
                        beginAtZero: true,
                        max: 100
                    }
                }
            }
        });
    }
    
    // Sparkline grafikonok
    generateSparklines();
}

/**
 * Űrlapok validálásának beállítása
 */
function setupFormValidation() {
    // Bootstrap validáció
    const forms = document.querySelectorAll('.needs-validation');
    
    Array.from(forms).forEach(form => {
        form.addEventListener('submit', event => {
            if (!form.checkValidity()) {
                event.preventDefault();
                event.stopPropagation();
            }
            
            form.classList.add('was-validated');
        }, false);
    });
    
    // Stratégia beállítások validálása
    const strategyForm = document.getElementById('strategySettingsForm');
    if (strategyForm) {
        strategyForm.addEventListener('submit', function(e) {
            e.preventDefault();
            
            // Adatok összegyűjtése
            const formData = new FormData(this);
            const data = {};
            
            for (const [key, value] of formData.entries()) {
                data[key] = value;
            }
            
            // Adatok küldése
            fetch('/api/strategy/' + data.strategy_id + '/update', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCsrfToken()
                },
                body: JSON.stringify(data)
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    // Sikeres mentés
                    showAlert('success', 'A stratégia beállításai sikeresen mentve!');
                } else {
                    // Hiba
                    showAlert('danger', 'Hiba történt a mentés során: ' + data.error);
                }
            })
            .catch(error => {
                console.error('Error saving strategy settings:', error);
                showAlert('danger', 'Hiba történt a mentés során!');
            });
        });
    }
}

/**
 * Táblázatok rendezésének és szűrésének beállítása
 */
function setupDataTables() {
    // Egyszerű táblázat rendezés
    document.querySelectorAll('.sortable-table').forEach(table => {
        const headers = table.querySelectorAll('th[data-sort]');
        
        headers.forEach(header => {
            header.addEventListener('click', function() {
                const sortKey = this.getAttribute('data-sort');
                const sortDirection = this.classList.contains('sort-asc') ? 'desc' : 'asc';
                
                // Rendezési irány beállítása
                headers.forEach(h => {
                    h.classList.remove('sort-asc', 'sort-desc');
                });
                
                this.classList.add('sort-' + sortDirection);
                
                // Táblázat rendezése
                const tbody = table.querySelector('tbody');
                const rows = Array.from(tbody.querySelectorAll('tr'));
                
                rows.sort((a, b) => {
                    const aValue = a.querySelector(`td[data-sort-value="${sortKey}"]`)?.getAttribute('data-sort-value') || 
                                  a.cells[Array.from(headers).indexOf(header)].textContent.trim();
                    
                    const bValue = b.querySelector(`td[data-sort-value="${sortKey}"]`)?.getAttribute('data-sort-value') || 
                                  b.cells[Array.from(headers).indexOf(header)].textContent.trim();
                    
                    // Szám vagy szöveg
                    if (!isNaN(aValue) && !isNaN(bValue)) {
                        return sortDirection === 'asc' ? 
                            parseFloat(aValue) - parseFloat(bValue) : 
                            parseFloat(bValue) - parseFloat(aValue);
                    } else {
                        return sortDirection === 'asc' ? 
                            aValue.localeCompare(bValue) : 
                            bValue.localeCompare(aValue);
                    }
                });
                
                // Táblázat újrarendezése
                rows.forEach(row => tbody.appendChild(row));
            });
        });
    });
    
    // Táblázat szűrés
    document.querySelectorAll('.filterable-table').forEach(table => {
        const filterInput = document.createElement('input');
        filterInput.type = 'text';
        filterInput.className = 'form-control mb-3';
        filterInput.placeholder = 'Keresés a táblázatban...';
        
        table.parentNode.insertBefore(filterInput, table);
        
        filterInput.addEventListener('input', function() {
            const filterValue = this.value.toLowerCase();
            const rows = table.querySelectorAll('tbody tr');
            
            rows.forEach(row => {
                const text = row.textContent.toLowerCase();
                row.style.display = text.includes(filterValue) ? '' : 'none';
            });
        });
    });
}

/**
 * Mobilbarát optimalizációk beállítása
 */
function setupMobileOptimizations() {
    // Képernyő méret ellenőrzése
    const isMobile = window.innerWidth < 768;
    
    if (isMobile) {
        // Táblázatok görgethetővé tétele
        document.querySelectorAll('table').forEach(table => {
            if (!table.parentElement.classList.contains('table-responsive')) {
                const wrapper = document.createElement('div');
                wrapper.className = 'table-responsive';
                table.parentNode.insertBefore(wrapper, table);
                wrapper.appendChild(table);
            }
        });
        
        // Kártyák egyszerűsítése
        document.querySelectorAll('.card').forEach(card => {
            card.classList.add('card-sm');
        });
        
        // Grafikonok magasságának csökkentése
        document.querySelectorAll('.chart-container').forEach(container => {
            container.style.height = '200px';
        });
        
        // Animációk kikapcsolása
        document.body.classList.add('animation-effects');
    }
}

/**
 * CSRF token lekérése
 * @returns {string} CSRF token
 */
function getCsrfToken() {
    return document.querySelector('meta[name="csrf-token"]')?.getAttribute('content') || '';
}

/**
 * Értesítés megjelenítése
 * @param {string} type - Az értesítés típusa (success, danger, warning, info)
 * @param {string} message - Az értesítés szövege
 */
function showAlert(type, message) {
    const alertsContainer = document.querySelector('.alerts-container');
    
    if (!alertsContainer) {
        // Létrehozza a konténert, ha még nem létezik
        const container = document.createElement('div');
        container.className = 'alerts-container position-fixed top-0 end-0 p-3';
        container.style.zIndex = '1050';
        document.body.appendChild(container);
    }
    
    // Értesítés létrehozása
    const alert = document.createElement('div');
    alert.className = `alert alert-${type} alert-dismissible fade show`;
    alert.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
    `;
    
    // Hozzáadás a konténerhez
    alertsContainer.appendChild(alert);
    
    // Automatikus eltüntetés
    setTimeout(() => {
        const bsAlert = new bootstrap.Alert(alert);
        bsAlert.close();
    }, 5000);
}

/**
 * WebSocket kapcsolat létrehozása
 * @param {string} endpoint - A WebSocket végpont
 * @param {function} onMessage - Üzenet kezelő függvény
 * @returns {WebSocket} WebSocket kapcsolat
 */
function createWebSocketConnection(endpoint, onMessage) {
    // Ellenőrzi, hogy létezik-e már kapcsolat
    if (websocketConnections[endpoint]) {
        return websocketConnections[endpoint];
    }
    
    // Protokoll meghatározása
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${protocol}//${window.location.host}${endpoint}`;
    
    // Kapcsolat létrehozása
    const ws = new WebSocket(wsUrl);
    
    ws.onopen = function() {
        console.log(`WebSocket connection established to ${endpoint}`);
    };
    
    ws.onmessage = function(event) {
        const data = JSON.parse(event.data);
        onMessage(data);
    };
    
    ws.onerror = function(error) {
        console.error(`WebSocket error on ${endpoint}:`, error);
    };
    
    ws.onclose = function() {
        console.log(`WebSocket connection closed to ${endpoint}`);
        delete websocketConnections[endpoint];
        
        // Újracsatlakozás 5 másodperc múlva
        setTimeout(() => {
            createWebSocketConnection(endpoint, onMessage);
        }, 5000);
    };
    
    // Kapcsolat tárolása
    websocketConnections[endpoint] = ws;
    
    return ws;
}

/**
 * Oldal elhagyásakor
 */
window.addEventListener('beforeunload', function() {
    // Időzítők törlése
    Object.values(updateIntervals).forEach(interval => {
        clearInterval(interval);
    });
    
    // WebSocket kapcsolatok bezárása
    Object.values(websocketConnections).forEach(ws => {
        ws.close();
    });
});
