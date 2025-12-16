"use client";
import React, { useEffect, useMemo, useRef, useState } from "react";

type NutrientType = "vitamin" | "mineral" | "marker" | "compound";
type RelationType = "booster" | "antagonist" | "cofactor" | "shared";

type SizeMetric = "importance" | "risk" | "confidence";

interface NutrientNode {
  id: string;
  label: string;
  type: NutrientType;
  cluster: "iron" | "b-complex" | "fat-soluble" | "other";
  importance: number; // 0..1
  risk: number; // 0..1 (deficiency risk)
  confidence: number; // 0..1 (evidence confidence)
}

interface NutrientLink {
  source: string;
  target: string;
  relation: RelationType;
  strength?: number; // 0..1
}

type RecommendationSnapshot = {
  deficiencies?: string[];
  highRisk?: string[];
  networkNotes?: string[];
  createdAt?: number;
};

// Fetch graph data from API (backed by cleaned_data/network_relationships.csv)
async function fetchGraph(): Promise<{ nodes: NutrientNode[]; links: NutrientLink[] }> {
  const res = await fetch("/api/network/graph", { cache: "no-store" });
  if (!res.ok) throw new Error(`Failed to load graph: ${res.status}`);
  const data = await res.json();
  return data;
}

const NODE_COLORS: Record<NutrientType, string> = {
  vitamin: "#f59e0b", // amber-500
  mineral: "#0ea5e9", // sky-500
  marker: "#64748b", // slate-500
  compound: "#10b981", // emerald-500 (reserved)
};

const LINK_COLORS: Record<RelationType, string> = {
  booster: "#16a34a", // green-600
  antagonist: "#dc2626", // red-600
  cofactor: "#2563eb", // blue-600
  shared: "#6b7280", // gray-500
};

function normalizeId(value: string) {
  return value.toLowerCase().replace(/\s+/g, "_");
}

