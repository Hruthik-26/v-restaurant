// Main App Controller
document.addEventListener('DOMContentLoaded', () => {
    initNavbarScroll();
    initPageTransitions();
    initGSAPHoverTilts();
    initAnimatedCounters();

    // Safety fallback: force hide loader overlay after 2 seconds if still visible
    setTimeout(() => {
        const loader = document.getElementById('loader');
        if (loader && loader.style.visibility !== 'hidden') {
            loader.style.opacity = '0';
            setTimeout(() => {
                loader.style.visibility = 'hidden';
            }, 500);
        }
    }, 2000);
});

// 1. Navbar Scroll Py Shrinking
function initNavbarScroll() {
    const nav = document.getElementById('main-nav');
    if (!nav) return;
    
    window.addEventListener('scroll', () => {
        if (window.scrollY > 50) {
            nav.classList.add('scrolled');
        } else {
            nav.classList.remove('scrolled');
        }
    });
}

// 4. GSAP Card Tilts
function initGSAPHoverTilts() {
    // Select cards
    const cards = document.querySelectorAll('.food-card, .category-card');
    cards.forEach(card => {
        card.addEventListener('mousemove', (e) => {
            const rect = card.getBoundingClientRect();
            const x = e.clientX - rect.left - (rect.width/2);
            const y = e.clientY - rect.top - (rect.height/2);
            
            // Calculate tilt angle ratios
            const rotX = -(y / (rect.height/2)) * 8;
            const rotY = (x / (rect.width/2)) * 8;

            gsap.to(card, {
                rotationX: rotX,
                rotationY: rotY,
                transformPerspective: 600,
                ease: 'power1.out',
                duration: 0.3
            });
        });
        
        card.addEventListener('mouseleave', () => {
            gsap.to(card, {
                rotationX: 0,
                rotationY: 0,
                ease: 'power1.out',
                duration: 0.5
            });
        });
    });
}

// 5. Statistics Numeric counters
function initAnimatedCounters() {
    const counters = document.querySelectorAll('.counter');
    if (counters.length === 0) return;

    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                const target = entry.target;
                const countTo = parseInt(target.getAttribute('data-target'));
                
                gsap.to(target, {
                    innerText: countTo,
                    duration: 2,
                    snap: { innerText: 1 },
                    ease: 'power2.out',
                    onUpdate: function() {
                        target.innerHTML = Math.ceil(target.innerText);
                    }
                });
                observer.unobserve(target);
            }
        });
    }, { threshold: 0.5 });

    counters.forEach(c => observer.observe(c));
}

// Seamless premium page transitions
function initPageTransitions() {
    const contentWrapper = document.querySelector('body > div.d-flex.flex-column');
    if (contentWrapper) {
        // Fade in page on load
        contentWrapper.style.opacity = '0';
        contentWrapper.style.transition = 'opacity 0.4s ease';
        requestAnimationFrame(() => {
            contentWrapper.style.opacity = '1';
        });
    }

    // Intercept navigation links for smooth page exit transitions
    const links = document.querySelectorAll('a:not([target="_blank"]):not([href^="#"]):not([href^="mailto:"]):not([href^="tel:"])');
    links.forEach(link => {
        link.addEventListener('click', (e) => {
            if (e.ctrlKey || e.shiftKey || e.metaKey || e.defaultPrevented) return;
            
            // Exclude logout, delete, or other non-GET links if they are standard form/action triggers
            if (link.getAttribute('onclick') || link.classList.contains('no-transition')) return;
            
            e.preventDefault();
            const targetUrl = link.href;

            if (contentWrapper) {
                contentWrapper.style.opacity = '0';
                setTimeout(() => {
                    window.location.href = targetUrl;
                }, 400);
            } else {
                window.location.href = targetUrl;
            }
        });
    });
}

// Toast alerts helper function
function showToast(message, isError = false) {
    const toastEl = document.getElementById('app-toast');
    const toastMsg = document.getElementById('toast-message');
    if (!toastEl) return;

    toastMsg.textContent = message;
    
    if (isError) {
        toastEl.classList.remove('bg-success');
        toastEl.classList.add('bg-danger');
    } else {
        toastEl.classList.remove('bg-danger');
        toastEl.classList.add('bg-success');
    }

    const toast = new bootstrap.Toast(toastEl);
    toast.show();
}
