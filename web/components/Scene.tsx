"use client";
/**
 * One scene, two targets: every node lerps between pos_graph and the mercator
 * projection of pos_geo. Nodes without geography keep their hierarchy position
 * in map mode, so the double arrow stays connected.
 *
 * Nodes render as ONE InstancedMesh — one draw call, the technique that will
 * carry the 2,500+ municipios when they arrive.
 */
import { useLayoutEffect, useMemo, useRef } from "react";
import * as THREE from "three";
import { useFrame, useThree } from "@react-three/fiber";
import { MapControls } from "@react-three/drei";
import { EDGE_COLORS, LEVEL_COLORS, geoOffset, nodeRadius, projectGeo } from "../lib/data";
import type { Dataset, EdgeRow } from "../lib/data";
import { useVizStore } from "../lib/store";

const EDGE_OFFSET = 0.4; // shifts each direction sideways so a↔b pairs read as a double arrow
const LERP_LAMBDA = 6; // speed of the grafo↔mapa transition
const EXTINCT_COLOR = new THREE.Color("#4b5563");

function writeSegments(
  list: EdgeRow[],
  index: Map<string, number>,
  out: Float32Array,
  pos: Float32Array,
): void {
  for (let i = 0; i < list.length; i++) {
    const a = index.get(list[i].from)! * 2;
    const b = index.get(list[i].to)! * 2;
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

export default function Scene({ data }: { data: Dataset }) {
  const mode = useVizStore((s) => s.mode);
  const showExtinct = useVizStore((s) => s.showExtinct);
  const selected = useVizStore((s) => s.selected);
  const select = useVizStore((s) => s.select);
  const { nodes, edges, index } = data;
  const N = nodes.length;

  const meshRef = useRef<THREE.InstancedMesh>(null);
  const autoAttr = useRef<THREE.BufferAttribute>(null);
  const legiAttr = useRef<THREE.BufferAttribute>(null);
  const dummy = useMemo(() => new THREE.Object3D(), []);
  const { invalidate } = useThree();

  const autoridadEdges = useMemo(() => edges.filter((e) => e.type === "autoridad"), [edges]);
  const legitimidadEdges = useMemo(() => edges.filter((e) => e.type === "legitimidad"), [edges]);
  const current = useMemo(
    () => Float32Array.from(nodes.flatMap((n) => [n.pos_graph.x, n.pos_graph.y])),
    [nodes],
  );
  const autoArray = useMemo(() => new Float32Array(autoridadEdges.length * 6), [autoridadEdges]);
  const legiArray = useMemo(() => new Float32Array(legitimidadEdges.length * 6), [legitimidadEdges]);

  // Colors: by government level; extinct organs go grey (R9 — they stay visible).
  useLayoutEffect(() => {
    const mesh = meshRef.current;
    if (!mesh) return;
    const c = new THREE.Color();
    nodes.forEach((n, i) => {
      const base = n.extinct ? EXTINCT_COLOR : c.set(LEVEL_COLORS[n.level]);
      mesh.setColorAt(i, n.id === selected ? c.set("#ffffff") : base);
    });
    if (mesh.instanceColor) mesh.instanceColor.needsUpdate = true;
    invalidate();
  }, [nodes, selected, invalidate]);

  useFrame((_, dt) => {
    const mesh = meshRef.current;
    if (!mesh) return;
    for (let i = 0; i < N; i++) {
      const n = nodes[i];
      let tx = n.pos_graph.x;
      let ty = n.pos_graph.y;
      if (mode === "mapa" && n.pos_geo) {
        [tx, ty] = projectGeo(n.pos_geo.lon, n.pos_geo.lat);
        const [ox, oy] = geoOffset(n.node_type);
        tx += ox;
        ty += oy;
      }
      current[i * 2] = THREE.MathUtils.damp(current[i * 2], tx, LERP_LAMBDA, dt);
      current[i * 2 + 1] = THREE.MathUtils.damp(current[i * 2 + 1], ty, LERP_LAMBDA, dt);
      const hidden = n.extinct && !showExtinct;
      dummy.position.set(current[i * 2], current[i * 2 + 1], n.id === selected ? 1 : 0);
      dummy.scale.setScalar(hidden ? 0 : nodeRadius(n) * (n.id === selected ? 1.8 : 1));
      dummy.updateMatrix();
      mesh.setMatrixAt(i, dummy.matrix);
    }
    mesh.instanceMatrix.needsUpdate = true;
    writeSegments(autoridadEdges, index, autoArray, current);
    writeSegments(legitimidadEdges, index, legiArray, current);
    if (autoAttr.current) autoAttr.current.needsUpdate = true;
    if (legiAttr.current) legiAttr.current.needsUpdate = true;
  });

  return (
    <>
      <MapControls enableRotate={false} screenSpacePanning minZoom={2} maxZoom={200} makeDefault />
      <instancedMesh
        ref={meshRef}
        args={[undefined, undefined, N]}
        frustumCulled={false}
        onClick={(e) => {
          e.stopPropagation();
          const i = e.instanceId;
          if (i !== undefined) select(nodes[i].id);
        }}
        onPointerMissed={() => select(null)}
      >
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
        <lineBasicMaterial color={EDGE_COLORS.autoridad} transparent opacity={0.35} />
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
        <lineBasicMaterial color={EDGE_COLORS.legitimidad} transparent opacity={0.35} />
      </lineSegments>
    </>
  );
}
