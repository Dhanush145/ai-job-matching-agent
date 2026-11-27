
import axios from "axios";

// Backend API configuration
const api = axios.create({
  baseURL: "http://127.0.0.1:8000",
  headers: {
    "Content-Type": "application/json",
  },
});

// --------------------------------------
// JOB INTERFACE
// --------------------------------------

export interface Job {
  id: number;
  job_id: string;
  title: string;
  company: string;
  location: string;
  description: string;
  required_skills: string[];
  experience_required: number;
  employment_type: string;
  salary_min_lpa: number | null;
  salary_max_lpa: number | null;
}

// --------------------------------------
// RECOMMENDATION INTERFACES
// --------------------------------------

export interface JobRecommendation {
  job_id: string;
  title: string;
  company: string;
  location: string;
  description: string;
  required_skills: string[];
  experience_required: number;
  employment_type: string;

  similarity_score: number;
  match_score: number;

  score_breakdown: {
    semantic_similarity: number;
    skill_matching: number;
    experience_matching: number;
    location_matching: number;
  };

  matched_skills: string[];
  missing_skills: string[];
  explanation: string[];
  rank: number;
}

export interface RecommendationResponse {
  candidate_id: number;
  candidate_name: string;
  ranking_method: string;

  ranking_weights: {
    semantic_similarity: number;
    skill_matching: number;
    experience_matching: number;
    location_matching: number;
  };

  total_recommendations: number;
  recommendations: JobRecommendation[];
}

// --------------------------------------
// API FUNCTIONS
// --------------------------------------

/**
 * Fetch all jobs from the backend.
 */
export const getJobs = async (): Promise<Job[]> => {
  const response = await api.get("/api/jobs/");

  // Supports both a direct array and { jobs: [...] }
  const data = response.data;

  return Array.isArray(data) ? data : data.jobs ?? [];
};

/**
 * Fetch personalized job recommendations
 * for a particular candidate.
 */
export const getRecommendations = async (
  candidateId: number
): Promise<RecommendationResponse> => {
  const response = await api.get(
    `/api/recommendations/${candidateId}`
  );

  return response.data;
};

// --------------------------------------
// EXPORT AXIOS INSTANCE
// --------------------------------------

export default api;
