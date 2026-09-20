'use client';

import React, { useEffect, useRef } from 'react';
import * as THREE from 'three';
import { BlochVector } from '@/lib/types';

interface Bloch3DCanvasProps {
  vector: BlochVector;
  colorHex: number;
  label: string;
}

export const Bloch3DCanvas: React.FC<Bloch3DCanvasProps> = ({ vector, colorHex, label }) => {
  const mountRef = useRef<HTMLDivElement>(null);
  const arrowRef = useRef<THREE.ArrowHelper | null>(null);

  useEffect(() => {
    const currentMount = mountRef.current;
    if (!currentMount) return;

    const width = 140;
    const height = 140;

    // Scene
    const scene = new THREE.Scene();

    // Camera
    const camera = new THREE.PerspectiveCamera(45, width / height, 0.1, 100);
    camera.position.set(2.5, 2.2, 3.2);
    camera.lookAt(0, 0, 0);

    // Renderer
    const renderer = new THREE.WebGLRenderer({ alpha: true, antialias: true });
    renderer.setSize(width, height);
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    currentMount.appendChild(renderer.domElement);

    // Wireframe Sphere (ブロッホ球体)
    const sphereGeo = new THREE.SphereGeometry(1, 16, 12);
    const sphereMat = new THREE.MeshBasicMaterial({
      color: 0x1e293b,
      wireframe: true,
      transparent: true,
      opacity: 0.35,
    });
    const sphereMesh = new THREE.Mesh(sphereGeo, sphereMat);
    scene.add(sphereMesh);

    // 赤道リング
    const ringGeo = new THREE.RingGeometry(0.99, 1.01, 32);
    const ringMat = new THREE.MeshBasicMaterial({
      color: 0x334155,
      side: THREE.DoubleSide,
      transparent: true,
      opacity: 0.6,
    });
    const ringMesh = new THREE.Mesh(ringGeo, ringMat);
    ringMesh.rotation.x = Math.PI / 2;
    scene.add(ringMesh);

    // 座標軸 (X=赤, Y=緑, Z=青/シアン)
    // Three.js座標系: X=右, Y=上(ブロッホのZ軸に対応), Z=手前(ブロッホのY軸に対応)
    const axesLength = 1.35;

    // Z軸 (|0⟩ and |1⟩) -> Three.js の Y軸
    const zAxisMat = new THREE.LineBasicMaterial({ color: 0x00f0ff, transparent: true, opacity: 0.7 });
    const zPoints = [new THREE.Vector3(0, -axesLength, 0), new THREE.Vector3(0, axesLength, 0)];
    const zAxisGeo = new THREE.BufferGeometry().setFromPoints(zPoints);
    scene.add(new THREE.Line(zAxisGeo, zAxisMat));

    // X軸 -> Three.js の X軸
    const xAxisMat = new THREE.LineBasicMaterial({ color: 0x64748b, transparent: true, opacity: 0.4 });
    const xPoints = [new THREE.Vector3(-axesLength, 0, 0), new THREE.Vector3(axesLength, 0, 0)];
    const xAxisGeo = new THREE.BufferGeometry().setFromPoints(xPoints);
    scene.add(new THREE.Line(xAxisGeo, xAxisMat));

    // Y軸 -> Three.js の Z軸
    const yAxisMat = new THREE.LineBasicMaterial({ color: 0x64748b, transparent: true, opacity: 0.4 });
    const yPoints = [new THREE.Vector3(0, 0, -axesLength), new THREE.Vector3(0, 0, axesLength)];
    const yAxisGeo = new THREE.BufferGeometry().setFromPoints(yPoints);
    scene.add(new THREE.Line(yAxisGeo, yAxisMat));

    // 状態ベクトル Arrow (初期向き)
    const dir = new THREE.Vector3(vector.x, vector.z, vector.y).normalize();
    const length = Math.min(1.0, Math.sqrt(vector.x ** 2 + vector.y ** 2 + vector.z ** 2));
    const arrow = new THREE.ArrowHelper(dir, new THREE.Vector3(0, 0, 0), length, colorHex, 0.25, 0.15);
    scene.add(arrow);
    arrowRef.current = arrow;

    // わずかな自転アニメーション
    let animId: number;
    const animate = () => {
      animId = requestAnimationFrame(animate);
      sphereMesh.rotation.y += 0.003;
      renderer.render(scene, camera);
    };
    animate();

    return () => {
      cancelAnimationFrame(animId);
      if (currentMount && renderer.domElement) {
        currentMount.removeChild(renderer.domElement);
      }
      renderer.dispose();
    };
  }, [colorHex]);

  // ベクトル更新時
  useEffect(() => {
    if (!arrowRef.current) return;
    // Three.js 空間: X=x, Y=z, Z=y
    const targetDir = new THREE.Vector3(vector.x, vector.z, vector.y);
    const len = Math.max(0.01, Math.min(1.0, targetDir.length()));
    arrowRef.current.setDirection(targetDir.normalize());
    arrowRef.current.setLength(len, 0.25, 0.15);
  }, [vector]);

  return (
    <div className="flex flex-col items-center">
      <div className="relative" ref={mountRef}>
        <div className="absolute top-1 left-2 text-[9px] text-cyan-400 font-bold">|0⟩ (+z)</div>
        <div className="absolute bottom-1 left-2 text-[9px] text-slate-400 font-bold">|1⟩ (-z)</div>
      </div>
      <span className="text-[11px] font-bold text-slate-300 mt-1">{label}</span>
      <div className="text-[10px] text-slate-400 font-mono flex gap-2">
        <span>x:{vector.x.toFixed(2)}</span>
        <span>y:{vector.y.toFixed(2)}</span>
        <span>z:{vector.z.toFixed(2)}</span>
      </div>
    </div>
  );
};
