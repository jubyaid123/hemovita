// Adjust if backend shape changes, but this matches your schema now.
export type FoodItem = {
  name: string;
  category: string;
  serving_g: number | null;
};

export type ReportResponse = {
  labels: Record<string, string>; // e.g. { Hemoglobin: "low", ... }
  supplement_plan: Record<string, string[]>; // e.g. { AM_empty: ["ferritin", "vitamin_C"], ... }
  foods: Record<string, FoodItem[]>; // e.g. { iron: [ { name: "Beef liver", ... }, ... ] }
  network_notes: string[];
  report_text: string;
};
