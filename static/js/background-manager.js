/**
 * background-manager.js
 * Orchestrates WebGL scene generation, particle distribution, mouse parallax,
 * and performance downscaling.
 */
let bgSceneManager = null;
let candles = [];
let hearts = [];
let petals = [];
let lastIsMobileState = false;

function repositionBorders() {
    if (!bgSceneManager || !bgSceneManager.camera) return;

    // 1. Position Candles at z = 1
    const candleBounds = bgSceneManager.getBoundsAt(1);
    const candlePadding = 0.22;

    const leftCandles = candles.filter(c => c.isLeft && !c.isSmallTop);
    leftCandles.forEach((candle, idx) => {
        const seg = candleBounds.height / (leftCandles.length + 1);
        const y = candleBounds.bottom + (idx + 1) * seg;
        candle.mesh.position.set(candleBounds.left + candlePadding, y, 1);
    });

    const rightCandles = candles.filter(c => c.isRight && !c.isSmallTop);
    rightCandles.forEach((candle, idx) => {
        const seg = candleBounds.height / (rightCandles.length + 1);
        const y = candleBounds.bottom + (idx + 1) * seg;
        candle.mesh.position.set(candleBounds.right - candlePadding, y, 1);
    });

    const bottomCandles = candles.filter(c => c.isBottom);
    bottomCandles.forEach((candle, idx) => {
        const seg = candleBounds.width / (bottomCandles.length + 1);
        const x = candleBounds.left + (idx + 1) * seg;
        const organicY = Math.sin(idx * 1.7) * 0.03;
        candle.mesh.position.set(x, candleBounds.bottom + candlePadding + organicY, 1);
    });

    const topCandles = candles.filter(c => c.isSmallTop);
    topCandles.forEach((candle, idx) => {
        const seg = candleBounds.width / (topCandles.length + 1);
        const x = candleBounds.left + (idx + 1) * seg;
        candle.mesh.position.set(x, candleBounds.top - candlePadding, 1);
    });

    // 2. Position hearts at z = 1.5
    const heartBounds = bgSceneManager.getBoundsAt(1.5);
    const heartPadding = 0.32;

    const cornerTopHearts = hearts.filter(h => h.isCornerTop);
    if (cornerTopHearts.length >= 2) {
        cornerTopHearts[0].mesh.position.set(heartBounds.left + heartPadding, heartBounds.top - heartPadding, 1.5);
        cornerTopHearts[1].mesh.position.set(heartBounds.right - heartPadding, heartBounds.top - heartPadding, 1.5);
    }

    const cornerBottomHearts = hearts.filter(h => h.isCornerBottom);
    if (cornerBottomHearts.length >= 2) {
        cornerBottomHearts[0].mesh.position.set(heartBounds.left + heartPadding, heartBounds.bottom + heartPadding, 1.5);
        cornerBottomHearts[1].mesh.position.set(heartBounds.right - heartPadding, heartBounds.bottom + heartPadding, 1.5);
    }

    const leftHearts = hearts.filter(h => h.isLeft && !h.isCornerTop && !h.isCornerBottom);
    leftHearts.forEach((heart, idx) => {
        const seg = heartBounds.height / (leftHearts.length + 1);
        const y = heartBounds.bottom + (idx + 1) * seg + (seg * 0.2);
        heart.mesh.position.set(heartBounds.left + heartPadding, y, 1.5);
    });

    const rightHearts = hearts.filter(h => h.isRight && !h.isCornerTop && !h.isCornerBottom);
    rightHearts.forEach((heart, idx) => {
        const seg = heartBounds.height / (rightHearts.length + 1);
        const y = heartBounds.bottom + (idx + 1) * seg - (seg * 0.2);
        heart.mesh.position.set(heartBounds.right - heartPadding, y, 1.5);
    });
}

