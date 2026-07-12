/**
 * three-background.js
 * Procedural asset generation logic for luxury romantic elements.
 */

// Global cache helpers to optimize GPU performance
let sharedParticleTexture = null;
function getSharedParticleTexture() {
    if (!sharedParticleTexture) {
        const canvas = document.createElement('canvas');
        canvas.width = 64;
        canvas.height = 64;
        const ctx = canvas.getContext('2d');
        
        const grad = ctx.createRadialGradient(32, 32, 0, 32, 32, 32);
        grad.addColorStop(0, 'rgba(255, 255, 255, 1)');
        grad.addColorStop(0.3, 'rgba(255, 255, 255, 0.8)');
        grad.addColorStop(1, 'rgba(255, 255, 255, 0)');
        
        ctx.fillStyle = grad;
        ctx.fillRect(0, 0, 64, 64);
        sharedParticleTexture = new THREE.CanvasTexture(canvas);
    }
    return sharedParticleTexture;
}

let sharedPetalGeometry = null;
function getSharedPetalGeometry() {
    if (!sharedPetalGeometry) {
        // Curve a standard PlaneGeometry to represent a beautiful, curved rose petal
        const geom = new THREE.PlaneGeometry(0.3, 0.4, 8, 8);
        const pos = geom.attributes.position;
        for (let i = 0; i < pos.count; i++) {
            const x = pos.getX(i);
            const y = pos.getY(i);
            
            // Bend along Y (cup shape)
            const bendY = Math.sin((y + 0.2) * Math.PI / 0.4) * 0.055;
            
            // Taper the bottom (make it petal shaped)
            const normY = (y + 0.2) / 0.4; // 0 to 1
            const scaleX = Math.sin(normY * Math.PI); 
            pos.setX(i, x * (0.35 + 0.65 * scaleX));
            
            // Bend along X
            const bendX = (1.0 - Math.pow(x / 0.15, 2)) * 0.025;
            
            pos.setZ(i, bendY + bendX);
        }
        geom.computeVertexNormals();
        sharedPetalGeometry = geom;
    }
    return sharedPetalGeometry;
}

let sharedPetalMaterials = null;
function getSharedPetalMaterials() {
    if (!sharedPetalMaterials) {
        // Colors: dark red shades matching the luxury Candlelight Dinner atmosphere
        const colors = [0x7A0910, 0x5C0207, 0x9C121B];
        sharedPetalMaterials = colors.map(color => new THREE.MeshStandardMaterial({
            color: color,
            roughness: 0.45,
            metalness: 0.05,
            side: THREE.DoubleSide
        }));
    }
    return sharedPetalMaterials;
}

// 1. Slowly Falling Realistic Dark Red Rose Petal
class ProceduralPetal {
    constructor() {
        const geom = getSharedPetalGeometry();
        const mats = getSharedPetalMaterials();
        const randomMat = mats[Math.floor(Math.random() * mats.length)];

        this.mesh = new THREE.Mesh(geom, randomMat);
        
        // Random scale (0.75 to 1.5)
        const s = 0.75 + Math.random() * 0.75;
        this.mesh.scale.set(s, s, s);
        
        this.reset();
    }

    reset() {
        // Distribute nicely along screen width, starting above the top border
        this.mesh.position.set(
            (Math.random() - 0.5) * 16,
            Math.random() * 10 + 6,
            (Math.random() - 0.5) * 4 - 1
        );
        this.mesh.rotation.set(
            Math.random() * Math.PI,
            Math.random() * Math.PI,
            Math.random() * Math.PI
        );

        this.velocity = {
            y: 0.008 + Math.random() * 0.01, // slow natural fall
            x: (Math.random() - 0.5) * 0.003, // slow drift
            z: (Math.random() - 0.5) * 0.002
        };

        this.rotSpeed = {
            x: 0.004 + Math.random() * 0.008,
            y: 0.007 + Math.random() * 0.008,
            z: 0.002 + Math.random() * 0.005
        };
        this.swayWidth = 0.4 + Math.random() * 0.6;
        this.timeOffset = Math.random() * 100;
        this.mouseInfluence = { x: 0, y: 0 };
    }

    tick(elapsed, time) {
        // Natural wind sway
        const sway = Math.sin(elapsed * 1.4 + this.timeOffset) * this.swayWidth * 0.006;
        
        this.mesh.position.y -= this.velocity.y;
        this.mesh.position.x += this.velocity.x + sway + this.mouseInfluence.x;
        this.mesh.position.z += this.velocity.z + this.mouseInfluence.y;

        this.mesh.rotation.x += this.rotSpeed.x;
        this.mesh.rotation.y += this.rotSpeed.y;
        this.mesh.rotation.z += this.rotSpeed.z;

        // Slow wind dampening for mouse interaction
        this.mouseInfluence.x *= 0.95;
        this.mouseInfluence.y *= 0.95;

        // Recycle when out of bottom frame
        if (this.mesh.position.y < -7) {
            // Recycle immediately to the top to keep petal count steady
            this.mesh.position.y = 8;
            this.mesh.position.x = (Math.random() - 0.5) * 16;
            this.mesh.position.z = (Math.random() - 0.5) * 4 - 1;
        }
    }
}

