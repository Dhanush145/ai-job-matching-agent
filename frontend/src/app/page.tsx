
"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import {
  LayoutDashboard,
  BriefcaseBusiness,
  UserRound,
  Bot,
  Target,
  BookOpen,
  FileText,
  Settings,
  Bell,
  Search,
  MapPin,
  TrendingUp,
  Sparkles,
  Menu,
  RefreshCw,
  Building2,
  Wallet,
  Clock,
  GraduationCap,
  X,
  Send,
  UploadCloud,
  CheckCircle2,
} from "lucide-react";

import api, { uploadResume, type ResumeUploadResponse } from "@/lib/api";

type Job = {
  id: number;
  job_id: string;
  title: string;
  company: string;
  location: string;
  description: string;
  required_skills: string[];
  experience_required: number;
  employment_type: string;
  salary_min_lpa: number;
  salary_max_lpa: number;
};

type JobsResponse = {
  total: number;
  filters_applied?: Record<string, unknown>;
  jobs: Job[];
};

type JobRecommendation = {
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
};

type RecommendationResponse = {
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
};

type AgentChatResponse = {
  candidate_id: number;
  conversation_id: string;
  user_message: string;
  assistant_response: string;
};

type ChatMessage = {
  role: "user" | "assistant";
  content: string;
};

