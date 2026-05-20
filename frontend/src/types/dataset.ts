export type Dataset = {
  id: number;
  name: string;
  description: string | null;
  original_filename: string;
  stored_filename: string;
  file_type: string;
  file_size_bytes: number;
  file_hash: string;
  storage_backend: string;
  storage_uri: string;
  row_count: number | null;
  column_count: number | null;
  sheet_count: number | null;
  status: string;
  created_at: string;
  updated_at: string;
};

export type DatasetSchema = {
  id: number;
  dataset_id: number;
  sheet_name: string;
  column_index: number;
  column_name: string;
  normalized_column_name: string;
  raw_data_type: string;
  semantic_type: string;
  nullable: boolean;
  missing_count: number;
  missing_rate: number;
  unique_count: number | null;
  unique_ratio: number | null;
  sample_values_json: unknown[] | null;
  min_value: string | null;
  max_value: string | null;
  sensitivity_tag: string;
  is_measure: boolean;
  is_dimension: boolean;
  is_time_column: boolean;
  is_identifier: boolean;
  description: string | null;
  created_at: string;
  updated_at: string;
};

export type DatasetDetail = Dataset & {
  schema: DatasetSchema[];
  preview_columns: string[];
  preview_rows: Record<string, unknown>[];
  preview_row_count: number;
};