function rebuildEntities() {
    if (!bgSceneManager) return;

    bgSceneManager.objects.forEach(obj => {
        const mesh = obj.mesh || obj;
        if (mesh.geometry) mesh.geometry.dispose();
        if (mesh.material) {
            if (Array.isArray(mesh.material)) {
                mesh.material.forEach(m => m.dispose());
            } else {
                mesh.material.dispose();
            }
        }
        bgSceneManager.scene.remove(mesh);
    });
    bgSceneManager.objects = [];

    candles = [];
    hearts = [];
    petals = [];

    const isMobile = bgSceneManager.isMobile;

    const leftCandleCount = isMobile ? 3 : 7;
    const rightCandleCount = isMobile ? 3 : 7;
    const bottomCandleCount = isMobile ? 4 : 8;
    const topCandleCount = isMobile ? 0 : 4;

    const leftHeartCount = isMobile ? 1 : 3;
    const rightHeartCount = isMobile ? 1 : 3;

    const petalCount = isMobile ? 25 : 55;

    // 1. Candles
    for (let i = 0; i < leftCandleCount; i++) {
        const c = new ProceduralCandle(true, false, false, i);
        bgSceneManager.addObject(c);
        candles.push(c);
    }
    for (let i = 0; i < rightCandleCount; i++) {
        const c = new ProceduralCandle(false, true, false, i);
        bgSceneManager.addObject(c);
        candles.push(c);
    }
    for (let i = 0; i < bottomCandleCount; i++) {
        const c = new ProceduralCandle(false, false, true, i);
        bgSceneManager.addObject(c);
        candles.push(c);
    }
    for (let i = 0; i < topCandleCount; i++) {
        const c = new ProceduralCandle(false, false, false, i);
        c.isSmallTop = true;
        c.mesh.scale.set(0.65, 0.65, 0.65);
        bgSceneManager.addObject(c);
        candles.push(c);
    }

    // 2. Hearts
    const hTL = new ProceduralBorderHeart(false, false, false, 0);
    hTL.isCornerTop = true;
    bgSceneManager.addObject(hTL);
    hearts.push(hTL);

    const hTR = new ProceduralBorderHeart(false, false, false, 1);
    hTR.isCornerTop = true;
    bgSceneManager.addObject(hTR);
    hearts.push(hTR);

    const hBL = new ProceduralBorderHeart(false, false, false, 2);
    hBL.isCornerBottom = true;
    bgSceneManager.addObject(hBL);
    hearts.push(hBL);

    const hBR = new ProceduralBorderHeart(false, false, false, 3);
    hBR.isCornerBottom = true;
    bgSceneManager.addObject(hBR);
    hearts.push(hBR);

    for (let i = 0; i < leftHeartCount; i++) {
        const h = new ProceduralBorderHeart(true, false, false, i);
        bgSceneManager.addObject(h);
        hearts.push(h);
    }
    for (let i = 0; i < rightHeartCount; i++) {
        const h = new ProceduralBorderHeart(false, true, false, i);
        bgSceneManager.addObject(h);
        hearts.push(h);
    }

    // 3. Falling Petals
    for (let i = 0; i < petalCount; i++) {
        const p = new ProceduralPetal();
        bgSceneManager.addObject(p);
        petals.push(p);
    }

    repositionBorders();
}

function initLuxuryBackground() {
    const canvas = document.getElementById('threejs-bg-canvas');
    if (!canvas) return;

    const hideLoader = () => {
        const loader = document.getElementById('loader');
        if (loader && loader.style.visibility !== 'hidden') {
            loader.style.opacity = '0';
            setTimeout(() => {
                loader.style.visibility = 'hidden';
                loader.style.display = 'none';
            }, 500);
        }
    };

    try {
        if (typeof THREE === 'undefined') {
            console.warn("Three.js not loaded. Gracefully bypassing 3D background.");
            hideLoader();
            return;
        }

        bgSceneManager = new ThreeSceneManager('threejs-bg-canvas');
        if (!bgSceneManager.scene) {
            hideLoader();
            return;
        }

        lastIsMobileState = bgSceneManager.isMobile;

        rebuildEntities();

        window.addEventListener('resize', () => {
            if (bgSceneManager) {
                if (bgSceneManager.isMobile !== lastIsMobileState) {
                    lastIsMobileState = bgSceneManager.isMobile;
                    rebuildEntities();
                } else {
                    repositionBorders();
                }
            }
        });

        let targetMouseX = 0, targetMouseY = 0;

        window.addEventListener('mousemove', (e) => {
            targetMouseX = (e.clientX - window.innerWidth / 2) * 0.0003;
            targetMouseY = (e.clientY - window.innerHeight / 2) * 0.0003;
        });

        function mainLoop(time) {
            if (bgSceneManager) {
                if (!bgSceneManager.prefersReducedMotion && bgSceneManager.camera) {
                    // Petals react gently to cursor wind
                    const windX = targetMouseX * 0.1;
                    const windZ = -targetMouseY * 0.1;
                    petals.forEach(p => {
                        p.mouseInfluence.x = windX;
                        p.mouseInfluence.y = windZ;
                    });
                }
                bgSceneManager.tick(time);
            }
            requestAnimationFrame(mainLoop);
        }

        requestAnimationFrame(mainLoop);
        setTimeout(hideLoader, 300);

    } catch (err) {
        console.error("WebGL Background setup error:", err);
        hideLoader();
    }
}

document.addEventListener('DOMContentLoaded', () => {
    initLuxuryBackground();
});
