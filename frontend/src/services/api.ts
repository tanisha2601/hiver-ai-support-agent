import axios from 'axios';
import type { AgentRequest, AgentResult, EvaluationSummary, FailureMode, HealthStatus } from '../types/api';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

export const getHealth = async (): Promise<HealthStatus> => {
  const response = await apiClient.get<HealthStatus>('/api/health');
  return response.data;
};

export const runAgent = async (request: AgentRequest): Promise<AgentResult> => {
  const response = await apiClient.post<AgentResult>('/api/agent/run', request);
  return response.data;
};

export const getEvaluationSummary = async (): Promise<EvaluationSummary> => {
  const response = await apiClient.get<EvaluationSummary>('/api/evaluation/summary');
  return response.data;
};

export const getFailures = async (): Promise<FailureMode[]> => {
  const response = await apiClient.get<FailureMode[]>('/api/evaluation/failures');
  return response.data;
};

export const getConversations = async (): Promise<any[]> => {
  const response = await apiClient.get<any[]>('/api/evaluation/conversations');
  return response.data;
};
