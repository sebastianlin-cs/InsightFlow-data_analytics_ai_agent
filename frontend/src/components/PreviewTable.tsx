type Props = {
  previewColumns: string[];
  previewRows: Record<string, unknown>[];
};

export function PreviewTable({ previewColumns, previewRows }: Props) {
  if (previewColumns.length === 0 || previewRows.length === 0) {
    return <p className="text-sm text-slate-500">No preview rows.</p>;
  }

  return (
    <div className="overflow-x-auto rounded-lg border border-slate-200">
      <table className="min-w-full divide-y divide-slate-200 text-sm">
        <thead className="bg-slate-100 text-left text-xs uppercase tracking-wide text-slate-600">
          <tr>
            {previewColumns.map((column) => (
              <th key={column} className="px-4 py-3">
                {column}
              </th>
            ))}
          </tr>
        </thead>
        <tbody className="divide-y divide-slate-200 bg-white">
          {previewRows.map((row, index) => (
            <tr key={index}>
              {previewColumns.map((column) => (
                <td key={column} className="px-4 py-3">
                  {row[column] === null || row[column] === undefined ? "-" : String(row[column])}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