export default function NutrientGraph3D() {
  const containerRef = useRef<HTMLDivElement | null>(null);
  const fgRef = useRef<any>(null);
  const [nodes, setNodes] = useState<NutrientNode[]>([]);
  const [links, setLinks] = useState<NutrientLink[]>([]);

  const [sizeMetric, setSizeMetric] = useState<SizeMetric>("importance");
  const [showRel, setShowRel] = useState<Record<RelationType, boolean>>({
    booster: true,
    antagonist: true,
    cofactor: true,
    shared: true,
  });
  const [deficiencyNames, setDeficiencyNames] = useState<string[]>([]);
  const [highRiskNames, setHighRiskNames] = useState<string[]>([]);
  const [networkNotes, setNetworkNotes] = useState<string[]>([]);
  const [snapshotTime, setSnapshotTime] = useState<number | null>(null);
  const [highlightedIds, setHighlightedIds] = useState<Set<string>>(new Set());

  const [threeLib, setThreeLib] = useState<any>(null);
  const [fgFactory, setFgFactory] = useState<((opts?: any) => (el: HTMLElement) => any) | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loadingData, setLoadingData] = useState(true);
  const [loadingLibs, setLoadingLibs] = useState(true);

  useEffect(() => {
    let cancelled = false;
    setLoadingData(true);
    fetchGraph()
      .then((d) => {
        if (cancelled) return;
        setNodes(d.nodes);
        setLinks(d.links);
      })
      .catch((e) => {
        if (!cancelled) setError(e.message ?? "Failed to load graph data");
      })
      .finally(() => {
        if (!cancelled) setLoadingData(false);
      });
    return () => {
      cancelled = true;
    };
  }, []);

  useEffect(() => {
    if (typeof window === "undefined") return;
    const raw = localStorage.getItem("hemovita:lastRecommendation");
    if (!raw) return;
    try {
      const parsed: RecommendationSnapshot = JSON.parse(raw);
      setDeficiencyNames(parsed.deficiencies ?? []);
      setHighRiskNames(parsed.highRisk ?? []);
      setNetworkNotes(parsed.networkNotes ?? []);
      setSnapshotTime(parsed.createdAt ?? null);
    } catch (err) {
      console.error("Failed to parse saved recommendation snapshot", err);
    }
  }, []);

  const filtered = useMemo(() => {
    const activeLinks = links.filter((l) => showRel[l.relation as RelationType]);
    // Keep all nodes to preserve layout; alternatively filter isolated nodes here
    return { nodes, links: activeLinks };
  }, [links, nodes, showRel]);

  const flagged = useMemo(
    () => Array.from(new Set([...deficiencyNames, ...highRiskNames])),
    [deficiencyNames, highRiskNames],
  );

  useEffect(() => {
    if (!nodes.length) {
      setHighlightedIds(new Set());
      return;
    }
    const targets = new Set<string>();
    [...deficiencyNames, ...highRiskNames].forEach((name) => {
      targets.add(normalizeId(name));
    });
    const matched = new Set<string>();
    nodes.forEach((n) => {
      const idNorm = normalizeId(n.id);
      if (targets.has(idNorm) || targets.has(normalizeId(n.label))) {
        matched.add(n.id);
      }
    });
    setHighlightedIds(matched);
  }, [deficiencyNames, highRiskNames, nodes]);

  useEffect(() => {
    let cancelled = false;
    setLoadingLibs(true);
    Promise.all([import("three"), import("3d-force-graph")])
      .then(([three, fg]) => {
        if (cancelled) return;
        setThreeLib(three);
        const factory = (fg as any).default ?? fg;
        setFgFactory(() => factory);
      })
      .catch(() => {
        if (!cancelled) setError("Failed to load 3D graph library");
      })
      .finally(() => {
        if (!cancelled) setLoadingLibs(false);
      });
    return () => {
      cancelled = true;
    };
  }, []);

  useEffect(() => {
    if (!fgFactory || !threeLib) return;
    if (!containerRef.current) return;

    const nodeValue = (n: NutrientNode) => {
      const base = 5 + 12 * (n[sizeMetric] ?? 0.5);
      return highlightedIds.has(n.id) ? base + 6 : base;
    };

    const setSizeFromContainer = () => {
      if (!containerRef.current || !fgRef.current) return;
      fgRef.current.width(containerRef.current.clientWidth);
      fgRef.current.height(containerRef.current.clientHeight);
    };

    if (!fgRef.current) {
      fgRef.current = fgFactory()(containerRef.current)
        .nodeId("id")
        .nodeLabel((n: NutrientNode) => `${n.label} (${n.type})`)
        .nodeVal(nodeValue)
        .linkColor((l: NutrientLink) => LINK_COLORS[(l as any).relation as RelationType] || "#6b7280")
        .linkOpacity(0.7)
        .linkWidth(0.6)
        .linkDirectionalParticles((l: NutrientLink) =>
          ((l as any).relation === "booster" || (l as any).relation === "antagonist") ? 2 : 0
        )
        .linkDirectionalParticleWidth(2)
        .linkDirectionalParticleColor((l: NutrientLink) => LINK_COLORS[(l as any).relation as RelationType] || "#6b7280")
        .backgroundColor("rgba(0,0,0,0)")
        .showNavInfo(false);

      // Pull clusters apart a bit
      try {
        fgRef.current
          .d3Force("charge")
          .strength(-80);
        fgRef.current
          .d3Force("link")
          .distance((l: any) => {
            const s = nodes.find((n) => n.id === (l.source.id ?? l.source))?.cluster;
            const t = nodes.find((n) => n.id === (l.target.id ?? l.target))?.cluster;
            return s && t && s === t ? 35 : 90;
          });
      } catch {
        // If d3Force not available, ignore
      }

      setSizeFromContainer();
    }

    setSizeFromContainer();
    fgRef.current?.nodeThreeObject((n: NutrientNode) =>
      buildLabeledNode(n, sizeMetric, threeLib, highlightedIds.has(n.id))
    );
    // Update size metric on change
    fgRef.current?.nodeVal(nodeValue);
    fgRef.current?.graphData(filtered);
    window.addEventListener("resize", setSizeFromContainer);
    return () => window.removeEventListener("resize", setSizeFromContainer);
  }, [filtered, highlightedIds, sizeMetric, fgFactory, nodes, threeLib]);

  return (
    <div className="w-full h-full flex flex-col gap-4">
      <div className="flex flex-wrap items-center gap-3">
        <h2 className="text-xl font-semibold">Nutrient Relationship Graph (3D)</h2>
        <div className="ml-auto flex items-center gap-2">
          <label className="text-sm text-slate-600">Node size</label>
          <select
            className="border rounded px-2 py-1 text-sm"
            value={sizeMetric}
            onChange={(e) => setSizeMetric(e.target.value as SizeMetric)}
          >
            <option value="importance">Importance</option>
            <option value="risk">Deficiency Risk</option>
            <option value="confidence">Confidence</option>
          </select>
        </div>
      </div>

      <div className="flex flex-wrap gap-6 items-center">
        <Legend />
        <RelFilters value={showRel} onChange={setShowRel} />
      </div>

      <div className="rounded-md border bg-amber-50/70 p-3 text-sm space-y-2">
        <div className="font-semibold">Deficiencies from your last recommendation</div>
        {flagged.length > 0 ? (
          <div className="flex flex-wrap gap-2">
            {flagged.map((name) => (
              <span
                key={name}
                className="rounded-full border border-red-200 bg-red-50 px-3 py-1 text-xs font-semibold capitalize text-red-700"
              >
                {name.replace(/_/g, " ")}
              </span>
            ))}
          </div>
        ) : (
          <p className="text-slate-600">
            Run a recommendation to highlight flagged nutrients here and in the graph.
          </p>
        )}
        {snapshotTime ? (
          <p className="text-xs text-slate-500">
            Saved {new Date(snapshotTime).toLocaleString()}
          </p>
        ) : null}
      </div>

      <div
        ref={containerRef}
        className="rounded-md border bg-white/40 dark:bg-slate-900/10"
        style={{ height: "70vh", minHeight: 400, width: "100%", overflow: "hidden" }}
      />

      {(loadingData || loadingLibs || !fgFactory) && (
        <div className="text-sm text-slate-500">Loading 3D engine...</div>
      )}
      {error && (
        <div className="text-sm text-red-600">{error}</div>
      )}

      <div className="space-y-2">
        <h3 className="text-sm font-semibold">Notes from your recommendation</h3>
        {networkNotes.length > 0 ? (
          <ul className="space-y-1 text-sm text-slate-700">
            {networkNotes.map((note, idx) => (
              <li key={idx} className="flex gap-2">
                <span className="mt-1 h-1.5 w-1.5 rounded-full bg-slate-400" />
                <span>{note}</span>
              </li>
            ))}
          </ul>
        ) : (
          <p className="text-sm text-slate-500">
            Notes from your last recommendation will appear underneath the graph.
          </p>
        )}
      </div>
    </div>
  );
}

