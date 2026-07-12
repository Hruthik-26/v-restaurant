// Gourmet Shopping Cart Manager (LocalStorage + AJAX Session Sync)
class GourmetCart {
    constructor() {
        this.items = JSON.parse(localStorage.getItem('gourmet_cart')) || [];
        this.init();
    }

    init() {
        // Sync cart immediately on load
        this.sync();
        this.bindEvents();
    }

    bindEvents() {
        // Apply Coupon Event
        const applyBtn = document.getElementById('apply-coupon-btn');
        if (applyBtn) {
            applyBtn.addEventListener('click', () => {
                const code = document.getElementById('coupon-input').value.trim();
                if (code) this.applyCoupon(code);
            });
        }

        // Clear Cart Event
        const clearBtn = document.getElementById('clear-cart-btn');
        if (clearBtn) {
            clearBtn.addEventListener('click', () => this.clear());
        }

        // Event delegation for items increment/decrement inside drawer
        const drawerItems = document.getElementById('drawer-cart-items');
        if (drawerItems) {
            drawerItems.addEventListener('click', (e) => {
                const target = e.target;
                const card = target.closest('[data-cart-item-id]');
                if (!card) return;
                const itemId = card.getAttribute('data-cart-item-id');

                if (target.closest('.btn-qty-plus')) {
                    this.updateQty(itemId, 1);
                } else if (target.closest('.btn-qty-minus')) {
                    this.updateQty(itemId, -1);
                } else if (target.closest('.btn-remove-item')) {
                    this.remove(itemId);
                }
            });
        }

        // Bind Quick View Modals
        document.addEventListener('click', (e) => {
            const btn = e.target.closest('.quick-view-btn');
            if (btn) {
                const id = btn.getAttribute('data-id');
                this.loadQuickView(id);
            }
        });
    }

    add(id, name, price, imageUrl, isVeg) {
        if (!window.isUserAuthenticated) {
            showToast("Please Login First", true);
            return;
        }
        const existing = this.items.find(item => item.id == id);
        if (existing) {
            existing.qty += 1;
        } else {
            this.items.push({
                id: id,
                name: name,
                price: parseFloat(price),
                image_url: imageUrl,
                is_veg: isVeg,
                qty: 1
            });
        }
        this.save();
        this.sync();
        showToast(`"${name}" added to gourmet bag!`);
    }

    updateQty(id, delta) {
        const item = this.items.find(item => item.id == id);
        if (!item) return;

        item.qty += delta;
        if (item.qty <= 0) {
            this.items = this.items.filter(i => i.id != id);
        }
        this.save();
        this.sync();
    }

    remove(id) {
        this.items = this.items.filter(item => item.id != id);
        this.save();
        this.sync();
        showToast("Dish removed from gourmet bag.", true);
    }

    clear() {
        this.items = [];
        this.save();
        this.sync();
        showToast("Gourmet bag cleared.", true);
    }

    save() {
        localStorage.setItem('gourmet_cart', JSON.stringify(this.items));
    }

    // Sync state with Django session
    sync() {
        const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]')?.value || "";

