/**
 * falling-petals.js
 * Lightweight, high-performance 2D Canvas animation for falling red rose petals.
 * Auto-adjusts density on mobile and runs smoothly at 60 FPS.
 */

(function () {
    const canvas = document.getElementById('falling-petals-canvas');
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    const petalImg = new Image();
    petalImg.src = '/static/images/petal.png';

    let petals = [];
    let animationFrameId = null;
    let width = window.innerWidth;
    let height = window.innerHeight;

    // Configuration
    const isMobile = width < 768;
    const maxPetals = isMobile ? 15 : 45;

    // Petal class
    class Petal {
        constructor(isInitial = false) {
            this.reset(isInitial);
        }

        reset(isInitial = false) {
            this.x = Math.random() * width;
            this.y = isInitial ? Math.random() * height : -50;
            this.size = 12 + Math.random() * 20; // 12px to 32px
            this.speedY = 0.8 + Math.random() * 1.2; // slow graceful fall
            this.speedX = (Math.random() - 0.5) * 0.4; // slight drift
            this.angle = Math.random() * Math.PI * 2;
            this.rotateSpeed = (Math.random() - 0.5) * 0.015;
            this.swaySpeed = 0.01 + Math.random() * 0.015;
            this.swayAmplitude = 0.5 + Math.random() * 1.2;
            this.swayTime = Math.random() * 100;
        }

        update() {
            this.y += this.speedY;
            this.swayTime += this.swaySpeed;
            this.x += this.speedX + Math.sin(this.swayTime) * this.swayAmplitude * 0.25;
            this.angle += this.rotateSpeed;

            // Recycle if out of bounds
            if (this.y > height + 50 || this.x < -50 || this.x > width + 50) {
                this.reset(false);
            }
        }

        draw() {
            ctx.save();
            ctx.translate(this.x, this.y);
            ctx.rotate(this.angle);
            ctx.drawImage(petalImg, -this.size / 2, -this.size / 2, this.size, this.size);
            ctx.restore();
        }
    }

    // Initialize petals
    function init() {
        petals = [];
        for (let i = 0; i < maxPetals; i++) {
            petals.push(new Petal(true)); // spread across screen initially
        }
    }

    // Animation Loop
    function loop() {
        ctx.clearRect(0, 0, width, height);

        for (let i = 0; i < petals.length; i++) {
            petals[i].update();
            petals[i].draw();
        }

        animationFrameId = requestAnimationFrame(loop);
    }

    // Resize handler
    function resize() {
        width = window.innerWidth;
        height = window.innerHeight;
        canvas.width = width;
        canvas.height = height;
        init();
    }

    // Start as soon as image is loaded
    petalImg.onload = function () {
        resize();
        loop();
    };

    // Fallback start if image already cached or fails to trigger onload
    if (petalImg.complete) {
        resize();
        loop();
    }

    window.addEventListener('resize', resize);
})();
