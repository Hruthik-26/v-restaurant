// Kitchen Live Dashboard Controller (Drag-Drop, Poll, Timers)

document.addEventListener('DOMContentLoaded', () => {
    initElapsedTimers();
    setInterval(initElapsedTimers, 10000); // Update timers every 10s
    
    // Start AJAX Polling
    setInterval(pollKitchenOrders, 5000);
});

// Sound alerts for new order actions
const orderBellSound = new Audio('https://assets.mixkit.co/active_storage/sfx/2869/2869-120.wav');

// Drag and drop states
let draggedOrderId = null;

function handleDragStart(e, id) {
    draggedOrderId = id;
    e.dataTransfer.setData('text/plain', id);
    e.dataTransfer.effectAllowed = 'move';
}

function allowDrop(e) {
    e.preventDefault();
    const col = e.currentTarget;
    col.classList.add('drag-over');
}

function dragLeave(e) {
    const col = e.currentTarget;
    col.classList.remove('drag-over');
}

function handleDrop(e, targetStatus) {
    e.preventDefault();
    const col = e.currentTarget;
    col.classList.remove('drag-over');
    
    const id = e.dataTransfer.getData('text/plain') || draggedOrderId;
    if (id) {
        updateOrderStatus(id, targetStatus);
    }
}

// Progress status via API
function updateOrderStatus(id, status) {
    const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]')?.value || "";

    fetch(`/kitchen/api/orders/${id}/status/`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': csrfToken
        },
        body: JSON.stringify({ status: status })
    })
    .then(res => res.json())
    .then(data => {
        if (data.success) {
            // Instantly poll to redraw state
            pollKitchenOrders();
        } else {
            console.error("Status update failed:", data.error);
        }
    })
    .catch(err => console.error("Error updating status:", err));
}

// Adjust Priority order weight
function adjustPriority(id, delta) {
    const card = document.getElementById(`order-card-${id}`);
    if (!card) return;
    
    // Read current priority weight attribute
    const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]')?.value || "";

    fetch(`/kitchen/api/orders/${id}/status/`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': csrfToken
        },
        body: JSON.stringify({ priority: delta }) // increment/decrement delta weight
    })
    .then(res => res.json())
    .then(data => {
        if (data.success) {
            pollKitchenOrders();
        }
    })
    .catch(err => console.error("Priority update error: ", err));
}

// Keep Track of cooking elapsed minutes
function initElapsedTimers() {
    const badges = document.querySelectorAll('.elapsed-timer-badge');
    badges.forEach(badge => {
        const createdStr = badge.getAttribute('data-created-time');
        if (!createdStr) return;
        
        const created = new Date(createdStr);
        const diffMs = new Date().getTime() - created.getTime();
        const diffMins = Math.floor(diffMs / 60000);
        
        if (diffMins < 60) {
            badge.textContent = `${diffMins}m ago`;
            if (diffMins >= 15 && diffMins < 30) {
                badge.className = 'badge bg-warning-dim border border-warning text-warning elapsed-timer-badge';
            } else if (diffMins >= 30) {
                badge.className = 'badge bg-danger-dim border border-danger text-danger elapsed-timer-badge animate-pulse';
            } else {
                badge.className = 'badge bg-slate-950 border border-white-10 text-primary elapsed-timer-badge';
            }
        } else {
            const hrs = Math.floor(diffMins / 60);
            badge.textContent = `${hrs}h ago`;
            badge.className = 'badge bg-danger-dim border border-danger text-danger elapsed-timer-badge animate-pulse';
        }
    });
}

// Live polling orders
let previousOrdersCount = null;

function pollKitchenOrders() {
    fetch('/kitchen/api/orders/')
    .then(res => res.json())
    .then(data => {
        if (data.success) {
            // Check if there are new orders to trigger bell notification
            if (previousOrdersCount !== null && data.orders.length > previousOrdersCount) {
                orderBellSound.play().catch(() => {});
            }
            previousOrdersCount = data.orders.length;
            
            // Re-render columns DOM
            renderColumns(data.orders);
            
            // Update stats indicators
            const revenueEl = document.getElementById('stats-revenue');
            if (revenueEl) revenueEl.textContent = `₹${data.stats.revenue.toFixed(2)}`;
            
            const ordersEl = document.getElementById('stats-orders');
            if (ordersEl) ordersEl.textContent = data.stats.completed + data.stats.pending;
            
            const pendingEl = document.getElementById('stats-pending');
            if (pendingEl) pendingEl.textContent = data.stats.pending;
            
            const completedEl = document.getElementById('stats-completed');
            if (completedEl) completedEl.textContent = data.stats.completed;
        }
    })
    .catch(err => console.error("Poll Error:", err));
}