        fetch('/cart/sync/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrfToken
            },
            body: JSON.stringify({ cart: this.items })
        })
        .then(res => res.json())
        .then(data => {
            if (data.success) {
                this.updateDOM(data);
            }
        })
        .catch(err => console.error("Sync error: ", err));
    }

    applyCoupon(code) {
        const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]')?.value || "";

        fetch('/coupon/apply/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrfToken
            },
            body: JSON.stringify({ code: code })
        })
        .then(res => res.json())
        .then(data => {
            if (data.success) {
                showToast(data.message);
                this.sync(); // Refresh pricing summaries
            } else {
                showToast(data.message, true);
            }
        })
        .catch(err => console.error("Coupon error: ", err));
    }

    updateDOM(data) {
        // Navbar Badge count
        const badge = document.getElementById('cart-badge-count');
        if (badge) badge.textContent = data.items_count;

        // Drawer Items
        const wrapper = document.getElementById('drawer-cart-items');
        if (!wrapper) return;

        if (data.items.length === 0) {
            wrapper.innerHTML = `
                <div class="text-center py-5 text-secondary">
                    <i class="bi bi-cart-x fs-1 d-block mb-3 text-secondary-dim"></i>
                    <p class="mb-0">Your gourmet bag is empty.</p>
                </div>
            `;
        } else {
            let html = '';
            data.items.forEach(item => {
                html += `
                    <div class="d-flex align-items-center gap-3 mb-3 pb-3 border-bottom border-white-5" data-cart-item-id="${item.id}">
                        <div class="rounded overflow-hidden" style="width: 60px; height: 60px; flex-shrink: 0;">
                            <img src="${item.image_url}" class="w-100 h-100 object-fit-cover">
                        </div>
                        <div class="flex-grow-1">
                            <h6 class="text-white mb-1 small">${item.name}</h6>
                            <span class="text-primary fw-semibold small">₹${item.price}</span>
                        </div>
                        <div class="d-flex align-items-center gap-2">
                            <button class="btn btn-icon btn-sm glass-btn btn-qty-minus"><i class="bi bi-dash"></i></button>
                            <span class="small fw-bold text-white px-1">${item.qty}</span>
                            <button class="btn btn-icon btn-sm glass-btn btn-qty-plus"><i class="bi bi-plus"></i></button>
                        </div>
                    </div>
                `;
            });
            wrapper.innerHTML = html;
        }

        // Summary labels update
        const subtotalEl = document.getElementById('summary-subtotal');
        if (subtotalEl) subtotalEl.textContent = `₹${data.subtotal.toFixed(2)}`;

        const taxEl = document.getElementById('summary-tax');
        if (taxEl) taxEl.textContent = `₹${data.tax.toFixed(2)}`;

        const totalEl = document.getElementById('summary-total');
        if (totalEl) totalEl.textContent = `₹${data.grand_total.toFixed(2)}`;

        // Delivery
        const deliveryRow = document.getElementById('summary-delivery-row');
        if (deliveryRow) {
            if (data.delivery_charge > 0) {
                deliveryRow.classList.remove('d-none');
                const deliveryVal = document.getElementById('summary-delivery');
                if (deliveryVal) deliveryVal.textContent = `₹${data.delivery_charge.toFixed(2)}`;
            } else {
                deliveryRow.classList.add('d-none');
            }
        }

        // Coupon Discount
        const discountRow = document.getElementById('summary-discount-row');
        if (discountRow) {
            if (data.discount > 0) {
                discountRow.classList.remove('d-none');
                const discountVal = document.getElementById('summary-discount');
                if (discountVal) discountVal.textContent = `-₹${data.discount.toFixed(2)}`;
                const couponInput = document.getElementById('coupon-input');
                if (couponInput) couponInput.value = data.coupon_code;
            } else {
                discountRow.classList.add('d-none');
            }
        }
    }

    loadQuickView(id) {
        const modalBody = document.getElementById('modal-item-content');
        if (!modalBody) return;

        modalBody.innerHTML = `
            <div class="col-12 text-center py-5">
                <div class="spinner-border text-primary" role="status"><span class="visually-hidden">Loading...</span></div>
            </div>
        `;

        fetch(`/menu/item/${id}/detail/`)
        .then(res => res.text())
        .then(html => {
            modalBody.innerHTML = html;
        })
        .catch(err => {
            console.error(err);
            modalBody.innerHTML = `<div class="col-12 text-center py-4 text-secondary">Error loading dish details.</div>`;
        });
    }
}

// Global cart instantiation
const cart = new GourmetCart();

// Toggle Favorite AJAX handler
function toggleFavorite(itemId, btn) {
    if (!window.isUserAuthenticated) {
        showToast("Please Login First", true);
        return;
    }
    
    const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]')?.value || "";
    
    fetch(`/favorites/toggle/${itemId}/`, {
        method: 'POST',
        headers: {
            'X-CSRFToken': csrfToken
        }
    })
    .then(res => res.json())
    .then(data => {
        if (data.success) {
            showToast(data.message);
            // Update active styling
            const hearts = document.querySelectorAll(`[data-item-id="${itemId}"].favorite-toggle-btn-grid, [onclick*="'${itemId}'"].favorite-toggle-btn`);
            hearts.forEach(heart => {
                if (data.favorited) {
                    heart.classList.add('active', 'text-danger');
                    heart.classList.remove('text-white');
                    const icon = heart.querySelector('i');
                    if (icon) {
                        icon.className = 'bi bi-heart-fill';
                    }
                } else {
                    heart.classList.remove('active', 'text-danger');
                    heart.classList.add('text-white');
                    const icon = heart.querySelector('i');
                    if (icon) {
                        icon.className = 'bi bi-heart';
                    }
                }
            });
        }
    })
    .catch(err => {
        console.error(err);
        showToast("Error updating favorites.", true);
    });
}

// Submit Review AJAX handler
function submitReview(event, itemId) {
    event.preventDefault();
    
    const form = event.target;
    const formData = new FormData(form);
    const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]')?.value || "";
    
    fetch(`/menu/item/${itemId}/review/`, {
        method: 'POST',
        body: formData,
        headers: {
            'X-CSRFToken': csrfToken
        }
    })
    .then(res => res.json())
    .then(data => {
        if (data.success) {
            showToast(data.message);
            // Reload the quick view modal to show the new review
            cart.loadQuickView(itemId);
        } else {
            showToast(data.message, true);
        }
    })
    .catch(err => {
        console.error(err);
        showToast("Error submitting review.", true);
    });
}