export default function Dashboard() {
  const [jobs, setJobs] = useState<Job[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedLocation, setSelectedLocation] = useState("All Locations");
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [candidateId, setCandidateId] = useState<number>(1);
  const [resumeFile, setResumeFile] = useState<File | null>(null);
  const [resumeUploading, setResumeUploading] = useState(false);
  const [resumeError, setResumeError] = useState("");
  const [resumeResult, setResumeResult] = useState<ResumeUploadResponse | null>(null);

  // AI recruitment agent chat
  const [chatInput, setChatInput] = useState("");
  const [chatMessages, setChatMessages] = useState<ChatMessage[]>([]);
  const [chatLoading, setChatLoading] = useState(false);
  const [chatError, setChatError] = useState("");
  const [conversationId, setConversationId] = useState("dashboard-test");
  const [chatHydrated, setChatHydrated] = useState(false);
  const chatEndRef = useRef<HTMLDivElement | null>(null);

  // Restore the chat transcript and conversation ID after a page reload.
  useEffect(() => {
    try {
      const savedConversationId = localStorage.getItem("jobpilot_conversation_id");
      const savedMessages = localStorage.getItem("jobpilot_chat_messages");

      if (savedConversationId) setConversationId(savedConversationId);
      if (savedMessages) {
        const parsedMessages = JSON.parse(savedMessages) as ChatMessage[];
        if (Array.isArray(parsedMessages)) setChatMessages(parsedMessages);
      }
    } catch (storageError) {
      console.error("Could not restore saved chat:", storageError);
    } finally {
      setChatHydrated(true);
    }
  }, []);

  // Keep the newest message visible as the conversation grows.
  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: "smooth", block: "end" });
  }, [chatMessages, chatLoading]);

  // Start a fresh conversation without deleting the backend's older checkpoint.
  const startNewConversation = () => {
    const nextId = `dashboard-${Date.now()}`;
    setConversationId(nextId);
    setChatMessages([]);
    setChatInput("");
    setChatError("");
  };

  // Save chat messages locally so the visible transcript survives reloads.
  useEffect(() => {
    if (!chatHydrated) return;

    try {
      localStorage.setItem("jobpilot_conversation_id", conversationId);
      localStorage.setItem("jobpilot_chat_messages", JSON.stringify(chatMessages));
    } catch (storageError) {
      console.error("Could not save chat:", storageError);
    }
  }, [chatMessages, conversationId, chatHydrated]);

  const sendChatMessage = async () => {
    const message = chatInput.trim();
    if (!message || chatLoading) return;

    setChatMessages((previous) => [...previous, { role: "user", content: message }]);
    setChatInput("");
    setChatLoading(true);
    setChatError("");

    try {
      const response = await api.post<AgentChatResponse>("/api/agent/chat", {
        candidate_id: candidateId,
        conversation_id: conversationId,
        message,
      });

      setChatMessages((previous) => [
        ...previous,
        { role: "assistant", content: response.data.assistant_response },
      ]);
    } catch (err) {
      console.error("AI agent chat failed:", err);
      setChatError("Unable to get a response from the AI agent. Check that the backend and Ollama are running.");
    } finally {
      setChatLoading(false);
    }
  };

  // Personalized recommendation state (candidate ID 1)
  const [recommendationData, setRecommendationData] =
    useState<RecommendationResponse | null>(null);
  const [recommendationsLoading, setRecommendationsLoading] = useState(true);
  const [recommendationsError, setRecommendationsError] = useState("");

  const fetchRecommendations = async (id: number = candidateId) => {
    // FastAPI validates this path parameter as an integer. Guard against
    // undefined, NaN, zero, or accidentally stored non-numeric values.
    if (!Number.isInteger(id) || id <= 0) {
      setRecommendationData(null);
      setRecommendationsError(`Invalid candidate ID: ${String(id)}. Upload a resume or select a valid candidate ID.`);
      setRecommendationsLoading(false);
      return;
    }

    try {
      setRecommendationsLoading(true);
      setRecommendationsError("");

      const response = await api.get<RecommendationResponse>(
        `/api/recommendations/${encodeURIComponent(String(id))}`
      );

      // Keep the displayed candidate in sync with the API response.
      if (response.data.candidate_id !== id) {
        console.warn(
          `Requested recommendations for candidate ${id}, but API returned candidate ${response.data.candidate_id}.`
        );
      }

      setRecommendationData(response.data);
    } catch (err: unknown) {
      const apiError = err as {
        message?: string;
        response?: {
          status?: number;
          data?: { detail?: unknown; message?: string };
        };
      };
      const status = apiError.response?.status;
      const detail = apiError.response?.data?.detail;
      const detailText = detail
        ? typeof detail === "string"
          ? detail
          : JSON.stringify(detail)
        : apiError.response?.data?.message || apiError.message || "Unknown error";

      console.error("Error fetching recommendations:", {
        candidateId: id,
        status,
        response: apiError.response?.data,
        message: apiError.message,
      });

      setRecommendationData(null);
      setRecommendationsError(
        `Could not load recommendations for candidate ${id}${status ? ` (HTTP ${status})` : ""}. ${detailText}`
      );
    } finally {
      setRecommendationsLoading(false);
    }
  };

  const handleResumeUpload = async () => {
    if (!resumeFile) {
      setResumeError("Please choose a PDF resume first.");
      return;
    }
    if (!resumeFile.name.toLowerCase().endsWith(".pdf")) {
      setResumeError("Please upload a PDF file.");
      return;
    }

    try {
      setResumeUploading(true);
      setResumeError("");
      setResumeResult(null);
      const result = await uploadResume(resumeFile);
      setResumeResult(result);
      setCandidateId(result.candidate_id);
      localStorage.setItem("jobpilot_candidate_id", String(result.candidate_id));
      setChatMessages([]);
      const nextConversationId = `candidate-${result.candidate_id}-${Date.now()}`;
      setConversationId(nextConversationId);
      localStorage.setItem("jobpilot_conversation_id", nextConversationId);
      localStorage.setItem("jobpilot_chat_messages", JSON.stringify([]));
      await fetchRecommendations(result.candidate_id);
    } catch (err) {
      console.error("Resume upload failed:", err);
      setResumeError("Resume upload failed. Check the backend, endpoint, and multipart field name.");
    } finally {
      setResumeUploading(false);
    }
  };

  const fetchJobs = async () => {
    try {
      setLoading(true);
      setError("");

      const response = await api.get<JobsResponse | Job[]>(
        "/api/jobs/"
      );

      const data = response.data;

      // Supports both { total, jobs: [...] } and [...] responses.
      const jobList = Array.isArray(data) ? data : data.jobs;

      setJobs(jobList);
    } catch (err) {
      console.error("Error fetching jobs:", err);
      setError(
        "Unable to load jobs. Please check whether your FastAPI backend is running."
      );
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchJobs();
    const storedCandidateId = localStorage.getItem("jobpilot_candidate_id");
    const parsedCandidateId = storedCandidateId ? Number(storedCandidateId) : 1;
    const initialCandidateId =
      Number.isInteger(parsedCandidateId) && parsedCandidateId > 0
        ? parsedCandidateId
        : 1;

    setCandidateId(initialCandidateId);
    void fetchRecommendations(initialCandidateId);
  }, []);

  const locations = useMemo(() => {
    return [
      "All Locations",
      ...Array.from(new Set(jobs.map((job) => job.location))),
    ];
  }, [jobs]);

  const filteredJobs = useMemo(() => {
    return jobs.filter((job) => {
      const query = searchQuery.toLowerCase();

      const matchesSearch =
        job.title.toLowerCase().includes(query) ||
        job.company.toLowerCase().includes(query) ||
        job.required_skills.some((skill) =>
          skill.toLowerCase().includes(query)
        );

      const matchesLocation =
        selectedLocation === "All Locations" ||
        job.location === selectedLocation;

      return matchesSearch && matchesLocation;
    });
  }, [jobs, searchQuery, selectedLocation]);

  const remoteJobs = jobs.filter(
    (job) => job.location.toLowerCase() === "remote"
  ).length;

  const averageSalary =
    jobs.length > 0
      ? (
          jobs.reduce(
            (sum, job) =>
              sum +
              (job.salary_min_lpa + job.salary_max_lpa) / 2,
            0
          ) / jobs.length
        ).toFixed(1)
      : "0";

  const navigation = [
    { name: "Dashboard", icon: LayoutDashboard, active: true },
    { name: "Find Jobs", icon: BriefcaseBusiness, active: false },
    { name: "Recommendations", icon: Target, active: false },
    { name: "AI Assistant", icon: Bot, active: false },
    { name: "Skill Gap Analysis", icon: TrendingUp, active: false },
    { name: "Learning Roadmap", icon: BookOpen, active: false },
    { name: "My Resume", icon: FileText, active: false },
    { name: "My Profile", icon: UserRound, active: false },
  ];

  return (
    <div className="min-h-screen bg-[#f8fafc] text-gray-900">

      {/* Mobile sidebar backdrop */}
      {sidebarOpen && (
        <div
          className="fixed inset-0 z-40 bg-black/40 lg:hidden"
          onClick={() => setSidebarOpen(false)}
        />
      )}

      {/* Sidebar */}
      <aside
        className={`fixed inset-y-0 left-0 z-50 flex w-64 flex-col border-r border-gray-200 bg-white transition-transform duration-300 lg:translate-x-0 ${
          sidebarOpen ? "translate-x-0" : "-translate-x-full"
        }`}
      >
        <div className="flex h-20 items-center justify-between border-b border-gray-100 px-6">
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-blue-600 text-white">
              <Sparkles size={22} />
            </div>
            <div>
              <h1 className="text-lg font-bold tracking-tight">
                JobPilot <span className="text-blue-600">AI</span>
              </h1>
              <p className="text-xs text-gray-500">
                Intelligent Career Platform
              </p>
            </div>
          </div>

          <button
            onClick={() => setSidebarOpen(false)}
            className="text-gray-500 lg:hidden"
          >
            <X size={20} />
          </button>
        </div>

        <div className="px-4 py-6">
          <p className="mb-4 px-3 text-xs font-semibold uppercase tracking-wider text-gray-400">
            Workspace
          </p>

          <nav className="space-y-1">
            {navigation.map((item) => {
              const Icon = item.icon;

              return (
                <button
                  key={item.name}
                  onClick={() => setSidebarOpen(false)}
                  className={`flex w-full items-center gap-3 rounded-xl px-3 py-3 text-sm font-medium transition ${
                    item.active
                      ? "bg-blue-50 text-blue-700"
                      : "text-gray-600 hover:bg-gray-50 hover:text-gray-900"
                  }`}
                >
                  <Icon size={19} />
                  {item.name}
                </button>
              );
            })}
          </nav>
        </div>

        <div className="mt-auto border-t border-gray-100 p-5">
          <div className="rounded-xl bg-gradient-to-br from-blue-600 to-indigo-700 p-4 text-white">
            <Sparkles size={20} />
            <h3 className="mt-3 font-semibold">
              AI Career Assistant
            </h3>
            <p className="mt-1 text-xs leading-relaxed text-blue-100">
              Find opportunities that match your skills and career goals.
            </p>
            <p className="mt-3 text-xs font-semibold">
              Powered by JobPilot AI
            </p>
          </div>

          <button className="mt-5 flex w-full items-center gap-3 px-2 text-sm text-gray-600">
            <Settings size={18} />
            Settings
          </button>
        </div>
      </aside>

      {/* Main content */}
      <main className="min-h-screen lg:ml-64">

        {/* Header */}
        <header className="sticky top-0 z-30 flex h-20 items-center justify-between border-b border-gray-200 bg-white/90 px-5 backdrop-blur-md md:px-8">
          <div className="flex items-center gap-3">
            <button
              onClick={() => setSidebarOpen(true)}
              className="rounded-lg p-2 hover:bg-gray-100 lg:hidden"
            >
              <Menu size={22} />
            </button>

            <div>
              <h2 className="text-lg font-bold md:text-xl">
                Dashboard
              </h2>
              <p className="hidden text-xs text-gray-500 sm:block">
                Your AI-powered career workspace
              </p>
            </div>
          </div>

          <div className="flex items-center gap-4">
            <button className="relative rounded-full p-2 text-gray-500 hover:bg-gray-100">
              <Bell size={20} />
              <span className="absolute right-2 top-2 h-2 w-2 rounded-full bg-red-500" />
            </button>

            <div className="flex items-center gap-3 border-l border-gray-200 pl-4">
              <div className="flex h-10 w-10 items-center justify-center rounded-full bg-blue-100 font-bold text-blue-700">
                D
              </div>
              <div className="hidden sm:block">
                <p className="text-sm font-semibold">Dhanush N</p>
                <p className="text-xs text-gray-500">
                  Candidate
                </p>
              </div>
            </div>
          </div>
        </header>

        {/* Dashboard body */}
        <div className="space-y-8 p-5 md:p-8">

          {/* Welcome section */}
          <section className="flex flex-col justify-between gap-5 md:flex-row md:items-center">
            <div>
              <p className="text-sm font-medium text-blue-600">
                YOUR CAREER OVERVIEW
              </p>
              <h1 className="mt-2 text-2xl font-bold tracking-tight md:text-3xl">
                Welcome back, Dhanush!
              </h1>
              <p className="mt-2 text-sm text-gray-500">
                Explore opportunities and discover your next career move.
              </p>
            </div>

            <button
              onClick={fetchJobs}
              disabled={loading}
              className="flex items-center justify-center gap-2 rounded-xl bg-blue-600 px-5 py-3 text-sm font-semibold text-white shadow-sm transition hover:bg-blue-700 disabled:opacity-60"
            >
              <RefreshCw
                size={17}
                className={loading ? "animate-spin" : ""}
              />
              Refresh Jobs
            </button>
          </section>

          {/* Statistics */}
          <section className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-4">

            <StatCard
              title="Available Jobs"
              value={jobs.length.toString()}
              subtitle="Jobs in database"
              icon={<BriefcaseBusiness size={21} />}
              color="blue"
            />

            <StatCard
              title="Remote Jobs"
              value={remoteJobs.toString()}
              subtitle="Remote opportunities"
              icon={<Building2 size={21} />}
              color="purple"
            />

            <StatCard
              title="Average Salary"
              value={`${averageSalary} LPA`}
              subtitle="Average listed salary midpoint"
              icon={<Wallet size={21} />}
              color="green"
            />

            <StatCard
              title="Locations"
              value={Math.max(locations.length - 1, 0).toString()}
              subtitle="Unique job locations"
              icon={<MapPin size={21} />}
              color="orange"
            />

          </section>

          {/* Resume upload and candidate profile */}
          <section className="space-y-5" id="resume-upload">
            <div>
              <p className="text-sm font-medium text-blue-600">CANDIDATE PROFILE</p>
              <h2 className="mt-1 text-xl font-bold">Resume & Profile</h2>
              <p className="mt-1 text-sm text-gray-500">
                Upload a PDF resume to extract candidate details and refresh personalized job recommendations.
              </p>
            </div>

            <div className="rounded-2xl border border-gray-200 bg-white p-5 shadow-sm">
              <div className="flex flex-col gap-4 sm:flex-row sm:items-center">
                <label className="flex min-h-12 flex-1 cursor-pointer items-center gap-3 rounded-xl border border-dashed border-gray-300 bg-gray-50 px-4 py-3 hover:border-blue-400 hover:bg-blue-50/50">
                  <UploadCloud className="shrink-0 text-blue-600" size={22} />
                  <span className="min-w-0">
                    <span className="block truncate text-sm font-semibold text-gray-800">
                      {resumeFile ? resumeFile.name : "Choose your resume (PDF)"}
                    </span>
                    <span className="block text-xs text-gray-500">PDF format</span>
                  </span>
                  <input
                    type="file"
                    accept="application/pdf,.pdf"
                    className="hidden"
                    onChange={(event) => {
                      setResumeFile(event.target.files?.[0] ?? null);
                      setResumeError("");
                    }}
                  />
                </label>
                <button
                  type="button"
                  onClick={() => void handleResumeUpload()}
                  disabled={!resumeFile || resumeUploading}
                  className="flex items-center justify-center gap-2 rounded-xl bg-blue-600 px-5 py-3 text-sm font-semibold text-white hover:bg-blue-700 disabled:cursor-not-allowed disabled:opacity-50"
                >
                  {resumeUploading ? <RefreshCw size={17} className="animate-spin" /> : <UploadCloud size={17} />}
                  {resumeUploading ? "Processing resume..." : "Upload & Analyze"}
                </button>
              </div>
              {resumeError && <p className="mt-3 text-sm text-red-600">{resumeError}</p>}
            </div>

            {resumeResult && (
              <div className="overflow-hidden rounded-2xl border border-gray-200 bg-white shadow-sm">
                <div className="flex flex-col gap-3 border-b border-gray-100 bg-gradient-to-r from-blue-50 to-indigo-50 p-5 sm:flex-row sm:items-center sm:justify-between">
                  <div>
                    <div className="flex items-center gap-2 text-sm font-semibold text-green-700">
                      <CheckCircle2 size={18} /> {resumeResult.message}
                    </div>
                    <h3 className="mt-2 text-xl font-bold text-gray-900">{resumeResult.profile.name || "Candidate profile"}</h3>
                    <p className="mt-1 text-sm text-gray-600">Candidate ID: {resumeResult.candidate_id}</p>
                  </div>
                  <div className="rounded-xl bg-white px-4 py-3 text-center shadow-sm">
                    <p className="text-2xl font-bold text-blue-700">{resumeResult.profile.skills.length}</p>
                    <p className="text-xs text-gray-500">Skills extracted</p>
                  </div>
                </div>

                <div className="grid gap-5 p-5 md:grid-cols-2">
                  <div className="space-y-3">
                    <h4 className="font-semibold text-gray-900">Contact & Career Details</h4>
                    <div className="grid gap-3 text-sm sm:grid-cols-2">
                      <div><p className="text-xs text-gray-500">Email</p><p className="mt-1 break-all font-medium text-gray-800">{resumeResult.profile.email || "Not extracted"}</p></div>
                      <div><p className="text-xs text-gray-500">Phone</p><p className="mt-1 font-medium text-gray-800">{resumeResult.profile.phone || "Not extracted"}</p></div>
                      <div><p className="text-xs text-gray-500">Experience</p><p className="mt-1 font-medium text-gray-800">{resumeResult.profile.experience_years} years</p></div>
                      <div><p className="text-xs text-gray-500">Preferred roles</p><p className="mt-1 font-medium text-gray-800">{resumeResult.profile.preferred_roles?.join(", ") || "Not specified"}</p></div>
                      <div className="sm:col-span-2"><p className="text-xs text-gray-500">Preferred locations</p><p className="mt-1 font-medium text-gray-800">{resumeResult.profile.preferred_locations?.join(", ") || "Not specified"}</p></div>
                    </div>
                  </div>

                  <div className="space-y-3">
                    <h4 className="font-semibold text-gray-900">Education</h4>
                    {resumeResult.profile.education?.length ? (
                      resumeResult.profile.education.map((education, index) => (
                        <div key={`${education.institution}-${index}`} className="rounded-xl border border-gray-100 bg-gray-50 p-3 text-sm">
                          <p className="font-semibold text-gray-900">{education.degree || "Degree not specified"}</p>
                          <p className="mt-1 text-gray-600">{education.institution || "Institution not specified"}</p>
                          <p className="mt-1 text-xs text-gray-500">{education.field_of_study || ""}{education.graduation_year ? ` · Graduation ${education.graduation_year}` : ""}{education.cgpa ? ` · CGPA ${education.cgpa}` : ""}</p>
                        </div>
                      ))
                    ) : (
                      <p className="text-sm text-gray-500">No education details were extracted.</p>
                    )}
                  </div>
                </div>

                <div className="border-t border-gray-100 p-5">
                  <h4 className="mb-3 font-semibold text-gray-900">Extracted Skills</h4>
                  <div className="flex flex-wrap gap-2">
                    {resumeResult.profile.skills.map((skill) => (
                      <span key={skill} className="rounded-lg bg-blue-50 px-3 py-1.5 text-xs font-medium text-blue-700">{skill}</span>
                    ))}
                  </div>
                </div>
                <div className="border-t border-gray-100 bg-green-50/60 px-5 py-3 text-xs text-green-800">
                  Recommendations have been refreshed for candidate #{resumeResult.candidate_id}.
                </div>
              </div>
            )}

            <p className="text-xs text-gray-500">Current active candidate ID: {candidateId}. Uploading another resume creates/activates the candidate returned by the backend.</p>
          </section>

          {/* Personalized recommendations */}
          <section className="space-y-5">
            <div className="flex flex-col justify-between gap-3 sm:flex-row sm:items-end">
              <div>
                <p className="text-sm font-medium text-blue-600">
                  AI-POWERED MATCHING
                </p>
                <h2 className="mt-1 text-xl font-bold">
                  Personalized Job Recommendations
                </h2>
                <p className="mt-1 text-sm text-gray-500">
                  Jobs ranked using semantic similarity, skills, experience and location.
                </p>
              </div>

              <button
                onClick={fetchRecommendations}
                disabled={recommendationsLoading}
                className="flex items-center justify-center gap-2 rounded-xl border border-gray-200 bg-white px-4 py-2.5 text-sm font-semibold text-gray-700 transition hover:bg-gray-50 disabled:opacity-60"
              >
                <RefreshCw
                  size={16}
                  className={recommendationsLoading ? "animate-spin" : ""}
                />
                Refresh Recommendations
              </button>
            </div>

            {recommendationData && (
              <div className="grid grid-cols-2 gap-3 rounded-2xl border border-blue-100 bg-blue-50/70 p-4 sm:grid-cols-4">
                <div>
                  <p className="text-xs text-gray-500">Candidate</p>
                  <p className="mt-1 font-semibold text-gray-900">
                    {recommendationData.candidate_name}
                  </p>
                </div>
                <div>
                  <p className="text-xs text-gray-500">Ranking method</p>
                  <p className="mt-1 font-semibold text-gray-900">
                    {recommendationData.ranking_method}
                  </p>
                </div>
                <div>
                  <p className="text-xs text-gray-500">Recommendations</p>
                  <p className="mt-1 font-semibold text-gray-900">
                    {recommendationData.total_recommendations}
                  </p>
                </div>
                <div>
                  <p className="text-xs text-gray-500">Candidate ID</p>
                  <p className="mt-1 font-semibold text-gray-900">
                    {recommendationData.candidate_id}
                  </p>
                </div>
              </div>
            )}

            {recommendationsLoading && (
              <div className="rounded-2xl border border-gray-200 bg-white p-8 text-center">
                <RefreshCw size={26} className="mx-auto animate-spin text-blue-600" />
                <p className="mt-3 text-sm font-medium text-gray-700">
                  Finding your best job matches...
                </p>
              </div>
            )}

            {!recommendationsLoading && recommendationsError && (
              <div className="rounded-2xl border border-red-200 bg-red-50 p-5">
                <p className="font-semibold text-red-700">
                  Recommendations unavailable
                </p>
                <p className="mt-1 break-words text-sm text-red-600">
                  {recommendationsError}
                </p>
                <button
                  onClick={fetchRecommendations}
                  className="mt-3 rounded-lg bg-red-600 px-4 py-2 text-sm font-semibold text-white hover:bg-red-700"
                >
                  Try Again
                </button>
              </div>
            )}

            {!recommendationsLoading &&
              !recommendationsError &&
              recommendationData &&
              recommendationData.recommendations.length > 0 && (
                <div className="grid grid-cols-1 gap-5 xl:grid-cols-2">
                  {recommendationData.recommendations.map((job) => (
                    <RecommendationCard key={job.job_id} job={job} />
                  ))}
                </div>
              )}

            {!recommendationsLoading &&
              !recommendationsError &&
              recommendationData?.recommendations.length === 0 && (
                <div className="rounded-2xl border border-gray-200 bg-white p-8 text-center text-sm text-gray-500">
                  No personalized recommendations are available yet.
                </div>
              )}
          </section>

          {/* AI recruitment assistant */}
          <section className="space-y-5" id="ai-assistant">
            <div>
              <p className="text-sm font-medium text-blue-600">LANGGRAPH POWERED</p>
              <h2 className="mt-1 text-xl font-bold">AI Career Assistant</h2>
              <p className="mt-1 text-sm text-gray-500">
                Ask your recruitment agent to find jobs, explain matches, or explore career opportunities.
              </p>
            </div>

            <div className="overflow-hidden rounded-2xl border border-gray-200 bg-white shadow-sm">
              <div className="flex items-center gap-3 border-b border-gray-100 bg-gray-50 px-5 py-4">
                <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-blue-600 text-white">
                  <Bot size={21} />
                </div>
                <div>
                  <p className="font-semibold text-gray-900">JobPilot AI Agent</p>
                  <p className="text-xs text-gray-500">Candidate #{candidateId} · Conversation: {conversationId}</p>
                </div>
                <div className="ml-auto flex items-center gap-2">
                  <span className="hidden rounded-full bg-green-50 px-3 py-1 text-xs font-semibold text-green-700 sm:inline">Connected UI</span>
                  <button
                    type="button"
                    onClick={startNewConversation}
                    disabled={chatLoading}
                    className="rounded-lg border border-gray-200 bg-white px-3 py-2 text-xs font-semibold text-gray-700 hover:bg-gray-100 disabled:opacity-50"
                  >
                    New chat
                  </button>
                </div>
              </div>

              <div className="max-h-[460px] min-h-[180px] space-y-4 overflow-y-auto p-5">
                {chatMessages.length === 0 && (
                  <div className="rounded-xl border border-dashed border-gray-200 bg-gray-50 p-6 text-center">
                    <Sparkles className="mx-auto text-blue-600" size={25} />
                    <p className="mt-3 font-semibold text-gray-800">How can I help with your job search?</p>
                    <p className="mt-1 text-sm text-gray-500">Try: “Find the best AI and LLM engineering jobs for my profile.”</p>
                    <button
                      type="button"
                      onClick={() => setChatInput("Find the best AI and LLM engineering jobs for my profile")}
                      className="mt-4 rounded-lg border border-blue-200 bg-white px-3 py-2 text-xs font-semibold text-blue-700 hover:bg-blue-50"
                    >
                      Use example question
                    </button>
                  </div>
                )}

                {chatMessages.map((message, index) => (
                  <div key={`${message.role}-${index}`} className={`flex ${message.role === "user" ? "justify-end" : "justify-start"}`}>
                    <div className={`max-w-[90%] whitespace-pre-wrap rounded-2xl px-4 py-3 text-sm leading-relaxed ${message.role === "user" ? "bg-blue-600 text-white" : "border border-gray-200 bg-gray-50 text-gray-800"}`}>
                      {message.content}
                    </div>
                  </div>
                ))}

                {chatLoading && (
                  <div className="flex justify-start">
                    <div className="rounded-2xl border border-gray-200 bg-gray-50 px-4 py-3 text-sm text-gray-500">
                      AI agent is thinking...
                    </div>
                  </div>
                )}
                <div ref={chatEndRef} />
              </div>

              {chatError && <p className="px-5 pb-2 text-sm text-red-600">{chatError}</p>}

              <form
                className="flex gap-2 border-t border-gray-100 p-4"
                onSubmit={(event) => { event.preventDefault(); void sendChatMessage(); }}
              >
                <input
                  value={chatInput}
                  onChange={(event) => setChatInput(event.target.value)}
                  placeholder="Ask your AI career assistant..."
                  className="min-w-0 flex-1 rounded-xl border border-gray-200 bg-gray-50 px-4 py-3 text-sm outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-100"
                  disabled={chatLoading}
                />
                <button
                  type="submit"
                  disabled={!chatInput.trim() || chatLoading}
                  className="flex items-center gap-2 rounded-xl bg-blue-600 px-4 py-3 text-sm font-semibold text-white hover:bg-blue-700 disabled:cursor-not-allowed disabled:opacity-50"
                >
                  <Send size={16} />
                  <span className="hidden sm:inline">Send</span>
                </button>
              </form>
            </div>
          </section>

          {/* Job listings */}
          <section className="space-y-5">

            <div className="flex flex-col justify-between gap-3 sm:flex-row sm:items-end">
              <div>
                <h2 className="text-xl font-bold">
                  Explore Available Jobs
                </h2>
                <p className="mt-1 text-sm text-gray-500">
                  Opportunities retrieved directly from your FastAPI backend.
                </p>
              </div>

              <span className="text-sm font-medium text-gray-500">
                Showing {filteredJobs.length} of {jobs.length} jobs
              </span>
            </div>

            {/* Search and filters */}
            <div className="flex flex-col gap-3 rounded-2xl border border-gray-200 bg-white p-4 md:flex-row">
              <div className="relative flex-1">
                <Search
                  className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400"
                  size={19}
                />
                <input
                  type="text"
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  placeholder="Search job title, company or skills..."
                  className="w-full rounded-xl border border-gray-200 bg-gray-50 py-3 pl-10 pr-4 text-sm outline-none transition focus:border-blue-500 focus:ring-2 focus:ring-blue-100"
                />
              </div>

              <select
                value={selectedLocation}
                onChange={(e) => setSelectedLocation(e.target.value)}
                className="rounded-xl border border-gray-200 bg-gray-50 px-4 py-3 text-sm outline-none focus:border-blue-500"
              >
                {locations.map((location) => (
                  <option key={location} value={location}>
                    {location}
                  </option>
                ))}
              </select>
            </div>

            {/* Loading */}
            {loading && (
              <div className="rounded-2xl border border-gray-200 bg-white p-12 text-center">
                <RefreshCw
                  size={30}
                  className="mx-auto animate-spin text-blue-600"
                />
                <p className="mt-4 font-medium">
                  Loading available jobs...
                </p>
                <p className="mt-1 text-sm text-gray-500">
                  Connecting to your backend
                </p>
              </div>
            )}

            {/* Error */}
            {!loading && error && (
              <div className="rounded-2xl border border-red-200 bg-red-50 p-6 text-center">
                <p className="font-semibold text-red-700">
                  Something went wrong
                </p>
                <p className="mt-2 text-sm text-red-600">
                  {error}
                </p>
                <button
                  onClick={fetchJobs}
                  className="mt-4 rounded-lg bg-red-600 px-4 py-2 text-sm font-semibold text-white hover:bg-red-700"
                >
                  Try Again
                </button>
              </div>
            )}

            {/* Job cards */}
            {!loading && !error && filteredJobs.length > 0 && (
              <div className="grid grid-cols-1 gap-5 xl:grid-cols-2">
                {filteredJobs.map((job) => (
                  <JobCard key={job.job_id} job={job} />
                ))}
              </div>
            )}

            {/* No jobs */}
            {!loading && !error && filteredJobs.length === 0 && (
              <div className="rounded-2xl border border-gray-200 bg-white p-12 text-center">
                <BriefcaseBusiness
                  size={36}
                  className="mx-auto text-gray-300"
                />
                <h3 className="mt-4 font-semibold">
                  No jobs found
                </h3>
                <p className="mt-2 text-sm text-gray-500">
                  Try changing your search or location filter.
                </p>
                <button
                  onClick={() => {
                    setSearchQuery("");
                    setSelectedLocation("All Locations");
                  }}
                  className="mt-4 text-sm font-semibold text-blue-600 hover:underline"
                >
                  Clear filters
                </button>
              </div>
            )}
          </section>

          {/* Project information */}
          <section className="rounded-2xl border border-blue-100 bg-gradient-to-r from-blue-50 to-indigo-50 p-6">
            <div className="flex flex-col gap-4 md:flex-row md:items-center">
              <div className="flex h-12 w-12 shrink-0 items-center justify-center rounded-xl bg-blue-600 text-white">
                <Sparkles size={24} />
              </div>

              <div>
                <h3 className="font-bold text-gray-900">
                  Your AI Recruitment Agent
                </h3>
                <p className="mt-1 text-sm leading-relaxed text-gray-600">
                  JobPilot AI combines semantic job retrieval, hybrid
                  ranking, skill-gap analysis and personalized learning
                  recommendations to help candidates find relevant jobs.
                </p>
              </div>
            </div>
          </section>

          <footer className="border-t border-gray-200 pt-5 text-center text-xs text-gray-400">
            JobPilot AI © 2026. AI-Powered Job Matching & Recommendation Platform.
          </footer>

        </div>
      </main>
    </div>
  );
}

