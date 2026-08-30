"use client";
/**
 * One scene, two targets: every node lerps between pos_graph and the mercator
 * projection of pos_geo. Nodes without geography keep their hierarchy position
 * in map mode, so the double arrow stays connected.
 *
 * Nodes render as ONE InstancedMesh — one draw call, the same technique that
 * will carry the 2,500+ municipios later.
 */
import { useLayoutEffect, useMemo, useRef } from "react";
import * as THREE from "three";
import { useFrame } from "@react-three/fiber";
import { MapControls } from "@react-three/drei";
import { EDGE_COLORS, LEVEL_COLORS, edges, nodeRadius, nodes, projectGeo } from "../lib/data";
import type { EdgeRow } from "../lib/data";
import { useVizStore } from "../lib/store";

const N = nodes.length;
const nodeIndex = new Map(nodes.map((n, i) => [n.id, i]));
const autoridadEdges = edges.filter((e) => e.type === "autoridad");
const legitimidadEdges = edges.filter((e) => e.type === "legitimidad");
const EDGE_OFFSET = 0.4; // shifts each direction sideways so a↔b pairs read as a double arrow
const LERP_LAMBDA = 6; // speed of the grafo↔mapa transition

// Each edge is drawn slightly offset to its own left; opposite directions of
// the same pair land on opposite sides and render as two parallel lines.
function writeSegments(list: EdgeRow[], out: Float32Array, pos: Float32Array): void {
  for (let i = 0; i < list.length; i++) {
    const a = nodeIndex.get(list[i].from)! * 2;
    const b = nodeIndex.get(list[i].to)! * 2;
    const dx = pos[b] - pos[a];
    const dy = pos[b + 1] - pos[a + 1];
    const len = Math.hypot(dx, dy) || 1;
    const ox = (-dy / len) * EDGE_OFFSET;
    const oy = (dx / len) * EDGE_OFFSET;
    const o = i * 6;
    out[o] = pos[a] + ox;
    out[o + 1] = pos[a + 1] + oy;
    out[o + 2] = 0;
    out[o + 3] = pos[b] + ox;
    out[o + 4] = pos[b + 1] + oy;
    out[o + 5] = 0;
  }
}

export default function Scene() {
  const mode = useVizStore((s) => s.mode);
  const meshRef = useRef<THREE.InstancedMesh>(null);
  const autoAttr = useRef<THREE.BufferAttribute>(null);
  const legiAttr = useRef<THREE.BufferAttribute>(null);
  const dummy = useMemo(() => new THREE.Object3D(), []);
  const current = useMemo(
    () => Float32Array.from(nodes.flatMap((n) => [n.pos_graph.x, n.pos_graph.y])),
    [],
  );
  const autoArray = useMemo(() => new Float32Array(autoridadEdges.length * 6), []);
  const legiArray = useMemo(() => new Float32Array(legitimidadEdges.length * 6), []);

  useLayoutEffect(() => {
    const mesh = meshRef.current!;
    const color = new THREE.Color();
    nodes.forEach((n, i) => mesh.setColorAt(i, color.set(LEVEL_COLORS[n.level])));
    mesh.instanceColor!.needsUpdate = true;
  }, []);

  useFrame((_, dt) => {
    const mesh = meshRef.current;
    if (!mesh) return;
    for (let i = 0; i < N; i++) {
      const n = nodes[i];
      let tx = n.pos_graph.x;
      let ty = n.pos_graph.y;
      if (mode === "mapa" && n.pos_geo) {
        [tx, ty] = projectGeo(n.pos_geo.lon, n.pos_geo.lat);
      }
      current[i * 2] = THREE.MathUtils.damp(current[i * 2], tx, LERP_LAMBDA, dt);
      current[i * 2 + 1] = THREE.MathUtils.damp(current[i * 2 + 1], ty, LERP_LAMBDA, dt);
      dummy.position.set(current[i * 2], current[i * 2 + 1], 0);
      dummy.scale.setScalar(nodeRadius(n));
      dummy.updateMatrix();
      mesh.setMatrixAt(i, dummy.matrix);
    }
    mesh.instanceMatrix.needsUpdate = true;
    writeSegments(autoridadEdges, autoArray, current);
    writeSegments(legitimidadEdges, legiArray, current);
    if (autoAttr.current) autoAttr.current.needsUpdate = true;
    if (legiAttr.current) legiAttr.current.needsUpdate = true;
  });

  return (
    <>
      <MapControls enableRotate={false} screenSpacePanning minZoom={2} maxZoom={100} />
      <instancedMesh ref={meshRef} args={[undefined, undefined, N]} frustumCulled={false}>
        <circleGeometry args={[1, 24]} />
        <meshBasicMaterial />
      </instancedMesh>
      <lineSegments frustumCulled={false} renderOrder={-1}>
        <bufferGeometry>
          <bufferAttribute
            ref={autoAttr}
            attach="attributes-position"
            args={[autoArray, 3]}
            usage={THREE.DynamicDrawUsage}
          />
        </bufferGeometry>
        <lineBasicMaterial color={EDGE_COLORS.autoridad} transparent opacity={0.45} />
      </lineSegments>
      <lineSegments frustumCulled={false} renderOrder={-1}>
        <bufferGeometry>
          <bufferAttribute
            ref={legiAttr}
            attach="attributes-position"
            args={[legiArray, 3]}
            usage={THREE.DynamicDrawUsage}
          />
        </bufferGeometry>
        <lineBasicMaterial color={EDGE_COLORS.legitimidad} transparent opacity={0.45} />
      </lineSegments>
    </>
  );
}