// 2. Procedural Border Candle
class ProceduralCandle {
    constructor(isLeft, isRight, isBottom, index) {
        this.isLeft = isLeft;
        this.isRight = isRight;
        this.isBottom = isBottom;
        this.index = index;

        this.mesh = new THREE.Group();
        this.build();
    }

    build() {
        // Candle body (ivory cylinder with slightly random heights)
        const height = 0.35 + Math.random() * 0.3;
        const radius = 0.07;
        const bodyGeom = new THREE.CylinderGeometry(radius, radius, height, 12);
        const bodyMat = new THREE.MeshStandardMaterial({
            color: 0xFAF9F6, // Warm Ivory
            roughness: 0.7,
            metalness: 0.05
        });
        const body = new THREE.Mesh(bodyGeom, bodyMat);
        body.position.y = height / 2;
        this.mesh.add(body);

        // Candle Wick
        const wickGeom = new THREE.CylinderGeometry(0.01, 0.01, 0.06, 6);
        const wickMat = new THREE.MeshBasicMaterial({ color: 0x222222 });
        const wick = new THREE.Mesh(wickGeom, wickMat);
        wick.position.y = height + 0.03;
        this.mesh.add(wick);

        // 3D Flame Cone
        const flameGeom = new THREE.ConeGeometry(0.04, 0.12, 8);
        this.flameMat = new THREE.MeshBasicMaterial({
            color: 0xFFD166, // Warm Gold flame
            transparent: true,
            opacity: 0.95,
            blending: THREE.AdditiveBlending
        });
        this.flame = new THREE.Mesh(flameGeom, this.flameMat);
        this.flame.position.y = height + 0.11;
        this.mesh.add(this.flame);

        // Flame Glowing Sprite (Soft Halo effect)
        const glowMat = new THREE.SpriteMaterial({
            map: getSharedParticleTexture(),
            color: 0xFF9E4A, // Amber glow
            transparent: true,
            opacity: 0.28,
            blending: THREE.AdditiveBlending
        });
        this.glow = new THREE.Sprite(glowMat);
        this.glow.position.copy(this.flame.position);
        this.glow.scale.set(0.6, 0.6, 1);
        this.mesh.add(this.glow);

        // Local animation state
        this.height = height;
        this.flickerSpeed = 6 + Math.random() * 6;
        this.flickerOffset = Math.random() * 50;
    }

    tick(elapsed, time) {
        // Multi-frequency flickering flame animation
        const flicker = Math.sin(elapsed * this.flickerSpeed) * 0.05 + 
                        Math.cos(elapsed * this.flickerSpeed * 2.1) * 0.02;

        this.flame.scale.set(1 + flicker, 1 + flicker * 1.2, 1 + flicker);
        // Completely removed x and z positional shifting for static candles
        
        // Match glow scale and opacity to flickering
        this.glow.scale.set(0.6 + flicker * 0.1, 0.6 + flicker * 0.1, 1);
        this.glow.material.opacity = 0.24 + flicker * 0.08;
    }
}

// 3. Glowing Love Symbol (Pink Neon Border Heart Outline)
class ProceduralBorderHeart {
    constructor(isLeft, isRight, isTop, index) {
        this.isLeft = isLeft;
        this.isRight = isRight;
        this.isTop = isTop;
        this.index = index;

        this.mesh = new THREE.Group();
        this.build();
    }

    build() {
        // Generate heart path
        const points = [];
        for (let t = 0; t <= Math.PI * 2; t += 0.12) {
            // Parametric heart equations
            const x = 16 * Math.pow(Math.sin(t), 3);
            const y = 13 * Math.cos(t) - 5 * Math.cos(2*t) - 2 * Math.cos(3*t) - Math.cos(4*t);
            // Scale and rotate
            points.push(new THREE.Vector3(x * 0.008, y * 0.008, 0));
        }
        points.push(points[0].clone()); // Close path
        
        const curve = new THREE.CatmullRomCurve3(points);
        // Create 3D Tube geometry around path to make outline heart
        const geom = new THREE.TubeGeometry(curve, 32, 0.018, 6, true);
        
        // Emissive-like hot pink material
        const mat = new THREE.MeshBasicMaterial({
            color: 0xFF5D8F, // Soft Pink neon outline
            transparent: true,
            opacity: 0.85,
            blending: THREE.AdditiveBlending
        });
        
        const tube = new THREE.Mesh(geom, mat);
        this.mesh.add(tube);

        // Add secondary larger halo sprite behind the heart to simulate light bleed in fog
        const haloMat = new THREE.SpriteMaterial({
            map: getSharedParticleTexture(),
            color: 0xFF007F, // Neon Pink
            transparent: true,
            opacity: 0.14,
            blending: THREE.AdditiveBlending
        });
        const halo = new THREE.Sprite(haloMat);
        halo.scale.set(0.7, 0.7, 1);
        this.mesh.add(halo);

        // Initial sizing and speeds
        this.baseScale = 0.8 + Math.random() * 0.4;
        this.mesh.scale.setScalar(this.baseScale);
        
        this.pulseSpeed = 1.2 + Math.random() * 0.8;
        this.pulseOffset = Math.random() * 10;
    }

    tick(elapsed, time) {
        // Hearts are now completely static as requested.
        // Removed pulse animation.
    }
}

