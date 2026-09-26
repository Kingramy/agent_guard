"use client";

import { useEffect, useRef } from "react";
import * as THREE from "three";

export function EpistemicDefenseCanvas() {
  const mountRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const container = mountRef.current;
    if (!container) return;

    const width = container.clientWidth || 600;
    const height = container.clientHeight || 400;

    // Scene, Camera, Renderer
    const scene = new THREE.Scene();
    const camera = new THREE.PerspectiveCamera(45, width / height, 0.1, 1000);
    camera.position.z = 24;

    const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
    renderer.setSize(width, height);
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    renderer.setClearColor(0x000000, 0);
    container.appendChild(renderer.domElement);

    // Group for all rotating elements
    const rootGroup = new THREE.Group();
    scene.add(rootGroup);

    // 1. Central Geodesic Security Boundary Sphere (Wireframe)
    const sphereGeometry = new THREE.IcosahedronGeometry(7, 2);
    const sphereMaterial = new THREE.MeshBasicMaterial({
      color: 0x06b6d4,
      wireframe: true,
      transparent: true,
      opacity: 0.18,
    });
    const defenseSphere = new THREE.Mesh(sphereGeometry, sphereMaterial);
    rootGroup.add(defenseSphere);

    // Outer faint perimeter
    const outerSphereGeo = new THREE.IcosahedronGeometry(10, 1);
    const outerSphereMat = new THREE.MeshBasicMaterial({
      color: 0x3b82f6,
      wireframe: true,
      transparent: true,
      opacity: 0.08,
    });
    const outerSphere = new THREE.Mesh(outerSphereGeo, outerSphereMat);
    rootGroup.add(outerSphere);

    // 2. Trajectory Nodes (Emerald passes vs Crimson threat intercepts)
    const nodeCount = 38;
    const nodeData: {
      mesh: THREE.Mesh;
      isThreat: boolean;
      speed: number;
      orbitRadius: number;
      orbitAngle: number;
      orbitInclination: number;
      initialScale: number;
    }[] = [];

    const emeraldMat = new THREE.MeshBasicMaterial({ color: 0x10b981 });
    const crimsonMat = new THREE.MeshBasicMaterial({ color: 0xef4444 });
    const sphereNodeGeo = new THREE.SphereGeometry(0.35, 12, 12);
    const threatNodeGeo = new THREE.SphereGeometry(0.55, 16, 16);

    for (let i = 0; i < nodeCount; i++) {
      const isThreat = i < 5; // 5 critical threat nodes (NLI contradiction, canary, loop)
      const mesh = new THREE.Mesh(isThreat ? threatNodeGeo : sphereNodeGeo, isThreat ? crimsonMat : emeraldMat);

      const orbitRadius = isThreat ? 6 + Math.random() * 2 : 4 + Math.random() * 6;
      const orbitAngle = Math.random() * Math.PI * 2;
      const orbitInclination = (Math.random() - 0.5) * Math.PI * 0.8;

      mesh.position.x = Math.cos(orbitAngle) * orbitRadius * Math.cos(orbitInclination);
      mesh.position.y = Math.sin(orbitInclination) * orbitRadius;
      mesh.position.z = Math.sin(orbitAngle) * orbitRadius * Math.cos(orbitInclination);

      rootGroup.add(mesh);
      nodeData.push({
        mesh,
        isThreat,
        speed: (0.004 + Math.random() * 0.008) * (Math.random() > 0.5 ? 1 : -1),
        orbitRadius,
        orbitAngle,
        orbitInclination,
        initialScale: 1,
      });
    }

    // 3. Shockwave Rings for Crimson Threat Nodes
    const ringGeo = new THREE.RingGeometry(0.7, 0.9, 24);
    const ringMat = new THREE.MeshBasicMaterial({
      color: 0xef4444,
      side: THREE.DoubleSide,
      transparent: true,
      opacity: 0.7,
    });
    const rings: { mesh: THREE.Mesh; parentMesh: THREE.Mesh; scale: number }[] = [];

    nodeData
      .filter((n) => n.isThreat)
      .forEach((threat) => {
        const ring = new THREE.Mesh(ringGeo, ringMat.clone());
        ring.position.copy(threat.mesh.position);
        rootGroup.add(ring);
        rings.push({ mesh: ring, parentMesh: threat.mesh, scale: 1 });
      });

    // 4. Connecting Defense Vectors (Lines between nearby nodes)
    const lineMaterial = new THREE.LineBasicMaterial({
      color: 0x06b6d4,
      transparent: true,
      opacity: 0.15,
    });
    const lineGeometry = new THREE.BufferGeometry();
    const linePositions = new Float32Array(nodeCount * nodeCount * 6);
    lineGeometry.setAttribute("position", new THREE.BufferAttribute(linePositions, 3));
    const vectorLines = new THREE.LineSegments(lineGeometry, lineMaterial);
    rootGroup.add(vectorLines);

    // Mouse Interaction with Inertia Damping
    let mouseX = 0;
    let mouseY = 0;
    let targetRotationX = 0;
    let targetRotationY = 0;

    const handleMouseMove = (e: MouseEvent) => {
      const rect = container.getBoundingClientRect();
      const x = (e.clientX - rect.left) / rect.width - 0.5;
      const y = (e.clientY - rect.top) / height - 0.5;
      targetRotationY = x * 1.5;
      targetRotationX = y * 1.5;
    };

    container.addEventListener("mousemove", handleMouseMove);

    // Resize Handler
    const handleResize = () => {
      if (!container) return;
      const newWidth = container.clientWidth;
      const newHeight = container.clientHeight;
      camera.aspect = newWidth / newHeight;
      camera.updateProjectionMatrix();
      renderer.setSize(newWidth, newHeight);
    };

    window.addEventListener("resize", handleResize);

    // Animation Loop
    let animationFrameId: number;
    let clock = new THREE.Clock();

    const animate = () => {
      animationFrameId = requestAnimationFrame(animate);
      const elapsed = clock.getElapsedTime();

      // Smooth inertia rotation
      rootGroup.rotation.y += (targetRotationY - rootGroup.rotation.y) * 0.05 + 0.003;
      rootGroup.rotation.x += (targetRotationX - rootGroup.rotation.x) * 0.05;

      // Pulse defense sphere
      const sphereScale = 1 + Math.sin(elapsed * 1.5) * 0.02;
      defenseSphere.scale.set(sphereScale, sphereScale, sphereScale);
      outerSphere.rotation.y -= 0.001;

      // Update node orbits
      nodeData.forEach((node) => {
        node.orbitAngle += node.speed;
        node.mesh.position.x = Math.cos(node.orbitAngle) * node.orbitRadius * Math.cos(node.orbitInclination);
        node.mesh.position.z = Math.sin(node.orbitAngle) * node.orbitRadius * Math.cos(node.orbitInclination);

        if (node.isThreat) {
          const pulse = 1 + Math.sin(elapsed * 5) * 0.25;
          node.mesh.scale.set(pulse, pulse, pulse);
        }
      });

      // Update threat shockwave rings
      rings.forEach((ring) => {
        ring.mesh.position.copy(ring.parentMesh.position);
        ring.mesh.lookAt(camera.position);
        ring.scale += 0.02;
        if (ring.scale > 2.8) {
          ring.scale = 1;
        }
        ring.mesh.scale.set(ring.scale, ring.scale, ring.scale);
        (ring.mesh.material as THREE.MeshBasicMaterial).opacity = Math.max(0, 1 - ring.scale / 2.8);
      });

      // Dynamic network connections
      const positions = lineGeometry.attributes.position.array as Float32Array;
      let lineIndex = 0;
      for (let i = 0; i < nodeCount; i++) {
        for (let j = i + 1; j < nodeCount; j++) {
          const dist = nodeData[i].mesh.position.distanceTo(nodeData[j].mesh.position);
          if (dist < 4.8) {
            positions[lineIndex++] = nodeData[i].mesh.position.x;
            positions[lineIndex++] = nodeData[i].mesh.position.y;
            positions[lineIndex++] = nodeData[i].mesh.position.z;
            positions[lineIndex++] = nodeData[j].mesh.position.x;
            positions[lineIndex++] = nodeData[j].mesh.position.y;
            positions[lineIndex++] = nodeData[j].mesh.position.z;
          }
        }
      }
      lineGeometry.setDrawRange(0, lineIndex / 3);
      lineGeometry.attributes.position.needsUpdate = true;

      renderer.render(scene, camera);
    };

    animate();

    return () => {
      cancelAnimationFrame(animationFrameId);
      window.removeEventListener("resize", handleResize);
      container.removeEventListener("mousemove", handleMouseMove);
      if (renderer.domElement && renderer.domElement.parentNode) {
        renderer.domElement.parentNode.removeChild(renderer.domElement);
      }
      renderer.dispose();
    };
  }, []);

  return (
    <div
      ref={mountRef}
      className="w-full h-full min-h-[380px] lg:min-h-[440px] relative pointer-events-auto cursor-grab active:cursor-grabbing"
      aria-label="Interactive 3D WebGL Neural Defense & Trajectory Constellation"
    >
      <div className="absolute top-3 left-4 z-10 pointer-events-none">
        <div className="flex items-center gap-2 px-2.5 py-1 rounded-full bg-slate-950/80 border border-slate-800 text-[10px] font-mono text-cyan-400 backdrop-blur-md">
          <span className="w-1.5 h-1.5 rounded-full bg-cyan-400 animate-ping" />
          <span>WebGL 3D Lattice: Real-Time Threat Intercept Constellation</span>
        </div>
      </div>
      <div className="absolute bottom-3 right-4 z-10 pointer-events-none text-[10px] font-mono text-slate-500 bg-slate-950/70 px-2 py-0.5 rounded border border-slate-800">
        Drag to Rotate • Orbit Invariant
      </div>
    </div>
  );
}
