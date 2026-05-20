import { useEffect, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { getDatasetDetail } from "../api/datasets";
import { createAnalysisSession, listAnalysisSessions } from "../api/sessions";
import { BackButton } from "../components/BackButton";
import { PreviewTable } from "../components/PreviewTable";
import { SchemaTable } from "../components/SchemaTable";
import type { DatasetDetail } from "../types/dataset";
import type { AnalysisSession } from "../types/session";

export function DatasetDetailPage() {
  const { datasetId } = useParams();
  const navigate = useNavigate();
  const [dataset, setDataset] = useState<DatasetDetail | null>(null);
  const [sessions, setSessions] = useState<AnalysisSession[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [creatingSession, setCreatingSession] = useState(false);

  useEffect(() => {
    async function loadDataset() {
      if (!datasetId) return;
      setLoading(true);
      setError(null);
      try {
        const numericDatasetId = Number(datasetId);
        const [datasetData, sessionData] = await Promise.all([
          getDatasetDetail(numericDatasetId),
          listAnalysisSessions(numericDatasetId),
        ]);
        setDataset(datasetData);
        setSessions(sessionData);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to load dataset");
      } finally {
        setLoading(false);
      }
    }
    loadDataset();
  }, [datasetId]);

  async function handleAnalyze() {
    if (!dataset) return;
    setCreatingSession(true);
    try {
      const session = await createAnalysisSession(dataset.id, `Analysis for ${dataset.name}`);
      navigate(`/sessions/${session.id}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to create session");
    } finally {
      setCreatingSession(false);
    }
  }

  if (loading) return <p className="text-sm text-slate-500">Loading dataset...</p>;
  if (error) return <p className="rounded-md bg-red-50 p-3 text-sm text-red-700">{error}</p>;
  if (!dataset) return null;

  return (
    <div className="space-y-6">
      <div className="flex justify-start">
        <BackButton fallbackTo="/workspace" label="Back" />
      </div>

      <div className="flex flex-col justify-between gap-3 sm:flex-row sm:items-center">
        <div>
          <h1 className="mt-2 text-2xl font-semibold text-slate-950">{dataset.name}</h1>
        </div>
        <button onClick={handleAnalyze} disabled={creatingSession} className="rounded-md bg-slate-900 px-4 py-2 text-sm font-medium text-white disabled:bg-slate-400">
          {creatingSession ? "Creating..." : "Analyze"}
        </button>
      </div>

      <section className="rounded-lg border border-slate-200 bg-white p-4">
        <h2 className="text-base font-semibold text-slate-950">Metadata</h2>
        <dl className="mt-4 grid gap-3 text-sm sm:grid-cols-2 lg:grid-cols-4">
          <Meta label="File" value={dataset.original_filename} />
          <Meta label="Type" value={dataset.file_type} />
          <Meta label="Rows" value={dataset.row_count ?? "-"} />
          <Meta label="Columns" value={dataset.column_count ?? "-"} />
          <Meta label="Sheets" value={dataset.sheet_count ?? "-"} />
          <Meta label="Status" value={dataset.status} />
          <Meta label="Storage" value={dataset.storage_backend} />
          <Meta label="Size" value={`${dataset.file_size_bytes} bytes`} />
        </dl>
      </section>

      <section className="rounded-lg border border-slate-200 bg-white p-4">
        <h2 className="text-base font-semibold text-slate-950">Data Catalog</h2>
        <div className="mt-4">
          <SchemaTable schema={dataset.schema} />
        </div>
      </section>

      <section className="rounded-lg border border-slate-200 bg-white p-4">
        <h2 className="text-base font-semibold text-slate-950">Head5 Preview</h2>
        <div className="mt-4">
          <PreviewTable previewColumns={dataset.preview_columns} previewRows={dataset.preview_rows} />
        </div>
      </section>

      <section className="rounded-lg border border-slate-200 bg-white p-4">
        <div className="flex items-center justify-between gap-3">
          <h2 className="text-base font-semibold text-slate-950">Analysis Sessions</h2>
          <button onClick={handleAnalyze} disabled={creatingSession} className="rounded-md bg-slate-900 px-3 py-2 text-sm font-medium text-white disabled:bg-slate-400">
            {creatingSession ? "Creating..." : "New Session"}
          </button>
        </div>
        {sessions.length === 0 ? (
          <p className="mt-4 text-sm text-slate-500">No sessions for this dataset yet.</p>
        ) : (
          <div className="mt-4 divide-y divide-slate-200 rounded-lg border border-slate-200">
            {sessions.map((session) => (
              <Link
                key={session.id}
                to={`/sessions/${session.id}`}
                className="flex items-center justify-between gap-4 px-4 py-3 hover:bg-slate-50"
              >
                <div>
                  <div className="font-medium text-slate-950">{session.title}</div>
                  <div className="text-xs text-slate-500">Session #{session.id}</div>
                </div>
                <div className="text-right text-xs text-slate-500">
                  Updated {new Date(session.updated_at).toLocaleString()}
                </div>
              </Link>
            ))}
          </div>
        )}
      </section>
    </div>
  );
}

function Meta({ label, value }: { label: string; value: string | number }) {
  return (
    <div>
      <dt className="text-xs uppercase tracking-wide text-slate-500">{label}</dt>
      <dd className="mt-1 font-medium text-slate-900">{value}</dd>
    </div>
  );
}
