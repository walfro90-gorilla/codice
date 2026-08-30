"use client";

import dynamic from "next/dynamic";

// WebGL only lives in the browser: no SSR for the visualization.
const Viz = dynamic(() => import("../components/Viz"), { ssr: false });

export default function Page() {
  return <Viz />;
}
