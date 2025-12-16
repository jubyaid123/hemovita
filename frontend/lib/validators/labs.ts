import { z } from "zod";

const numericField = (label: string, min?: number, max?: number) =>
  z
    .union([z.string(), z.number(), z.null(), z.undefined()])
    .transform((val) => {
      if (val === null || val === undefined) return undefined;
      if (typeof val === "number") return Number.isFinite(val) ? val : NaN;
      const trimmed = val.trim();
      if (!trimmed) return undefined;
      const parsed = Number(trimmed);
      return Number.isFinite(parsed) ? parsed : NaN;
    })
    .refine((val) => val === undefined || !Number.isNaN(val), {
      message: `${label} must be a number`
    })
    .refine((val) => (val === undefined || min === undefined ? true : val >= min), {
      message: `${label} must be at least ${min}`
    })
    .refine((val) => (val === undefined || max === undefined ? true : val <= max), {
      message: `${label} must be at most ${max}`
    });

export const labSchema = z.object({
  Hemoglobin: numericField("Hemoglobin", 0, 25),
  MCV: numericField("MCV", 40, 150),
  ferritin: numericField("Ferritin", 0, 500),
  // indicator_iron_serum: numericField("Serum Iron", 0, 400),
  // transferrin: numericField("Transferrin", 0, 600),
  // total_iron_binding_capacity: numericField("Total Iron Binding Capacity", 0, 600),
  vitamin_B12: numericField("Vitamin B12", 0, 2000),
  folate_plasma: numericField("Folate", 0, 40),
  vitamin_D: numericField("Vitamin D", 0, 150),
  magnesium: numericField("Magnesium", 0, 4),
  zinc: numericField("Zinc", 0, 300),
  calcium: numericField("Calcium", 0, 15),
  vitamin_C: numericField("Vitamin C", 0, 5),
  vitamin_A: numericField("Vitamin A", 0, 120),
  vitamin_E: numericField("Vitamin E", 0, 40),
  vitamin_B6: numericField("Vitamin B6", 0, 80),
  homocysteine: numericField("Homocysteine", 0, 100)
});

export type LabInputs = {
  Hemoglobin?: number;
  MCV?: number;
  ferritin?: number;
  indicator_iron_serum?: number;
  transferrin?: number;
  total_iron_binding_capacity?: number;
  vitamin_B12?: number;
  folate_plasma?: number;
  vitamin_D?: number;
  magnesium?: number;
  zinc?: number;
  calcium?: number;
  vitamin_C?: number;
  vitamin_A?: number;
  vitamin_E?: number;
  vitamin_B6?: number;
  homocysteine?: number;
};

export function toLabInputs(values: unknown): LabInputs {
  const parsed = labSchema.safeParse(values);
  if (!parsed.success) {
    throw parsed.error;
  }
  return parsed.data as LabInputs;
}