function renderColumns(orders) {
    const colReceived = document.getElementById('col-RECEIVED');
    const colPreparing = document.getElementById('col-PREPARING');
    const colReady = document.getElementById('col-READY');
    
    if (!colReceived || !colPreparing || !colReady) return;

    let receivedHtml = '';
    let preparingHtml = '';
    let readyHtml = '';

    let receivedCount = 0;
    let preparingCount = 0;
    let readyCount = 0;

    orders.forEach(order => {
        // Build items list representation
        let itemsLi = '';
        order.items.forEach(item => {
            itemsLi += `
                <li class="text-secondary d-flex justify-content-between">
                    <span>${item.name}</span>
                    <strong class="text-white">x${item.qty}</strong>
                </li>
            `;
        });

        // Badge styling for dining option
        let badgeClass = 'bg-info-dim text-info';
        if (order.dining_option === 'Dine-In') badgeClass = 'bg-primary-dim text-primary';
        else if (order.dining_option === 'Delivery') badgeClass = 'bg-warning-dim text-warning';

        // Action button rendering
        let actionBtn = '';
        if (order.status === 'RECEIVED') {
            actionBtn = `
                <button class="btn btn-primary btn-sm px-3 rounded-pill fw-semibold btn-status-action" onclick="updateOrderStatus('${order.id}', 'PREPARING')">
                    Prepare <i class="bi bi-play-fill"></i>
                </button>
            `;
        } else if (order.status === 'PREPARING') {
            actionBtn = `
                <button class="btn btn-warning btn-sm px-3 rounded-pill fw-semibold btn-status-action" onclick="updateOrderStatus('${order.id}', 'COOKING')">
                    Cook <i class="bi bi-egg-fried"></i>
                </button>
            `;
        } else if (order.status === 'COOKING') {
            actionBtn = `
                <button class="btn btn-info btn-sm px-3 rounded-pill fw-semibold btn-status-action" onclick="updateOrderStatus('${order.id}', 'PACKED')">
                    Pack <i class="bi bi-box2-fill"></i>
                </button>
            `;
        } else if (order.status === 'PACKED') {
            actionBtn = `
                <button class="btn btn-success btn-sm px-3 rounded-pill fw-semibold btn-status-action" onclick="updateOrderStatus('${order.id}', 'READY')">
                    Ready <i class="bi bi-check-lg"></i>
                </button>
            `;
        } else if (order.status === 'READY') {
            actionBtn = `
                <button class="btn btn-warning btn-sm px-3 rounded-pill fw-semibold btn-status-action" onclick="updateOrderStatus('${order.id}', 'OUT_FOR_DELIVERY')">
                    Ship <i class="bi bi-truck"></i>
                </button>
            `;
        } else if (order.status === 'OUT_FOR_DELIVERY') {
            actionBtn = `
                <button class="btn btn-success btn-sm px-3 rounded-pill fw-semibold btn-status-action text-uppercase" onclick="updateOrderStatus('${order.id}', 'DELIVERED')">
                    Deliver <i class="bi bi-check-circle-fill"></i>
                </button>
            `;
        }

        const cardHtml = `
            <div class="card bg-slate-900 border border-white-10 rounded-4 p-3 mb-3 order-kitchen-card glass-card" 
                 id="order-card-${order.id}" 
                 draggable="true" 
                 ondragstart="handleDragStart(event, '${order.id}')"
                 data-order-id="${order.id}">
                
                <div class="d-flex justify-content-between align-items-center mb-2 pb-2 border-bottom border-white-10">
                    <span class="fw-bold text-white small">${order.order_number}</span>
                    <span class="badge bg-slate-950 border border-white-10 text-primary elapsed-timer-badge" 
                          data-created-time="${new Date(new Date().getTime() - order.elapsed_minutes*60000).toISOString()}">
                        ${order.elapsed_minutes}m ago
                    </span>
                </div>
                
                <div class="mb-3">
                    <h6 class="text-white mb-0">${order.customer_name}</h6>
                    <span class="badge ${badgeClass} px-2 py-1 mt-1 small" style="font-size: 0.7rem;">
                        ${order.dining_option} ${order.dining_option === 'Dine-In' ? '(Table #' + order.table_number + ')' : ''}
                    </span>
                </div>
                
                <div class="mb-3 bg-slate-950-50 p-2 rounded border border-white-5">
                    <ul class="list-unstyled mb-0 small">
                        ${itemsLi}
                    </ul>
                </div>
                
                <div class="d-flex justify-content-between align-items-center">
                    <div>
                        ${actionBtn}
                    </div>
                    
                    <div class="d-flex gap-1">
                        <button class="btn btn-icon btn-sm glass-btn border-white-10" onclick="adjustPriority('${order.id}', 1)" title="Increase Priority">
                            <i class="bi bi-chevron-up text-danger"></i>
                        </button>
                        <button class="btn btn-icon btn-sm glass-btn border-white-10" onclick="adjustPriority('${order.id}', -1)" title="Decrease Priority">
                            <i class="bi bi-chevron-down text-secondary"></i>
                        </button>
                    </div>
                </div>
            </div>
        `;

        if (order.status === 'RECEIVED') {
            receivedHtml += cardHtml;
            receivedCount++;
        } else if (order.status === 'PREPARING' || order.status === 'COOKING') {
            preparingHtml += cardHtml;
            preparingCount++;
        } else if (order.status === 'PACKED' || order.status === 'READY' || order.status === 'OUT_FOR_DELIVERY') {
            readyHtml += cardHtml;
            readyCount++;
        }
    });

    colReceived.innerHTML = receivedHtml || '<div class="text-center py-5 text-secondary empty-msg">No new orders queued.</div>';
    colPreparing.innerHTML = preparingHtml || '<div class="text-center py-5 text-secondary empty-msg">No active preparations.</div>';
    colReady.innerHTML = readyHtml || '<div class="text-center py-5 text-secondary empty-msg">No items ready for pickup.</div>';

    const countReceivedEl = document.getElementById('count-received');
    if (countReceivedEl) countReceivedEl.textContent = receivedCount;

    const countPreparingEl = document.getElementById('count-preparing');
    if (countPreparingEl) countPreparingEl.textContent = preparingCount;

    const countReadyEl = document.getElementById('count-ready');
    if (countReadyEl) countReadyEl.textContent = readyCount;

    initElapsedTimers();
}
