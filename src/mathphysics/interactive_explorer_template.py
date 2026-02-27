HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Exceptional Algebra Explorer</title>
    <script src="https://unpkg.com/vue@3/dist/vue.global.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/three@0.128.0/examples/js/controls/OrbitControls.js"></script>
    <script src="https://cdn.tailwindcss.com"></script>
    <style>
        body { margin: 0; background-color: #050505; color: #e0e0e0; font-family: 'Inter', sans-serif; overflow: hidden; }
        canvas { display: block; }
        .ui-overlay { position: absolute; top: 0; left: 0; width: 100%; height: 100%; pointer-events: none; }
        .ui-panel { pointer-events: auto; background: rgba(10, 10, 10, 0.85); backdrop-filter: blur(10px); border: 1px solid #333; padding: 1.5rem; border-radius: 0.75rem; }
        .neon-glow { text-shadow: 0 0 10px rgba(0, 255, 255, 0.7); }
        .neon-border { border-color: #00ffff; box-shadow: 0 0 10px rgba(0, 255, 255, 0.3); }
        .btn-active { background: #00ffff; color: #000; }
        .scrollbar-hide::-webkit-scrollbar { display: none; }
    </style>
</head>
<body>
    <div id="app" class="relative w-full h-screen">
        <div ref="canvasContainer" class="w-full h-full"></div>

        <div class="ui-overlay flex flex-col justify-between p-6">
            <!-- Header -->
            <div class="flex justify-between items-start">
                <div class="ui-panel neon-border">
                    <h1 class="text-2xl font-bold neon-glow">Exceptional Algebra Explorer</h1>
                    <p class="text-sm opacity-70">Unified Mapping: Lie ↔ Clifford ↔ Cayley-Dickson</p>
                </div>

                <div class="ui-panel space-y-4 max-w-xs">
                    <div class="text-sm font-semibold uppercase tracking-wider opacity-50">Algebra System</div>
                    <div class="grid grid-cols-3 gap-2">
                        <button v-for="sys in systems" :key="sys.name"
                                @click="selectSystem(sys)"
                                :class="['px-2 py-1 text-xs border border-gray-600 rounded transition-all', currentSystem.name === sys.name ? 'btn-active neon-border' : 'hover:border-cyan-400']">
                            {{ sys.name }}
                        </button>
                    </div>
                </div>
            </div>

            <!-- Bottom Info & Controls -->
            <div class="flex justify-between items-end">
                <div class="ui-panel w-96 space-y-4">
                    <div class="flex justify-between items-center">
                        <h2 class="text-lg font-bold text-cyan-400">{{ currentSystem.name }} Properties</h2>
                        <span class="text-xs px-2 py-1 bg-cyan-900 rounded">Rank: {{ currentSystem.rank }}</span>
                    </div>
                    <div class="text-sm space-y-2">
                        <div class="flex justify-between"><span class="opacity-60">Dimension:</span> <span>{{ currentSystem.dim }}</span></div>
                        <div class="flex justify-between"><span class="opacity-60">Roots:</span> <span>{{ currentSystem.roots.length }}</span></div>
                        <div class="flex justify-between"><span class="opacity-60">Cartan Det:</span> <span>{{ currentSystem.det }}</span></div>
                    </div>
                    <div class="pt-2 border-t border-gray-800">
                        <div class="text-xs font-semibold mb-2 opacity-50">Mapping Layers</div>
                        <div class="flex space-x-2">
                            <label class="flex items-center space-x-2 cursor-pointer">
                                <input type="checkbox" v-model="layers.roots" class="form-checkbox text-cyan-500">
                                <span class="text-xs">Roots</span>
                            </label>
                            <label class="flex items-center space-x-2 cursor-pointer">
                                <input type="checkbox" v-model="layers.connections" class="form-checkbox text-cyan-500">
                                <span class="text-xs">Weights</span>
                            </label>
                            <label class="flex items-center space-x-2 cursor-pointer">
                                <input type="checkbox" v-model="layers.clifford" class="form-checkbox text-cyan-500">
                                <span class="text-xs">Clifford</span>
                            </label>
                        </div>
                    </div>
                </div>

                <div class="ui-panel text-right space-y-2">
                    <div class="text-xs opacity-50 uppercase tracking-widest">Navigation</div>
                    <div class="text-sm">LMB: Rotate | RMB: Pan | Wheel: Zoom</div>
                    <button @click="resetCamera" class="mt-2 text-xs px-3 py-1 border border-gray-700 rounded hover:border-cyan-400">Reset View</button>
                </div>
            </div>
        </div>

        <!-- Detail Tooltip -->
        <div v-if="hoveredNode"
             :style="{ top: tooltipPos.y + 'px', left: tooltipPos.x + 'px' }"
             class="fixed pointer-events-none ui-panel py-2 px-3 text-xs neon-border transform -translate-x-1/2 -translate-y-full mb-4">
            <div class="font-bold text-cyan-400 mb-1">Root \u03b1_{{ hoveredNode.index + 1 }}</div>
            <div class="text-pink-400 mb-1">{{ hoveredNode.type }}</div>
            <div class="opacity-80">Coords: [{{ hoveredNode.coords.map(c => c.toFixed(2)).join(', ') }}]</div>
            <div class="mt-1 pt-1 border-t border-gray-800">
                <span class="text-pink-400">Clifford:</span> 0x{{ hoveredNode.bitPattern.toString(16) }}
            </div>
        </div>
    </div>

    <script>
        const { createApp, ref, onMounted, watch, reactive } = Vue;

        const ROOT_DATA = {data_placeholder};

        createApp({
            setup() {
                const canvasContainer = ref(null);
                const systems = ref(ROOT_DATA);
                const currentSystem = ref(ROOT_DATA[0]);
                const hoveredNode = ref(null);
                const tooltipPos = reactive({ x: 0, y: 0 });
                const layers = reactive({
                    roots: true,
                    connections: true,
                    clifford: false
                });

                let scene, camera, renderer, controls, pointCloud, lineSegments;
                let points = [];

                const initThree = () => {
                    scene = new THREE.Scene();
                    camera = new THREE.PerspectiveCamera(75, window.innerWidth / window.innerHeight, 0.1, 1000);
                    camera.position.z = 10;

                    renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
                    renderer.setSize(window.innerWidth, window.innerHeight);
                    renderer.setPixelRatio(window.devicePixelRatio);
                    canvasContainer.value.appendChild(renderer.domElement);

                    controls = new THREE.OrbitControls(camera, renderer.domElement);
                    controls.enableDamping = true;
                    controls.dampingFactor = 0.05;

                    const ambientLight = new THREE.AmbientLight(0xffffff, 0.5);
                    scene.add(ambientLight);
                    const pointLight = new THREE.PointLight(0x00ffff, 1);
                    pointLight.position.set(10, 10, 10);
                    scene.add(pointLight);

                    updateVisualization();
                    animate();
                };

                const updateVisualization = () => {
                    // Cleanup
                    if (pointCloud) scene.remove(pointCloud);
                    if (lineSegments) scene.remove(lineSegments);

                    const sys = currentSystem.value;
                    const geometry = new THREE.BufferGeometry();
                    const positions = [];
                    const colors = [];
                    const sizes = [];

                    sys.roots3d.forEach((root, i) => {
                        positions.push(root[0], root[1], root[2]);

                        // Color based on norm or index
                        const color = new THREE.Color();
                        if (layers.clifford) {
                            // Highlight by type
                            if (sys.types && sys.types[i].includes("Type 1")) {
                                color.setHex(0x00ffff); // Cyan for Type 1
                            } else {
                                color.setHex(0xff00ff); // Magenta for Type 2
                            }
                        } else {
                            color.setHSL(0.55, 0.8, 0.5 + 0.3 * (i / sys.roots.length));
                        }
                        colors.push(color.r, color.g, color.b);
                        sizes.push(layers.roots ? 0.15 : 0);
                    });

                    geometry.setAttribute('position', new THREE.Float32BufferAttribute(positions, 3));
                    geometry.setAttribute('color', new THREE.Float32BufferAttribute(colors, 3));

                    const material = new THREE.PointsMaterial({
                        size: 0.15,
                        vertexColors: true,
                        transparent: true,
                        opacity: 0.8,
                        map: createCircleTexture()
                    });

                    pointCloud = new THREE.Points(geometry, material);
                    scene.add(pointCloud);

                    if (layers.connections) {
                        const lineGeometry = new THREE.BufferGeometry();
                        const linePositions = [];
                        const lineColors = [];

                        // Simple lattice connections (nearest neighbors)
                        for (let i = 0; i < sys.roots3d.length; i++) {
                            for (let j = i + 1; j < sys.roots3d.length; j++) {
                                const d2 = Math.pow(sys.roots3d[i][0]-sys.roots3d[j][0], 2) +
                                           Math.pow(sys.roots3d[i][1]-sys.roots3d[j][1], 2) +
                                           Math.pow(sys.roots3d[i][2]-sys.roots3d[j][2], 2);
                                if (d2 < 2.5) { // Threshold for neighbor
                                    linePositions.push(...sys.roots3d[i], ...sys.roots3d[j]);
                                    lineColors.push(0, 0.5, 0.5, 0, 0.5, 0.5);
                                }
                            }
                        }
                        lineGeometry.setAttribute('position', new THREE.Float32BufferAttribute(linePositions, 3));
                        lineGeometry.setAttribute('color', new THREE.Float32BufferAttribute(lineColors, 3));
                        lineSegments = new THREE.LineSegments(lineGeometry, new THREE.LineBasicMaterial({ vertexColors: true, transparent: true, opacity: 0.2 }));
                        scene.add(lineSegments);
                    }
                };

                const createCircleTexture = () => {
                    const canvas = document.createElement('canvas');
                    canvas.width = 64; canvas.height = 64;
                    const ctx = canvas.getContext('2d');
                    ctx.beginPath(); ctx.arc(32, 32, 30, 0, Math.PI * 2);
                    ctx.fillStyle = 'white'; ctx.fill();
                    const texture = new THREE.CanvasTexture(canvas);
                    return texture;
                };

                const animate = () => {
                    requestAnimationFrame(animate);
                    controls.update();

                    // Auto-rotation
                    if (pointCloud) pointCloud.rotation.y += 0.001;
                    if (lineSegments) lineSegments.rotation.y += 0.001;

                    renderer.render(scene, camera);
                };

                const selectSystem = (sys) => {
                    currentSystem.value = sys;
                    updateVisualization();
                };

                const resetCamera = () => {
                    controls.reset();
                };

                const onMouseMove = (event) => {
                    tooltipPos.x = event.clientX;
                    tooltipPos.y = event.clientY;

                    if (!pointCloud) return;

                    const raycaster = new THREE.Raycaster();
                    const mouse = new THREE.Vector2();
                    mouse.x = (event.clientX / window.innerWidth) * 2 - 1;
                    mouse.y = -(event.clientY / window.innerHeight) * 2 + 1;

                    raycaster.setFromCamera(mouse, camera);
                    raycaster.params.Points.threshold = 0.1;
                    const intersects = raycaster.intersectObject(pointCloud);

                    if (intersects.length > 0) {
                        const idx = intersects[0].index;
                        hoveredNode.value = {
                            index: idx,
                            coords: currentSystem.value.roots[idx],
                            type: currentSystem.value.types ? currentSystem.value.types[idx] : "Unknown",
                            bitPattern: currentSystem.value.bitPatterns ? currentSystem.value.bitPatterns[idx] : 0
                        };
                    } else {
                        hoveredNode.value = null;
                    }
                };

                onMounted(() => {
                    initThree();
                    window.addEventListener('mousemove', onMouseMove);
                    window.addEventListener('resize', () => {
                        camera.aspect = window.innerWidth / window.innerHeight;
                        camera.updateProjectionMatrix();
                        renderer.setSize(window.innerWidth, window.innerHeight);
                    });
                });

                watch([() => layers.roots, () => layers.connections, () => layers.clifford], updateVisualization);

                return {
                    canvasContainer, systems, currentSystem, hoveredNode, tooltipPos, layers, selectSystem, resetCamera
                };
            }
        }).mount('#app');
    </script>
</body>
</html>
"""
