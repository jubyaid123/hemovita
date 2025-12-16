export const REF: Record<
  string,
  {
    low?: number;
    high?: number;
  }
> = {
  Hemoglobin: { low: 12.0, high: 16.0 },
  MCV: { low: 80, high: 100 },
  ferritin: { low: 30, high: 200 },
  indicator_iron_serum: { low: 60, high: 170 },
  transferrin: { low: 200, high: 360 },
  total_iron_binding_capacity: { low: 250, high: 450 },
  vitamin_B12: { low: 200, high: 900 },
  folate_plasma: { low: 4.0, high: 20.0 },
  vitamin_D: { low: 20, high: 50 },
  vitamin_C: { low: 0.4, high: 2.0 },
  vitamin_E: { low: 5.0, high: 20.0 },
  vitamin_A: { low: 20, high: 80 },
  vitamin_B6: { low: 5, high: 50 },
  magnesium: { low: 1.7, high: 2.3 },
  calcium: { low: 8.6, high: 10.2 },
  zinc: { low: 60, high: 120 },
  homocysteine: { low: 5, high: 15 }
};

export function classifyValue(marker: string, value?: number) {
  const r = REF[marker];
  if (value == null || Number.isNaN(value) || !r) return "unknown";
  if (r.low != null && value < r.low) return "low";
  if (r.high != null && value > r.high) return "high";
  return "normal";
}
