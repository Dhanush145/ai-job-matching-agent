
"use client";

import { useEffect, useMemo, useState } from "react";
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
} from "lucide-react";

import api from "@/lib/api";

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

export default function Dashboard() {
  const [jobs, setJobs] = useState<Job[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedLocation, setSelectedLocation] = useState("All Locations");
  const [sidebarOpen, setSidebarOpen] = useState(false);

  // Personalized recommendation state (candidate ID 1)
  const [recommendationData, setRecommendationData] =
    useState<RecommendationResponse | null>(null);
  const [recommendationsLoading, setRecommendationsLoading] = useState(true);
  const [recommendationsError, setRecommendationsError] = useState("");

  const fetchRecommendations = async () => {
    try {
      setRecommendationsLoading(true);
      setRecommendationsError("");

      const response = await api.get<RecommendationResponse>(
        "/api/recommendations/1"
      );

      setRecommendationData(response.data);
    } catch (err) {
      console.error("Error fetching recommendations:", err);
      setRecommendationsError(
        "Unable to load personalized recommendations. Check the recommendations API and candidate ID."
      );
    } finally {
      setRecommendationsLoading(false);
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
    fetchRecommendations();
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
                <p className="mt-1 text-sm text-red-600">
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
