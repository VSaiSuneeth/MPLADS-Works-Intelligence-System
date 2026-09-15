import axios from 'axios';
import { SimulationRequest, SimulationResponse, SimulationProjectItem } from '../types';

export const apiClient = axios.create({
  baseURL: '/api/v1',
  headers: {
    'Content-Type': 'application/json',
  },
});

// Intercept requests to attach Bearer token
apiClient.interceptors.request.use((config) => {
  const token = localStorage.getItem('mplads_auth_token');
  if (token && config.headers) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Handle global auth failures
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response && error.response.status === 401) {
      localStorage.removeItem('mplads_auth_token');
      localStorage.removeItem('mplads_auth_user');
    }
    return Promise.reject(error);
  }
);

// Simulation API Methods
export const runSimulationApi = (req: SimulationRequest) =>
  apiClient.post<SimulationResponse>('/simulation/run', req);

export const getSimulationBaseProjectApi = (workId: string) =>
  apiClient.get<SimulationProjectItem>(`/simulation/base-project/${workId}`);

export const listSimulationProjectsApi = () =>
  apiClient.get<{ items: SimulationProjectItem[]; total: number }>('/simulation/projects');

// Evidence & Photo Fraud API Methods
export const uploadEvidenceApi = (workId: string, file: File, evidenceType: string = 'PHOTOGRAPH') => {
  const formData = new FormData();
  formData.append('file', file);
  return apiClient.post(`/works/${workId}/evidence?evidenceType=${encodeURIComponent(evidenceType)}`, formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  });
};

export const getWorkEvidenceApi = (workId: string) =>
  apiClient.get(`/works/${workId}/evidence`);

export const getAllEvidenceFraudFlagsApi = () =>
  apiClient.get('/evidence/fraud-flags');
