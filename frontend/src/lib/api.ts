import axios from "axios";

// FastAPI backend client
const api = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_BASE_URL || "http://127.0.0.1:8000",
  headers: {
    "Content-Type": "application/json",
  },
});

// --------------------------------------
// JOB TYPES
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
// RESUME UPLOAD TYPES
// --------------------------------------
export interface EducationEntry {
  institution: string;
  degree: string;
  field_of_study: string;
  graduation_year: string;
  cgpa: string;
}

export interface CandidateProfile {
  name: string;
  email: string;
  phone: string;
  education: EducationEntry[];
  skills: string[];
  experience_years: number;
  preferred_roles: string[];
  preferred_locations: string[];
}

export interface ResumeUploadResponse {
  message: string;
  candidate_id: number;
  profile: CandidateProfile;
}

/** Upload a PDF resume to POST /api/resume/upload. */
export const uploadResume = async (
  file: File
): Promise<ResumeUploadResponse> => {
  const formData = new FormData();
  // Swagger's upload field is expected to be named "file".
  formData.append("file", file);

  const response = await api.post<ResumeUploadResponse>(
    "/api/resume/upload",
    formData,
    { headers: { "Content-Type": "multipart/form-data" } }
  );
  return response.data;
};

// --------------------------------------
// RECOMMENDATION TYPES
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

export const getRecommendations = async (
  candidateId: number
): Promise<RecommendationResponse> => {
  const response = await api.get<RecommendationResponse>(
    `/api/recommendations/${candidateId}`
  );
  return response.data;
};

export default api;
