import { NextResponse } from "next/server";
import path from "path";
import { promises as fs } from "fs";

type RelationType = "booster" | "antagonist" | "cofactor" | "shared";
type NutrientType = "vitamin" | "mineral" | "marker" | "compound";

interface CsvEdge {
  source: string;
  target: string;
  effect: string; // boosts | inhibits | ...
  confidence: string; // High | Moderate-High | ...
  notes: string;
}

function mapEffectToRelation(effect: string): RelationType {
  const e = effect.trim().toLowerCase();
  if (e === "boosts" || e === "enhances") return "booster";
  if (e === "inhibits" || e === "reduces" || e === "blocks") return "antagonist";
  if (e === "cofactor" || e === "supports") return "cofactor";
  return "shared";
}

function confidenceToNumber(conf: string): number {
  const c = conf.trim().toLowerCase();
  if (c.includes("high") && c.includes("moderate")) return 0.75;
  if (c.includes("high")) return 0.9;
  if (c.includes("moderate") && c.includes("low")) return 0.45;
  if (c.includes("moderate")) return 0.6;
  if (c.includes("low")) return 0.3;
  return 0.5;
}

const MINERALS = new Set([
  "iron",
  "zinc",
  "magnesium",
  "calcium",
  "copper",
  "selenium",
]);

function classifyNodeType(id: string): NutrientType {
  const k = id.toLowerCase();
  if (k.startsWith("vitamin_")) return "vitamin";
  if (MINERALS.has(k)) return "mineral";
  if (
    k.includes("hemoglobin") ||
    k.includes("ferritin") ||
    k.includes("transferrin") ||
    k.includes("mcv") ||
    k.includes("tibc") ||
    k.includes("indicator_") ||
    k.includes("homocysteine") ||
    k.includes("anemia")
  ) {
    return "marker";
  }
  return "compound";
}

function clusterOf(id: string): "iron" | "b-complex" | "fat-soluble" | "other" {
  const k = id.toLowerCase();
  if (
    k.includes("iron") ||
    k.includes("hemoglobin") ||
    k.includes("ferritin") ||
    k.includes("transferrin") ||
    k.includes("tibc")
  )
    return "iron";
  if (k.startsWith("vitamin_b")) return "b-complex";
  if (k === "vitamin_a" || k === "vitamin_d" || k === "vitamin_e" || k === "vitamin_k")
    return "fat-soluble";
  return "other";
}

export async function GET() {
  try {
    const csvPath = path.resolve(process.cwd(), "../cleaned_data/network_relationships.csv");
    const raw = await fs.readFile(csvPath, "utf8");

    const lines = raw.split(/\r?\n/).filter((l) => l.trim().length > 0);
    const header = lines.shift();
    if (!header) return NextResponse.json({ error: "Empty CSV" }, { status: 500 });

    const edges: CsvEdge[] = [];
    for (const line of lines) {
      // Robust-ish parsing: split by comma into at least 5 fields, join the rest as notes
      const parts = line.split(",");
      if (parts.length < 5) continue;
      const [source, target, effect, confidence, ...notesParts] = parts;
      const notes = notesParts.join(",").trim();
      edges.push({ source: source.trim(), target: target.trim(), effect: effect.trim(), confidence: confidence.trim(), notes });
    }

    // Build node set and aggregate metrics
    const nodeSet = new Map<string, { id: string; degree: number; confidences: number[] }>();
    const links = edges.map((e) => {
      const rel = mapEffectToRelation(e.effect);
      const confNum = confidenceToNumber(e.confidence);
      if (!nodeSet.has(e.source)) nodeSet.set(e.source, { id: e.source, degree: 0, confidences: [] });
      if (!nodeSet.has(e.target)) nodeSet.set(e.target, { id: e.target, degree: 0, confidences: [] });
      nodeSet.get(e.source)!.degree += 1;
      nodeSet.get(e.target)!.degree += 1;
      nodeSet.get(e.source)!.confidences.push(confNum);
      nodeSet.get(e.target)!.confidences.push(confNum);
      return {
        source: e.source,
        target: e.target,
        relation: rel,
        strength: confNum,
        confidenceLabel: e.confidence,
        notes: e.notes,
      };
    });

    // Normalize degree to 0..1 for importance; compute avg confidence
    const maxDeg = Math.max(1, ...Array.from(nodeSet.values()).map((n) => n.degree));
    const nodes = Array.from(nodeSet.values()).map((n) => {
      const confAvg = n.confidences.length
        ? n.confidences.reduce((a, b) => a + b, 0) / n.confidences.length
        : 0.5;
      const id = n.id;
      return {
        id,
        label: id.replaceAll("_", " "),
        type: classifyNodeType(id),
        cluster: clusterOf(id),
        importance: n.degree / maxDeg,
        risk: id.includes("anemia") ? 1 : 0.5,
        confidence: confAvg,
      };
    });

    return NextResponse.json({ nodes, links }, { status: 200 });
  } catch (e: any) {
    return NextResponse.json({ error: e?.message ?? "Failed to load network" }, { status: 500 });
  }
}

