import { useEffect, useState } from "react";
import { deleteDataset, listDatasets } from "../api/datasets";
import { DatasetTable } from "../components/DatasetTable";
import { DatasetUpload } from "../components/DatasetUpload";
import type { Dataset } from "../types/dataset";

export function WorkspacePage() {
  const [datasets, setDatasets] = useState<Dataset[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  async function loadDatasets() {
    setLoading(true);
    setError(null);
    try {
      setDatasets(await listDatasets());
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load datasets");
    } finally {
      setLoading(false);
    }
  }

  async function handleDelete(datasetId: number) {
    if (!confirm("Delete this dataset?")) return;
    await deleteDataset(datasetId);
    loadDatasets();
  }

  useEffect(() => {
    loadDatasets();
  }, []);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold text-slate-950">Workspace</h1>
        <p className="mt-1 text-sm text-slate-600">Datasets available for analysis.</p>
      </div>
      <DatasetUpload onUploaded={loadDatasets} />
      {error && <p className="rounded-md bg-red-50 p-3 text-sm text-red-700">{error}</p>}
      {loading ? <p className="text-sm text-slate-500">Loading datasets...</p> : <DatasetTable datasets={datasets} onDelete={handleDelete} />}
    </div>
  );
}
