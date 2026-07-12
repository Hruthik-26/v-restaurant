/**
 * three-scene.js
 * Core viewport manager for the Three.js 3D WebGL background scene.
 */
class ThreeSceneManager {
    constructor(canvasId) {
        this.canvas = document.getElementById(canvasId);
        if (!this.canvas) return;

        this.scene = null;
        this.camera = null;
        this.renderer = null;
        this.isMobile = window.innerWidth < 768;
        this.prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
        this.animationActive = true;
        
        this.lights = {
            ambient: null,
            gold: null,
            pink: null,
            candleLeft: null,
            candleRight: null
        };
        
        this.bgPlane = null;
        this.objects = [];
        this.init();
    }

    init() {
        // 1. Create Scene
        this.scene = new THREE.Scene();
        
        // 2. Setup Burgundy Fog for realistic atmospheric depth
        this.scene.fog = new THREE.FogExp2(0x180306, 0.05);

        // 3. Setup Camera
        this.camera = new THREE.PerspectiveCamera(60, window.innerWidth / window.innerHeight, 0.1, 100);
        this.camera.position.z = 8;

        // 4. Setup WebGL Renderer
        this.renderer = new THREE.WebGLRenderer({
            canvas: this.canvas,
            alpha: true,
            antialias: !this.isMobile,
            powerPreference: "high-performance"
        });
        this.renderer.setSize(window.innerWidth, window.innerHeight);
        this.renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));

        // Background gradient plane removed so CSS background image is visible.
        this.bgPlane = null;

        // 6. Rig Cinematic Lights
        // Warm Burgundy Ambient glow
        this.lights.ambient = new THREE.AmbientLight(0x2A0B12, 1.8);
        this.scene.add(this.lights.ambient);

        // Soft Warm Gold lighting from the front/side to illuminate the petals
        this.lights.gold = new THREE.DirectionalLight(0xFFD166, 1.6);
        this.lights.gold.position.set(5, 5, 4);
        this.scene.add(this.lights.gold);

        // Soft Pink backlight to highlight petal edges
        this.lights.pink = new THREE.DirectionalLight(0xFF5D8F, 1.0);
        this.lights.pink.position.set(-5, -3, 2);
        this.scene.add(this.lights.pink);

        // Border candlelight glows (warm flickering PointLights)
        this.lights.candleLeft = new THREE.PointLight(0xFFD166, 3.2, 18);
        this.scene.add(this.lights.candleLeft);

        this.lights.candleRight = new THREE.PointLight(0xFF9E4A, 3.2, 18);
        this.scene.add(this.lights.candleRight);

        // 7. Initialize positioning and sizes
        this.onResize();

        // 8. Register Listeners
        window.addEventListener('resize', this.onResize.bind(this));
        document.addEventListener('visibilitychange', this.onVisibilityChange.bind(this));
    }

    createBackgroundGradientTexture() {
        const canvas = document.createElement('canvas');
        canvas.width = 512;
        canvas.height = 512;
        const ctx = canvas.getContext('2d');
        
        // 1. Fill deep black/burgundy
        ctx.fillStyle = '#080103';
        ctx.fillRect(0, 0, 512, 512);
        
        // 2. Add linear gradient from bottom (burgundy) to top (pitch black)
        const vGrad = ctx.createLinearGradient(0, 512, 0, 0);
        vGrad.addColorStop(0, '#2A0B12');
        vGrad.addColorStop(0.5, '#120306');
        vGrad.addColorStop(1, '#050505');
        ctx.fillStyle = vGrad;
        ctx.fillRect(0, 0, 512, 512);
        
        // 3. Add soft warm gold radial glow at the bottom center representing candle lighting reflections
        const goldGlow = ctx.createRadialGradient(256, 512, 20, 256, 512, 380);
        goldGlow.addColorStop(0, 'rgba(255, 209, 102, 0.16)'); // Warm gold #FFD166
        goldGlow.addColorStop(1, 'rgba(0, 0, 0, 0)');
        ctx.fillStyle = goldGlow;
        ctx.fillRect(0, 0, 512, 512);

        // 4. Add soft pink radial glow at the top center
        const pinkGlow = ctx.createRadialGradient(256, 0, 10, 256, 0, 300);
        pinkGlow.addColorStop(0, 'rgba(255, 93, 143, 0.08)'); // Soft pink #FF5D8F
        pinkGlow.addColorStop(1, 'rgba(0, 0, 0, 0)');
        ctx.fillStyle = pinkGlow;
        ctx.fillRect(0, 0, 512, 512);
        
        const texture = new THREE.CanvasTexture(canvas);
        return texture;
    }

    getBoundsAt(z) {
        if (!this.camera) return { width: 10, height: 10, left: -5, right: 5, bottom: -5, top: 5 };
        const distance = this.camera.position.z - z;
        const fovRad = (this.camera.fov * Math.PI) / 180;
        const height = 2 * Math.tan(fovRad / 2) * distance;
        const width = height * this.camera.aspect;
        return {
            width,
            height,
            left: -width / 2,
            right: width / 2,
            bottom: -height / 2,
            top: height / 2
        };
    }

    addObject(obj) {
        if (obj) {
            this.scene.add(obj.mesh || obj);
            this.objects.push(obj);
        }
    }

    onResize() {
        if (!this.camera || !this.renderer) return;
        this.isMobile = window.innerWidth < 768;
        this.camera.aspect = window.innerWidth / window.innerHeight;
        this.camera.updateProjectionMatrix();
        this.renderer.setSize(window.innerWidth, window.innerHeight);

        // Scale background plane to cover the camera field of view at z = -10 with safety margin
        if (this.bgPlane) {
            const bounds = this.getBoundsAt(-10);
            this.bgPlane.scale.set(bounds.width * 1.5, bounds.height * 1.5, 1);
        }

        // Lock flickering PointLights to left and right borders at z = 3
        const borderBounds = this.getBoundsAt(3);
        if (this.lights.candleLeft) {
            this.lights.candleLeft.position.set(borderBounds.left + 0.5, 0, 3);
        }
        if (this.lights.candleRight) {
            this.lights.candleRight.position.set(borderBounds.right - 0.5, 0, 3);
        }
    }

    onVisibilityChange() {
        this.animationActive = !document.hidden;
    }

    tick(time) {
        if (!this.animationActive) return;

        const elapsed = time * 0.001;

        // Simulate candlelight flicker using high frequency sine/cosine offsets
        if (this.lights.candleLeft) {
            this.lights.candleLeft.intensity = 3.2 + Math.sin(elapsed * 5.2) * 0.6 + Math.cos(elapsed * 2.1) * 0.3;
        }
        if (this.lights.candleRight) {
            this.lights.candleRight.intensity = 3.2 + Math.cos(elapsed * 4.4) * 0.5 + Math.sin(elapsed * 1.8) * 0.2;
        }

        // Tick objects in scene
        this.objects.forEach(obj => {
            if (obj && typeof obj.tick === 'function') {
                obj.tick(elapsed, time);
            }
        });

        // Render Frame
        this.renderer.render(this.scene, this.camera);
    }

    dispose() {
        window.removeEventListener('resize', this.onResize);
        document.removeEventListener('visibilitychange', this.onVisibilityChange);
        
        // Remove all meshes from scene
        this.objects.forEach(obj => {
            const mesh = obj.mesh || obj;
            if (mesh.geometry) mesh.geometry.dispose();
            if (mesh.material) {
                if (Array.isArray(mesh.material)) {
                    mesh.material.forEach(mat => mat.dispose());
                } else {
                    mesh.material.dispose();
                }
            }
            this.scene.remove(mesh);
        });

        if (this.bgPlane) {
            this.bgPlane.geometry.dispose();
            this.bgPlane.material.dispose();
            this.scene.remove(this.bgPlane);
        }
        
        this.renderer.dispose();
    }
}
