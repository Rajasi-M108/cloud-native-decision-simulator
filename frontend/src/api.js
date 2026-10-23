import axios from "axios";

const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";
const ID_TOKEN = import.meta.env.VITE_ID_TOKEN;

const client = axios.create({ baseURL: API_URL });

client.interceptors.request.use((config) => {
  if (ID_TOKEN) config.headers.Authorization = `Bearer ${ID_TOKEN}`;
  return config;
});

export const getSummary = () => client.get("/api/summary").then((r) => r.data);
export const getRegional = () => client.get("/api/regional").then((r) => r.data);
export const getCategories = () => client.get("/api/categories").then((r) => r.data);
export const getModelComparison = () => client.get("/api/models/comparison").then((r) => r.data);
export const getAnomalySummary = () => client.get("/api/anomalies/summary").then((r) => r.data);
export const getTopAnomalies = () => client.get("/api/anomalies/top").then((r) => r.data);
export const getGlobalExplanations = () => client.get("/api/explain/global").then((r) => r.data);
export const getSampleExplanations = () => client.get("/api/explain/samples").then((r) => r.data);
export const predictScenario = (payload) => client.post("/api/predict", payload).then((r) => r.data);

export const getBenchmarkGlobal = () => client.get("/api/benchmark/global").then((r) => r.data);
export const getBenchmarkCategories = () => client.get("/api/benchmark/categories").then((r) => r.data);
