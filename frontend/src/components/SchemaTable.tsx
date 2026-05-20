import type { DatasetSchema } from "../types/dataset";

type Props = {
  schema: DatasetSchema[];
};

export function SchemaTable({ schema }: Props) {
  if (schema.length === 0) {
    return <p className="text-sm text-slate-500">No catalog records.</p>;
  }

  return (
    <div className="overflow-x-auto rounded-lg border border-slate-200">
      <table className="min-w-full divide-y divide-slate-200 text-sm">
        <thead className="bg-slate-100 text-left text-xs uppercase tracking-wide text-slate-600">
          <tr>
            <th className="px-4 py-3">Column</th>
            <th className="px-4 py-3">Semantic</th>
            <th className="px-4 py-3">Measure</th>
            <th className="px-4 py-3">Dimension</th>
            <th className="px-4 py-3">Time</th>
            <th className="px-4 py-3">Identifier</th>
            <th className="px-4 py-3">Sensitivity</th>
            <th className="px-4 py-3">Missing</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-slate-200 bg-white">
          {schema.map((field) => (
            <tr key={field.id}>
              <td className="px-4 py-3 font-medium text-slate-950">{field.column_name}</td>
              <td className="px-4 py-3">{field.semantic_type}</td>
              <td className="px-4 py-3">{field.is_measure ? "Yes" : "No"}</td>
              <td className="px-4 py-3">{field.is_dimension ? "Yes" : "No"}</td>
              <td className="px-4 py-3">{field.is_time_column ? "Yes" : "No"}</td>
              <td className="px-4 py-3">{field.is_identifier ? "Yes" : "No"}</td>
              <td className="px-4 py-3">{field.sensitivity_tag}</td>
              <td className="px-4 py-3">{(field.missing_rate * 100).toFixed(1)}%</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