/* Personalized recommendation card */

function RecommendationCard({ job }: { job: JobRecommendation }) {
  const scoreColor =
    job.match_score >= 70
      ? "text-green-700 bg-green-50"
      : job.match_score >= 50
      ? "text-blue-700 bg-blue-50"
      : "text-orange-700 bg-orange-50";

  const scoreItems = [
    { label: "Semantic", value: job.score_breakdown.semantic_similarity },
    { label: "Skills", value: job.score_breakdown.skill_matching },
    { label: "Experience", value: job.score_breakdown.experience_matching },
    { label: "Location", value: job.score_breakdown.location_matching },
  ];

  return (
    <article className="rounded-2xl border border-gray-200 bg-white p-5 shadow-sm transition hover:-translate-y-1 hover:border-blue-200 hover:shadow-md">
      <div className="flex items-start justify-between gap-3">
        <div className="flex items-start gap-3">
          <div className="flex h-12 w-12 shrink-0 items-center justify-center rounded-xl bg-blue-50 text-blue-600">
            <Target size={23} />
          </div>
          <div>
            <div className="flex flex-wrap items-center gap-2">
              <h3 className="font-bold text-gray-900">{job.title}</h3>
              <span className="rounded-full bg-gray-100 px-2.5 py-1 text-xs font-semibold text-gray-600">
                Rank #{job.rank}
              </span>
            </div>
            <p className="mt-1 text-sm text-gray-500">{job.company}</p>
          </div>
        </div>

        <div className={`shrink-0 rounded-xl px-3 py-2 text-right ${scoreColor}`}>
          <p className="text-xl font-bold">{job.match_score.toFixed(2)}%</p>
          <p className="text-[10px] font-semibold uppercase tracking-wide">
            Match
          </p>
        </div>
      </div>

      <p className="mt-4 line-clamp-2 text-sm leading-relaxed text-gray-600">
        {job.description}
      </p>

      <div className="mt-4 grid grid-cols-2 gap-3 text-sm text-gray-600">
        <div className="flex items-center gap-2">
          <MapPin size={15} className="text-gray-400" />
          {job.location}
        </div>
        <div className="flex items-center gap-2">
          <Clock size={15} className="text-gray-400" />
          {job.experience_required} years experience
        </div>
      </div>

      <div className="mt-5">
        <div className="mb-2 flex items-center justify-between">
          <p className="text-xs font-semibold uppercase tracking-wide text-gray-400">
            Match score breakdown
          </p>
          <p className="text-xs text-gray-400">Percentage</p>
        </div>
        <div className="grid grid-cols-2 gap-3">
          {scoreItems.map((item) => (
            <div key={item.label}>
              <div className="mb-1 flex justify-between text-xs">
                <span className="text-gray-500">{item.label}</span>
                <span className="font-semibold text-gray-700">
                  {item.value.toFixed(1)}%
                </span>
              </div>
              <div className="h-2 overflow-hidden rounded-full bg-gray-100">
                <div
                  className="h-full rounded-full bg-blue-600"
                  style={{
                    width: `${Math.min(100, Math.max(0, item.value))}%`,
                  }}
                />
              </div>
            </div>
          ))}
        </div>
      </div>

      <div className="mt-5 border-t border-gray-100 pt-4">
        <p className="mb-2 text-xs font-semibold uppercase tracking-wide text-gray-400">
          Matched Skills
        </p>
        <div className="flex flex-wrap gap-2">
          {job.matched_skills.length > 0 ? (
            job.matched_skills.map((skill) => (
              <span
                key={skill}
                className="rounded-lg bg-green-50 px-2.5 py-1.5 text-xs font-medium text-green-700"
              >
                {skill}
              </span>
            ))
          ) : (
            <span className="text-xs text-gray-400">No matched skills listed</span>
          )}
        </div>

        {job.missing_skills.length > 0 && (
          <>
            <p className="mb-2 mt-4 text-xs font-semibold uppercase tracking-wide text-gray-400">
              Skills to Improve
            </p>
            <div className="flex flex-wrap gap-2">
              {job.missing_skills.map((skill) => (
                <span
                  key={skill}
                  className="rounded-lg bg-orange-50 px-2.5 py-1.5 text-xs font-medium text-orange-700"
                >
                  {skill}
                </span>
              ))}
            </div>
          </>
        )}
      </div>

      {job.explanation.length > 0 && (
        <div className="mt-4 rounded-xl bg-gray-50 p-3">
          <p className="mb-1 text-xs font-semibold text-gray-500">
            Why this job matches
          </p>
          <ul className="space-y-1">
            {job.explanation.map((reason, index) => (
              <li key={index} className="text-xs leading-relaxed text-gray-600">
                • {reason}
              </li>
            ))}
          </ul>
        </div>
      )}
    </article>
  );
}

