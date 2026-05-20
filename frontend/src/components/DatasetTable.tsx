import { Link } from "react-router-dom";
import type { Dataset } from "../types/dataset";

type Props = {
  datasets: Dataset[];
  onDelete: (datasetId: number) => void;
};

export function DatasetTable({ datasets, onDelete }: Props) {
  if (datasets.length === 0) {
    return <div className="rounded-lg border border-dashed border-slate-300 bg-white p-8 text-center text-slate-500">No datasets yet.</div>;
  }

  return (
    <div className="overflow-x-auto rounded-lg border border-slate-200 bg-white">
      <table className="min-w-full divide-y divide-slate-200 text-sm">
        <thead className="bg-slate-100 text-left text-xs uppercase tracking-wide text-slate-600">
          <tr>
            <th className="px-4 py-3">ID</th>
            <th className="px-4 py-3">Name</th>
            <th className="px-4 py-3">File</th>
            <th className="px-4 py-3">Type</th>
            <th className="px-4 py-3">Rows</th>
            <th className="px-4 py-3">Columns</th>
            <th className="px-4 py-3">Sheets</th>
            <th className="px-4 py-3">Status</th>
            <th className="px-4 py-3">Created</th>
            <th className="px-4 py-3">Actions</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-slate-200">
          {datasets.map((dataset) => (
            <tr key={dataset.id}>
              <td className="px-4 py-3">{dataset.id}</td>
              <td className="px-4 py-3 font-medium text-slate-950">{dataset.name}</td>
              <td className="px-4 py-3">{dataset.original_filename}</td>
              <td className="px-4 py-3">{dataset.file_type}</td>
              <td className="px-4 py-3">{dataset.row_count ?? "-"}</td>
              <td className="px-4 py-3">{dataset.column_count ?? "-"}</td>
              <td className="px-4 py-3">{dataset.sheet_count ?? "-"}</td>
              <td className="px-4 py-3">{dataset.status}</td>
              <td className="px-4 py-3">{new Date(dataset.created_at).toLocaleString()}</td>
              <td className="px-4 py-3">
                <div className="flex gap-2">
                  <Link className="rounded-md bg-slate-900 px-3 py-1.5 text-xs font-medium text-white" to={`/datasets/${dataset.id}`}>
                    Open Detail
                  </Link>
                  <button
                    onClick={() => onDelete(dataset.id)}
                    className="rounded-md border border-red-200 px-3 py-1.5 text-xs font-medium text-red-700 hover:bg-red-50"
                  >
                    Delete
                  </button>
                </div>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