function Legend() {
  return (
    <div className="flex flex-col gap-2 text-sm">
      <div className="font-medium">Legend</div>
      <div className="flex items-center gap-3">
        <Swatch color={NODE_COLORS.vitamin} /> <span>Vitamin</span>
        <Swatch color={NODE_COLORS.mineral} /> <span>Mineral</span>
        <Swatch color={NODE_COLORS.marker} /> <span>Marker</span>
      </div>
      <div className="flex items-center gap-3">
        <LineSwatch color={LINK_COLORS.booster} /> <span>Booster</span>
        <LineSwatch color={LINK_COLORS.antagonist} /> <span>Antagonist</span>
        <LineSwatch color={LINK_COLORS.cofactor} /> <span>Cofactor</span>
        <LineSwatch color={LINK_COLORS.shared} /> <span>Shared Pathway</span>
      </div>
    </div>
  );
}

function RelFilters({
  value,
  onChange,
}: {
  value: Record<RelationType, boolean>;
  onChange: (v: Record<RelationType, boolean>) => void;
}) {
  const toggle = (k: RelationType) => onChange({ ...value, [k]: !value[k] });
  return (
    <div className="flex items-center gap-3 text-sm">
      <span className="font-medium">Relationships</span>
      {(["booster", "antagonist", "cofactor", "shared"] as RelationType[]).map(
        (k) => (
          <label key={k} className="inline-flex items-center gap-1">
            <input
              type="checkbox"
              checked={value[k]}
              onChange={() => toggle(k)}
            />
            <span className="capitalize">{k}</span>
          </label>
        )
      )}
      </div>
  );
}

function buildLabeledNode(n: NutrientNode, metric: SizeMetric, three: any, highlighted = false) {
  const group = new three.Group();
  const radius = 5 + 12 * (n[metric] ?? 0.5);
  const sphereRadius = Math.max(radius * 0.2, 1.5);
  const baseColor = NODE_COLORS[n.type] || "#0ea5e9";

  const sphere = new three.Mesh(
    new three.SphereGeometry(sphereRadius, 16, 16),
    highlighted
      ? new three.MeshLambertMaterial({
          color: baseColor,
          emissive: "#ef4444",
          emissiveIntensity: 0.4,
        })
      : new three.MeshLambertMaterial({ color: baseColor })
  );
  group.add(sphere);

  if (highlighted) {
    const glow = new three.Mesh(
      new three.SphereGeometry(sphereRadius * 1.6, 12, 12),
      new three.MeshBasicMaterial({
        color: "#ef4444",
        transparent: true,
        opacity: 0.25,
      })
    );
    group.add(glow);
  }

  const label = makeTextSprite(three, n.label, "#ffffff", "rgba(0,0,0,0.65)");
  if (label) {
    label.position.set(0, radius * 0.28 + 2, 0);
    group.add(label);
  }

  return group;
}

function makeTextSprite(three: any, text: string, fill: string, background: string) {
  const canvas = document.createElement("canvas");
  const ctx = canvas.getContext("2d");
  if (!ctx) return null;

  const fontSize = 90;
  const padding = 32;
  ctx.font = `${fontSize}px sans-serif`;
  const textWidth = ctx.measureText(text).width;
  canvas.width = textWidth + padding * 2;
  canvas.height = fontSize + padding * 2;

  ctx.font = `${fontSize}px sans-serif`;
  ctx.fillStyle = background;
  ctx.fillRect(0, 0, canvas.width, canvas.height);
  ctx.fillStyle = fill;
  ctx.textBaseline = "middle";
  ctx.fillText(text, padding, canvas.height / 2);

  const texture = new three.CanvasTexture(canvas);
  texture.needsUpdate = true;

  const material = new three.SpriteMaterial({ map: texture, depthWrite: false });
  const sprite = new three.Sprite(material);
  const scale = 0.03; // scale canvas dimensions into world units
  sprite.scale.set(canvas.width * scale, canvas.height * scale, 1);
  sprite.center.set(0.5, 0.5);

  return sprite;
}

function Swatch({ color }: { color: string }) {
  return (
    <span
      className="inline-block rounded-full"
      style={{ width: 12, height: 12, backgroundColor: color }}
    />
  );
}

function LineSwatch({ color }: { color: string }) {
  return (
    <span
      className="inline-block"
      style={{ width: 24, height: 3, backgroundColor: color }}
    />
  );
}
