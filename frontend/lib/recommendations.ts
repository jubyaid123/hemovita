import { classifyValue } from "./ref";
import { type LabInputs } from "./validators/labs";

export type MarkerClassification = {
  marker: keyof LabInputs | (string & {});
  value?: number;
  status: "low" | "normal" | "high" | "unknown";
  note: string;
};

export type ScheduleItem = {
  title: string;
  timeframe: string;
  description: string;
};

export type RecommendationPayload = {
  markers: MarkerClassification[];
  summary: string;
  schedule: ScheduleItem[];
};

const NOTES: Record<string, { low?: string; high?: string }> = {
  Hemoglobin: {
    low: "Hemoglobin is below the reference range and may indicate anemia or iron deficiency.",
    high: "Elevated hemoglobin can be associated with dehydration or chronic hypoxia."
  },
  MCV: {
    low: "Low MCV values can signal microcytic anemia, often linked to iron deficiency.",
    high: "High MCV is associated with macrocytic anemia and can reflect B12 or folate deficiency."
  },
  ferritin: {
    low: "Low ferritin is a strong indicator of depleted iron stores.",
    high: "High ferritin can be inflammatory or signal iron overload."
  },
  vitamin_B12: {
    low: "Low B12 may contribute to neuropathy and macrocytic anemia.",
    high: "Elevated B12 can be linked to supplementation or liver dysfunction."
  },
  folate_plasma: {
    low: "Low folate can impair cell division and contribute to macrocytic anemia.",
    high: "High folate is usually benign but can mask B12 deficiency symptoms."
  },
  vitamin_D: {
    low: "Low vitamin D is associated with bone density loss and immune dysregulation.",
    high: "High vitamin D may cause hypercalcemia; ensure dosing is appropriate."
  },
  homocysteine: {
    high: "Elevated homocysteine is a cardiovascular risk marker and may respond to B12, folate, and B6."
  }
};

export function buildRecommendations(values: LabInputs): RecommendationPayload {
  const markers = Object.entries(values).map(([marker, value]) => {
    const status = classifyValue(marker, value);
    const note =
      NOTES[marker]?.[status as keyof (typeof NOTES)[string]] ??
      (status === "normal"
        ? "Within the reference range; continue current support."
        : "No reference available for this marker.");
    return {
      marker: marker as MarkerClassification["marker"],
      status,
      value,
      note
    };
  });

  const summary = summarize(markers);

  return {
    markers,
    summary,
    schedule: buildSchedule(markers)
  };
}

function summarize(classifications: MarkerClassification[]) {
  const lowCount = classifications.filter((c) => c.status === "low").length;
  const highCount = classifications.filter((c) => c.status === "high").length;
  if (lowCount === 0 && highCount === 0) {
    return "All submitted markers are currently within the reference range.";
  }
  const parts = [];
  if (lowCount) parts.push(`${lowCount} low`);
  if (highCount) parts.push(`${highCount} high`);
  return `Detected ${parts.join(" and ")} marker${lowCount + highCount > 1 ? "s" : ""}. Prioritize follow-up with your provider.`;
}

function buildSchedule(classifications: MarkerClassification[]): ScheduleItem[] {
  const hasIronIssues = classifications.some(
    (c) =>
      (c.marker === "Hemoglobin" || c.marker === "ferritin" || c.marker === "indicator_iron_serum") &&
      c.status === "low"
  );
  const hasBComplexIssues = classifications.some(
    (c) =>
      (c.marker === "vitamin_B12" || c.marker === "folate_plasma" || c.marker === "vitamin_B6") &&
      (c.status === "low" || c.status === "high")
  );
  const hasVitaminDIssue = classifications.some((c) => c.marker === "vitamin_D" && c.status !== "normal");
  const followUps = classifications.filter((c) => c.status !== "normal").length;

  const schedule: ScheduleItem[] = [
    {
      title: "Lifestyle Check-in",
      timeframe: "This week",
      description:
        "Review dietary intake, sleep, and stress. Capture at least three days of meals to discuss with your care team."
    },
    {
      title: "Practitioner Review",
      timeframe: followUps > 0 ? "Within 2 weeks" : "Within 6 months",
      description: followUps
        ? "Share these results with your primary care provider or dietitian to confirm next steps."
        : "Maintain routine monitoring with your healthcare provider."
    }
  ];

  if (hasIronIssues) {
    schedule.push({
      title: "Iron Re-evaluation",
      timeframe: "In 6-8 weeks",
      description: "Re-check hemoglobin, ferritin, and transferrin saturation after implementing dietary or supplement changes."
    });
  }
  if (hasBComplexIssues) {
    schedule.push({
      title: "B-Vitamin Follow-up",
      timeframe: "In 8 weeks",
      description: "Assess B12, folate, and homocysteine after adjusting intake or supplements."
    });
  }
  if (hasVitaminDIssue) {
    schedule.push({
      title: "Vitamin D Monitoring",
      timeframe: "In 12 weeks",
      description: "Re-test 25(OH)D to ensure levels trend toward the target range."
    });
  }

  return schedule;
}