/* Statistics card */

function StatCard({
  title,
  value,
  subtitle,
  icon,
  color,
}: {
  title: string;
  value: string;
  subtitle: string;
  icon: React.ReactNode;
  color: "blue" | "purple" | "green" | "orange";
}) {
  const colors = {
    blue: "bg-blue-50 text-blue-600",
    purple: "bg-purple-50 text-purple-600",
    green: "bg-green-50 text-green-600",
    orange: "bg-orange-50 text-orange-600",
  };

  return (
    <div className="rounded-2xl border border-gray-200 bg-white p-5 shadow-sm transition hover:-translate-y-1 hover:shadow-md">
      <div className="flex items-center justify-between">
        <p className="text-sm font-medium text-gray-500">
          {title}
        </p>
        <div className={`rounded-xl p-3 ${colors[color]}`}>
          {icon}
        </div>
      </div>

      <h3 className="mt-4 text-2xl font-bold">
        {value}
      </h3>

      <p className="mt-1 text-xs text-gray-500">
        {subtitle}
      </p>
    </div>
  );
}

/* Individual job card */

function JobCard({ job }: { job: Job }) {
  return (
    <article className="rounded-2xl border border-gray-200 bg-white p-5 shadow-sm transition hover:-translate-y-1 hover:border-blue-200 hover:shadow-md">

      <div className="flex items-start justify-between gap-3">
        <div className="flex items-start gap-3">
          <div className="flex h-12 w-12 shrink-0 items-center justify-center rounded-xl bg-blue-50 text-blue-600">
            <BriefcaseBusiness size={23} />
          </div>

          <div>
            <h3 className="font-bold text-gray-900">
              {job.title}
            </h3>
            <p className="mt-1 text-sm text-gray-500">
              {job.company}
            </p>
          </div>
        </div>

        <span className="rounded-full bg-green-50 px-3 py-1 text-xs font-semibold text-green-700">
          {job.employment_type}
        </span>
      </div>

      <p className="mt-4 line-clamp-2 text-sm leading-relaxed text-gray-600">
        {job.description}
      </p>

      <div className="mt-5 grid grid-cols-1 gap-3 sm:grid-cols-2">
        <div className="flex items-center gap-2 text-sm text-gray-600">
          <MapPin size={16} className="shrink-0 text-gray-400" />
          {job.location}
        </div>

        <div className="flex items-center gap-2 text-sm text-gray-600">
          <Wallet size={16} className="shrink-0 text-gray-400" />
          {job.salary_min_lpa}–{job.salary_max_lpa} LPA
        </div>

        <div className="flex items-center gap-2 text-sm text-gray-600">
          <Clock size={16} className="shrink-0 text-gray-400" />
          {job.experience_required} years experience
        </div>

        <div className="flex items-center gap-2 text-sm text-gray-600">
          <GraduationCap size={16} className="shrink-0 text-gray-400" />
          {job.job_id}
        </div>
      </div>

      <div className="mt-5 border-t border-gray-100 pt-4">
        <p className="mb-3 text-xs font-semibold uppercase tracking-wide text-gray-400">
          Required Skills
        </p>

        <div className="flex flex-wrap gap-2">
          {job.required_skills.map((skill) => (
            <span
              key={skill}
              className="rounded-lg bg-gray-100 px-3 py-1.5 text-xs font-medium text-gray-700"
            >
              {skill}
            </span>
          ))}
        </div>
      </div>

    </article>
  );
}
