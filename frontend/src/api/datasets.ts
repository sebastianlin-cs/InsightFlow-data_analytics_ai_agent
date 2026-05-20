import { apiRequest } from "./client";
import type { Dataset, DatasetDetail } from "../types/dataset";

export function listDatasets(): Promise<Dataset[]> {
  return apiRequest<Dataset[]>("/api/datasets");
}

export function uploadDataset(file: File): Promise<Dataset> {
  const formData = new FormData();
  formData.append("file", file);
  return apiRequest<Dataset>("/api/datasets/upload", {
    method: "POST",
    body: formData,
  });
}

export function getDatasetDetail(datasetId: number): Promise<DatasetDetail> {
  return apiRequest<DatasetDetail>(`/api/datasets/${datasetId}`);
}

export function deleteDataset(datasetId: number): Promise<{ message: string }> {
  return apiRequest<{ message: string }>(`/api/datasets/${datasetId}`, {
    method: "DELETE",
  });
}
