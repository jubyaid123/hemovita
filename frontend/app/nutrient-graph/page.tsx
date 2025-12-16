import NutrientGraph3D from "@/components/visuals/nutrient-graph-3d";

export const metadata = {
  title: "Nutrient Graph | Hemovita",
};

export default function Page() {
  return (
    <main className="p-6 md:p-8 lg:p-10 space-y-6">
      <div className="space-y-1">
        <h1 className="text-2xl font-bold tracking-tight">Nutrient Graph</h1>
        <p className="text-sm text-slate-600">
          Explore nutrient relationships in 3D. Node color = type, node size = metric
          (importance, risk, confidence), edge color = relationship.
        </p>
      </div>
      <NutrientGraph3D />
    </main>
  );
}

