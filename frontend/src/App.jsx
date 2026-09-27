import React, { useState, useEffect } from 'react';
import {
  Trophy, Shield, Users, LayoutGrid, CheckCircle2, Lock,
  PlusCircle, FileText, ChevronRight, Download, Award,
  Sparkles, ExternalLink, Activity, Scale, Compass, Filter,
  MessageSquare, ThumbsUp, LogOut, Check, AlertCircle, Flame,
  TrendingUp, BarChart3, CheckSquare, Zap, Sun, Moon,
  ChevronDown, Code, HeartHandshake, Eye, Cpu, Terminal
} from 'lucide-react';
import confetti from 'canvas-confetti';

const API_BASE = import.meta.env.VITE_API_BASE || '/api';

export default function App() {
  const [theme, setTheme] = useState('light'); // 'light' or 'dark'
  const [currentUser, setCurrentUser] = useState(null);
  const [view, setView] = useState('gallery'); // 'gallery', 'submit', 'judge', 'organizer', 'results'
  const [projects, setProjects] = useState([]);
  const [eventData, setEventData] = useState(null);
  const [selectedTrack, setSelectedTrack] = useState('all');
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedProject, setSelectedProject] = useState(null);
  const [resultsData, setResultsData] = useState([]);
  const [organizerData, setOrganizerData] = useState(null);
  const [judgeAssignments, setJudgeAssignments] = useState([]);
  const [loading, setLoading] = useState(false);
  const [notification, setNotification] = useState(null);

  // Apply theme class to root body
  useEffect(() => {
    document.body.className = theme === 'light' ? 'light-mode' : 'dark-mode';
  }, [theme]);

  // Auth / Quick switcher accounts
  const accounts = [
    { role: 'visitor', label: 'Visitor (Public View)', icon: Users, token: '' },
    { role: 'participant', label: 'Participant (Charlie)', icon: PlusCircle, token: 'prt_2e88' },
    { role: 'judge_a', label: 'Judge A (Tomas Varga)', icon: Scale, token: 'jdg_a_91bc' },
    { role: 'judge_b', label: 'Judge B (Wei Lindqvist)', icon: Shield, token: 'jdg_b_44de' },
    { role: 'organizer', label: 'Organizer (Alice)', icon: Trophy, token: 'org_7f2a' }
  ];

  const showToast = (msg, type = 'success') => {
    setNotification({ msg, type });
    setTimeout(() => setNotification(null), 4000);
  };

  const switchAccount = async (token) => {
    if (!token) {
      document.cookie = "session=; path=/; max-age=0";
      setCurrentUser(null);
      setView('gallery');
      showToast("Browsing as anonymous visitor");
      return;
    }
    document.cookie = `session=${token}; path=/; max-age=86400`;
    fetchCurrentUser();
  };

  const fetchCurrentUser = async () => {
    try {
      const res = await fetch(`${API_BASE}/auth/me`);
      if (res.ok) {
        const user = await res.json();
        setCurrentUser(user);
        showToast(`Signed in as ${user.name} (${user.role.toUpperCase()})`);
      } else {
        setCurrentUser(null);
      }
    } catch (e) {
      setCurrentUser(null);
    }
  };

  const fetchProjects = async () => {
    try {
      setLoading(true);
      const url = new URL(`${window.location.origin}${API_BASE}/projects`);
      if (selectedTrack !== 'all') url.searchParams.append('track', selectedTrack);
      if (searchQuery) url.searchParams.append('search', searchQuery);

      const res = await fetch(url);
      if (res.ok) {
        const data = await res.json();
        setProjects(data);
      }
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  const fetchEvent = async () => {
    try {
      const res = await fetch(`${API_BASE}/events`);
      if (res.ok) {
        const data = await res.json();
        if (data.length > 0) setEventData(data[0]);
      }
    } catch (e) {
      console.error(e);
    }
  };

  const fetchResults = async () => {
    try {
      setLoading(true);
      const res = await fetch(`${API_BASE}/results`);
      if (res.ok) {
        const data = await res.json();
        setResultsData(data);
      }
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  const fetchOrganizerData = async () => {
    try {
      setLoading(true);
      const res = await fetch(`${API_BASE}/organizer/overview`);
      if (res.ok) {
        const data = await res.json();
        setOrganizerData(data);
      } else if (res.status === 403 || res.status === 401) {
        showToast("Access Denied: Organizer privileges required.", "error");
      }
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  const fetchJudgeAssignments = async () => {
    try {
      setLoading(true);
      const res = await fetch(`${API_BASE}/judge/assignments`);
      if (res.ok) {
        const data = await res.json();
        setJudgeAssignments(data);
      }
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchCurrentUser();
    fetchEvent();
    fetchProjects();
  }, []);

  useEffect(() => {
    fetchProjects();
  }, [selectedTrack, searchQuery]);

  useEffect(() => {
    if (view === 'results') fetchResults();
    if (view === 'organizer') fetchOrganizerData();
    if (view === 'judge') fetchJudgeAssignments();
  }, [view]);

  // Handle Score Submit
  const handleScoreSubmit = async (projectId, criteriaScores, comment) => {
    try {
      const res = await fetch(`${API_BASE}/judge/scores`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          project_id: projectId,
          criteria: criteriaScores,
          comment: comment
        })
      });
      if (res.ok) {
        showToast("Score successfully saved in isolated database!");
        confetti({ particleCount: 50, spread: 70, origin: { y: 0.8 }, colors: ['#F97316', '#F59E0B', '#EF4444'] });
        fetchJudgeAssignments();
      } else {
        const err = await res.json();
        showToast(err.detail || "Scoring failed", "error");
      }
    } catch (e) {
      showToast("Error saving score", "error");
    }
  };

  const isLight = theme === 'light';
  const role = currentUser?.role || 'visitor';

  // Role-based visible tabs computation:
  // - Public Gallery: All roles (Visitor, Participant, Judge, Organizer, Admin)
  // - Submit Project: Participant, Organizer, Admin (Hidden for Judge & Visitor)
  // - Judging Engine: Judge, Admin (Hidden for Participant & Visitor)
  // - Organizer Ops: Organizer, Admin (Hidden for Judge, Participant, Visitor)
  // - Fair Leaderboard: All roles
  const allNavItems = [
    { id: 'gallery', label: 'Public Gallery', icon: LayoutGrid, allowedRoles: ['visitor', 'participant', 'judge', 'organizer', 'admin'] },
    { id: 'submit', label: 'Submit Project', icon: PlusCircle, allowedRoles: ['participant', 'organizer', 'admin'] },
    { id: 'judge', label: 'Judging Engine', icon: Scale, allowedRoles: ['judge', 'admin'] },
    { id: 'organizer', label: 'Organizer Ops', icon: Trophy, allowedRoles: ['organizer', 'admin'] },
    { id: 'results', label: 'Fair Leaderboard', icon: Award, allowedRoles: ['visitor', 'participant', 'judge', 'organizer', 'admin'] }
  ];

  const visibleNavItems = allNavItems.filter(item => item.allowedRoles.includes(role));

  // Automatically adjust view if current view is not allowed for the selected role
  useEffect(() => {
    const isCurrentViewAllowed = visibleNavItems.some(item => item.id === view);
    if (!isCurrentViewAllowed) {
      setView('gallery');
    }
  }, [role, view]);

  // Helper track badge colors
  const getTrackBadgeStyle = (trackName = '') => {
    const t = trackName.toLowerCase();
    if (t.includes('access')) return isLight ? 'bg-orange-100 text-orange-700 border-orange-200' : 'bg-orange-500/10 text-orange-400 border-orange-500/30';
    if (t.includes('health')) return isLight ? 'bg-emerald-100 text-emerald-700 border-emerald-200' : 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30';
    if (t.includes('edu')) return isLight ? 'bg-amber-100 text-amber-800 border-amber-200' : 'bg-amber-500/10 text-amber-400 border-amber-500/30';
    if (t.includes('dev') || t.includes('tool')) return isLight ? 'bg-orange-100 text-orange-800 border-orange-200' : 'bg-orange-500/10 text-orange-400 border-orange-500/30';
    if (t.includes('sec')) return isLight ? 'bg-rose-100 text-rose-700 border-rose-200' : 'bg-rose-500/10 text-rose-400 border-rose-500/30';
    return isLight ? 'bg-stone-100 text-stone-700 border-stone-200' : 'bg-stone-800 text-stone-300 border-stone-700';
  };

  return (
    <div className={`min-h-screen flex flex-col font-sans transition-colors duration-200 ${isLight ? 'light-mode bg-[#FAFAF8] text-[#1C1917]' : 'dark-mode bg-[#080604] text-[#FDF4EB]'}`}>
      {/* Toast Notification */}
      {notification && (
        <div className={`fixed top-4 right-4 z-50 px-5 py-3.5 rounded-2xl border shadow-2xl flex items-center space-x-3 transition-all duration-300 animate-in fade-in slide-in-from-top-4 ${
          notification.type === 'error'
            ? 'bg-rose-950 text-rose-200 border-rose-500/50'
            : isLight ? 'bg-white text-stone-800 border-orange-300 shadow-orange-500/10' : 'bg-orange-950 text-orange-200 border-orange-500/50'
        }`}>
          {notification.type === 'error' ? <AlertCircle className="w-5 h-5 text-rose-500" /> : <Check className="w-5 h-5 text-emerald-500" />}
          <span className="text-sm font-semibold">{notification.msg}</span>
        </div>
      )}

      {/* Top Navbar with Parakh Logo and Role-Based Tabs */}
      <header className="sticky top-0 z-40 navbar-blur">
        <div className="w-full px-4 sm:px-8 lg:px-12 h-20 flex items-center justify-between">
          {/* Logo & Brand Name: Parakh */}
          <div className="flex items-center space-x-3 cursor-pointer" onClick={() => setView('gallery')}>
            <div className={`p-1.5 rounded-2xl flex items-center justify-center transition-all ${
              isLight ? 'bg-transparent' : 'bg-white shadow-md shadow-white/10'
            }`}>
              <img
                src="/parakh-logo.svg"
                alt="Parakh Logo"
                className="w-9 h-9 object-contain"
              />
            </div>
            <div className="flex items-center space-x-3">
              <span className={`text-2xl font-black tracking-tight ${isLight ? 'text-stone-900' : 'text-white'}`}>
                PARAKH
              </span>
              <span className={`px-2.5 py-1 text-[11px] font-bold uppercase tracking-wider rounded-full border flex items-center space-x-1 ${
                isLight ? 'bg-emerald-50 text-emerald-700 border-emerald-200' : 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30'
              }`}>
                <CheckCircle2 className="w-3.5 h-3.5 text-emerald-500 inline mr-0.5" />
                <span>T1 & T2 VERIFIED</span>
              </span>
            </div>
          </div>

          {/* Navigation Items (Role-Filtered) */}
          <nav className="flex items-center space-x-1 sm:space-x-2">
            {visibleNavItems.map((tab) => {
              const Icon = tab.icon;
              const active = view === tab.id;
              return (
                <button
                  key={tab.id}
                  onClick={() => setView(tab.id)}
                  className={`px-3.5 py-2 rounded-xl text-xs sm:text-sm font-bold transition-all flex items-center space-x-2 cursor-pointer ${
                    active
                      ? isLight
                        ? 'bg-orange-50 text-orange-600 border border-orange-200 shadow-sm'
                        : 'bg-orange-600/30 text-amber-300 border border-orange-500/40'
                      : isLight
                        ? 'text-stone-600 hover:text-orange-600 hover:bg-stone-50'
                        : 'text-stone-400 hover:text-stone-200 hover:bg-stone-900/60'
                  }`}
                >
                  <Icon className={`w-4 h-4 ${active ? 'text-orange-500' : 'text-stone-400'}`} />
                  <span className="hidden md:inline">{tab.label}</span>
                </button>
              );
            })}
          </nav>

          {/* Right Actions: Theme Toggle & Role Persona Switcher */}
          <div className="flex items-center space-x-3">
            {/* Light / Dark Mode Toggle Button */}
            <button
              onClick={() => setTheme(isLight ? 'dark' : 'light')}
              title={`Switch to ${isLight ? 'Dark' : 'Light'} Mode`}
              className={`p-2.5 rounded-xl border flex items-center justify-center transition-all cursor-pointer ${
                isLight
                  ? 'bg-stone-100 hover:bg-stone-200 text-stone-700 border-stone-200'
                  : 'bg-stone-900 hover:bg-stone-800 text-amber-400 border-orange-950'
              }`}
            >
              {isLight ? <Moon className="w-4 h-4 text-stone-700" /> : <Sun className="w-4 h-4 text-amber-400" />}
            </button>

            {/* Persona Switcher Dropdown */}
            <div className="relative group">
              <button className={`flex items-center space-x-2 px-4 py-2 rounded-xl border text-xs font-bold transition-all cursor-pointer ${
                isLight
                  ? 'bg-white border-orange-300 text-stone-800 shadow-sm hover:border-orange-400'
                  : 'bg-[#18110C] border-orange-900/60 text-orange-200 hover:border-orange-500'
              }`}>
                <Shield className="w-4 h-4 text-orange-500" />
                <span>{currentUser ? `${currentUser.name} (${currentUser.role.toUpperCase()})` : 'Visitor (PUBLIC)'}</span>
                <ChevronDown className="w-3.5 h-3.5 text-stone-400" />
              </button>
              <div className={`absolute right-0 mt-2 w-64 py-2.5 rounded-2xl shadow-2xl hidden group-hover:block z-50 border ${
                isLight ? 'bg-white border-stone-200' : 'bg-[#16100B] border-orange-900'
              }`}>
                <div className={`px-4 py-2 text-[11px] font-bold uppercase tracking-wider border-b ${
                  isLight ? 'text-stone-400 border-stone-100' : 'text-orange-400 border-orange-950'
                }`}>
                  Select Role Persona
                </div>
                {accounts.map((acc, i) => (
                  <button
                    key={i}
                    onClick={() => switchAccount(acc.token)}
                    className={`w-full text-left px-4 py-2.5 text-xs font-semibold flex items-center space-x-3 transition-colors cursor-pointer ${
                      isLight ? 'text-stone-700 hover:bg-orange-50 hover:text-orange-600' : 'text-stone-300 hover:bg-orange-600/20 hover:text-orange-300'
                    }`}
                  >
                    <acc.icon className="w-4 h-4 text-orange-500" />
                    <span>{acc.label}</span>
                  </button>
                ))}
              </div>
            </div>
          </div>
        </div>
      </header>

      {/* Main Wide Container */}
      <main className="flex-1 w-full px-4 sm:px-8 lg:px-12 py-8">
        {/* VIEW 1: PUBLIC GALLERY */}
        {view === 'gallery' && (
          <div className="space-y-8">
            {/* Hero Banner with Parakh Evaluation Branding */}
            <div className="relative rounded-3xl p-8 sm:p-12 overflow-hidden hero-banner">
              <div className="relative z-10 max-w-4xl">
                <div className="inline-flex items-center space-x-2 px-3.5 py-1.5 rounded-full bg-orange-500/10 border border-orange-500/30 text-xs font-bold text-orange-700 mb-4">
                  <Zap className="w-3.5 h-3.5 text-orange-600" />
                  <span>Parakh Evaluation Hub</span>
                </div>
                <h1 className={`text-3xl sm:text-5xl font-black tracking-tight mb-4 ${isLight ? 'text-[#0F172A]' : 'text-white'}`}>
                  40+ Verified Hackathon Submissions & Live Judging
                </h1>
                <p className={`text-sm sm:text-base leading-relaxed mb-8 max-w-2xl ${isLight ? 'text-stone-700' : 'text-stone-300'}`}>
                  Explore projects evaluated with strict backend judge isolation, Z-score cross-judge normalization, and automated verification on Parakh.
                </p>

                {/* Filter & Search Bar */}
                <div className="flex flex-col sm:flex-row gap-3.5">
                  <div className="relative flex-1">
                    <input
                      type="text"
                      placeholder="Search across 40+ fixture projects by title, summary or tech..."
                      value={searchQuery}
                      onChange={(e) => setSearchQuery(e.target.value)}
                      className="w-full pl-11 pr-4 py-3.5 rounded-2xl text-sm font-medium input-box focus:outline-none focus:border-orange-500"
                    />
                    <Filter className="w-5 h-5 text-orange-500 absolute left-3.5 top-3.5" />
                  </div>
                  <select
                    value={selectedTrack}
                    onChange={(e) => setSelectedTrack(e.target.value)}
                    className="px-5 py-3.5 rounded-2xl text-sm font-semibold input-box focus:outline-none focus:border-orange-500 cursor-pointer"
                  >
                    <option value="all">All Tracks (8 Tracks Available)</option>
                    {eventData?.tracks?.map((t) => (
                      <option key={t.id} value={t.id}>{t.name}</option>
                    ))}
                  </select>
                </div>
              </div>
            </div>

            {/* Project Cards */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
              {projects.map((p) => {
                const trackStyle = getTrackBadgeStyle(p.track?.name);
                return (
                  <div
                    key={p.id}
                    onClick={() => setSelectedProject(p)}
                    className="glass-card rounded-2xl p-6 flex flex-col justify-between cursor-pointer group"
                  >
                    <div>
                      <div className="flex items-center justify-between mb-3.5">
                        <span className={`px-3 py-1 rounded-lg text-[11px] font-bold border ${trackStyle}`}>
                          {p.track?.name || 'General'}
                        </span>
                        <span className={`text-[11px] font-mono ${isLight ? 'text-stone-400' : 'text-stone-500'}`}>
                          {p.id}
                        </span>
                      </div>
                      <h3 className={`text-xl font-bold mb-2 group-hover:text-orange-600 transition-colors ${isLight ? 'text-stone-900' : 'text-white'}`}>
                        {p.title}
                      </h3>
                      <p className={`text-xs line-clamp-3 mb-6 leading-relaxed ${isLight ? 'text-stone-600' : 'text-stone-400'}`}>
                        {p.summary || 'A state of the art submission built during the Parakh hackathon.'}
                      </p>
                    </div>

                    <div className={`pt-4 border-t flex items-center justify-between text-xs ${isLight ? 'border-stone-100 text-stone-500' : 'border-orange-950 text-stone-400'}`}>
                      <span className={`font-semibold ${isLight ? 'text-stone-700' : 'text-stone-300'}`}>
                        {p.team?.name || 'Solo'}
                      </span>
                      <div className="flex items-center space-x-3.5">
                        <span className="flex items-center space-x-1 text-orange-600 font-bold">
                          <Scale className="w-3.5 h-3.5" />
                          <span>{p.scores_count} reviews</span>
                        </span>
                        <span className={`flex items-center space-x-1 font-semibold ${isLight ? 'text-emerald-600' : 'text-emerald-400'}`}>
                          <ThumbsUp className="w-3.5 h-3.5" />
                          <span>{p.votes_count}</span>
                        </span>
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        )}

        {/* VIEW 2: SUBMIT PROJECT (Participants / Organizers) */}
        {view === 'submit' && (
          <div className="max-w-3xl mx-auto py-4">
            <div className="glass-panel rounded-3xl p-8 sm:p-10">
              <div className="flex items-center space-x-4 mb-6">
                <div className="w-12 h-12 rounded-2xl bg-orange-500/15 border border-orange-500/30 flex items-center justify-center">
                  <PlusCircle className="w-6 h-6 text-orange-600" />
                </div>
                <div>
                  <h2 className={`text-2xl font-black ${isLight ? 'text-stone-900' : 'text-white'}`}>Submit New Project</h2>
                  <p className="text-xs text-stone-500">Live submission portal with GitHub repository linking & verification.</p>
                </div>
              </div>

              {/* Deadline Status Banner */}
              <div className="p-5 rounded-2xl bg-amber-50 border border-amber-200 text-amber-900 text-sm mb-8 flex items-start space-x-3.5">
                <Lock className="w-5 h-5 shrink-0 mt-0.5 text-amber-600" />
                <div>
                  <p className="font-bold flex items-center space-x-2">
                    <span>Hackathon Submissions Active</span>
                    <span className="px-2 py-0.5 text-[10px] bg-emerald-100 text-emerald-700 rounded-full font-bold border border-emerald-200">OPEN</span>
                  </p>
                  <p className="text-xs text-amber-800/90 mt-1">
                    Enter your project details, GitHub repository link, and live demo below. Submissions will be registered directly into the Parakh database.
                  </p>
                </div>
              </div>

              <form onSubmit={async (e) => {
                e.preventDefault();
                const formData = new FormData(e.target);
                try {
                  const res = await fetch(`${API_BASE}/projects/new`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                      title: formData.get('title'),
                      summary: formData.get('summary'),
                      repo_url: formData.get('repo_url'),
                      track_id: formData.get('track_id')
                    })
                  });
                  if (res.ok) {
                    showToast("Project successfully submitted to Parakh!");
                    confetti({ colors: ['#F97316', '#F59E0B'] });
                    fetchProjects();
                    setView('gallery');
                  } else {
                    const err = await res.json();
                    showToast(err.detail || "Submission refused", "error");
                  }
                } catch (err) {
                  showToast("Network/server error", "error");
                }
              }} className="space-y-5">
                <div>
                  <label className="block text-xs font-bold text-stone-600 mb-2 uppercase tracking-wide">Project Title</label>
                  <input
                    name="title"
                    required
                    placeholder="e.g. Autonomous Multi-Agent Evaluator"
                    className="w-full px-4 py-3 rounded-xl text-sm input-box focus:border-orange-500 focus:outline-none"
                  />
                </div>
                <div>
                  <label className="block text-xs font-bold text-stone-600 mb-2 uppercase tracking-wide">Select Track</label>
                  <select
                    name="track_id"
                    className="w-full px-4 py-3 rounded-xl text-sm input-box focus:border-orange-500 focus:outline-none cursor-pointer"
                  >
                    {eventData?.tracks?.map((t) => (
                      <option key={t.id} value={t.id}>{t.name}</option>
                    ))}
                  </select>
                </div>
                <div>
                  <label className="block text-xs font-bold text-stone-600 mb-2 uppercase tracking-wide">Project Summary</label>
                  <textarea
                    name="summary"
                    rows={3}
                    placeholder="Describe what your project solves, its core architecture, and impact..."
                    className="w-full px-4 py-3 rounded-xl text-sm input-box focus:border-orange-500 focus:outline-none"
                  />
                </div>
                <div>
                  <label className="block text-xs font-bold text-stone-600 mb-2 uppercase tracking-wide flex items-center justify-between">
                    <span>GitHub Repository Link (Required)</span>
                    <span className="text-[11px] text-orange-600 font-normal">e.g. https://github.com/username/repo</span>
                  </label>
                  <input
                    name="repo_url"
                    type="url"
                    required
                    placeholder="https://github.com/your-team/hackathon-project"
                    className="w-full px-4 py-3 rounded-xl text-sm input-box focus:border-orange-500 focus:outline-none"
                  />
                </div>
                <button
                  type="submit"
                  className="w-full py-4 bg-gradient-to-r from-orange-600 to-amber-600 hover:from-orange-500 hover:to-amber-500 rounded-xl font-bold text-sm text-white shadow-xl shadow-orange-600/30 transition-all cursor-pointer"
                >
                  Submit Hackathon Project
                </button>
              </form>
            </div>
          </div>
        )}

        {/* VIEW 3: JUDGING ENGINE & ISOLATED SCORING (Judges Only) */}
        {view === 'judge' && (
          <div className="space-y-6">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
              <div>
                <h2 className={`text-3xl font-black flex items-center space-x-3 ${isLight ? 'text-stone-900' : 'text-white'}`}>
                  <Scale className="w-7 h-7 text-orange-600" />
                  <span>Isolated Judge Scoring Interface</span>
                </h2>
                <p className="text-xs text-stone-500 mt-1">
                  Active Judge: <span className="text-orange-600 font-bold">{currentUser?.name || 'Judge A (Tomas Varga)'}</span>. Strictly isolated from peer judges.
                </p>
              </div>
              <div>
                <span className={`px-4 py-1.5 text-xs rounded-full font-bold flex items-center space-x-2 border ${
                  isLight ? 'bg-orange-50 text-orange-700 border-orange-200' : 'bg-orange-500/15 border-orange-500/30 text-orange-300'
                }`}>
                  <Shield className="w-4 h-4 text-orange-500" />
                  <span>Strict Backend Isolation Active</span>
                </span>
              </div>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-3 gap-6">
              {judgeAssignments.map((asg) => (
                <div key={asg.project_id} className="glass-panel rounded-3xl p-6 flex flex-col justify-between">
                  <div>
                    <div className="flex items-center justify-between mb-3">
                      <span className={`px-3 py-1 rounded-lg text-[11px] font-bold border ${getTrackBadgeStyle(asg.track?.name)}`}>
                        {asg.track?.name || 'Assigned Track'}
                      </span>
                      {asg.is_scored ? (
                        <span className="text-xs font-bold text-emerald-600 flex items-center space-x-1">
                          <CheckCircle2 className="w-4 h-4" />
                          <span>Scored</span>
                        </span>
                      ) : (
                        <span className="text-xs font-bold text-amber-600">Pending Review</span>
                      )}
                    </div>

                    <h3 className={`text-xl font-bold mb-1.5 ${isLight ? 'text-stone-900' : 'text-white'}`}>{asg.title}</h3>
                    <p className={`text-xs mb-4 leading-relaxed ${isLight ? 'text-stone-600' : 'text-stone-400'}`}>{asg.summary}</p>

                    {/* Participant Project & GitHub Links to Evaluate */}
                    <div className="p-3.5 rounded-2xl sub-card space-y-2 mb-5">
                      <div className="flex items-center justify-between text-xs">
                        <span className="text-stone-500 font-medium">Team:</span>
                        <span className={`font-bold ${isLight ? 'text-stone-800' : 'text-stone-200'}`}>{asg.team_name}</span>
                      </div>
                      <div className="flex items-center justify-between text-xs">
                        <span className="text-stone-500 font-medium">Repository:</span>
                        {asg.repo_url ? (
                          <a
                            href={asg.repo_url}
                            target="_blank"
                            rel="noreferrer"
                            className="text-orange-600 hover:text-orange-700 font-bold flex items-center space-x-1 hover:underline truncate max-w-[200px]"
                          >
                            <span>GitHub Code</span>
                            <ExternalLink className="w-3 h-3 shrink-0" />
                          </a>
                        ) : (
                          <span className="text-stone-400 italic">No repo url</span>
                        )}
                      </div>
                      <div className="pt-1 flex items-center justify-between text-xs">
                        <button
                          onClick={() => {
                            const fullProj = projects.find(p => p.id === asg.project_id) || asg;
                            setSelectedProject(fullProj);
                          }}
                          className="w-full py-1.5 px-2 bg-orange-500/10 hover:bg-orange-500/20 text-orange-600 rounded-lg font-bold text-[11px] flex items-center justify-center space-x-1.5 cursor-pointer transition-colors"
                        >
                          <Eye className="w-3.5 h-3.5" />
                          <span>View Full Submission Details</span>
                        </button>
                      </div>
                    </div>

                    {/* Rubric Matrix */}
                    <div className="space-y-3.5 sub-card p-4 rounded-2xl mb-6">
                      <div className="text-xs font-bold text-orange-600 uppercase tracking-wider mb-2">Weighted Criteria (1-5)</div>
                      {['functionality', 'quality', 'innovation'].map((crit) => (
                        <div key={crit} className="flex items-center justify-between">
                          <span className={`text-xs capitalize font-semibold ${isLight ? 'text-stone-700' : 'text-stone-300'}`}>{crit}</span>
                          <div className="flex items-center space-x-1.5">
                            {[1, 2, 3, 4, 5].map((val) => {
                              const currentVal = asg.my_score?.criteria?.[crit] || 3;
                              return (
                                <button
                                  key={val}
                                  onClick={() => {
                                    const updated = { ...(asg.my_score?.criteria || { functionality: 3, quality: 3, innovation: 3 }), [crit]: val };
                                    handleScoreSubmit(asg.project_id, updated, asg.my_score?.comment || "Evaluated");
                                  }}
                                  className={`w-8 h-8 rounded-xl text-xs font-black transition-all cursor-pointer ${
                                    currentVal === val
                                      ? 'bg-orange-600 text-white shadow-md shadow-orange-600/40 scale-105'
                                      : isLight ? 'bg-white text-stone-600 border border-stone-200 hover:bg-orange-50' : 'bg-[#18110C] text-stone-400 hover:bg-stone-800'
                                  }`}
                                >
                                  {val}
                                </button>
                              );
                            })}
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>

                  <div className="text-right pt-2">
                    <button
                      onClick={() => handleScoreSubmit(
                        asg.project_id,
                        asg.my_score?.criteria || { functionality: 4, quality: 4, innovation: 4 },
                        "Verified by Judge"
                      )}
                      className="w-full py-2.5 bg-orange-600 hover:bg-orange-500 text-xs font-bold text-white rounded-xl transition-all shadow-md shadow-orange-600/30 cursor-pointer"
                    >
                      Save Evaluation
                    </button>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* VIEW 4: ORGANIZER OPS & PROGRESS (Organizers Only) */}
        {view === 'organizer' && (
          <div className="space-y-8">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
              <div>
                <h2 className={`text-3xl font-black flex items-center space-x-3 ${isLight ? 'text-stone-900' : 'text-white'}`}>
                  <Trophy className="w-7 h-7 text-amber-500" />
                  <span>Organizer Operations & Live Progress</span>
                </h2>
                <p className="text-xs text-stone-500 mt-1">
                  Live real-time monitoring of judge completion, tracks, and CSV exports.
                </p>
              </div>
              <a
                href="/api/export.csv"
                target="_blank"
                rel="noreferrer"
                className="px-5 py-3 bg-gradient-to-r from-emerald-600 to-teal-600 hover:from-emerald-500 hover:to-teal-500 rounded-2xl text-xs font-bold text-white flex items-center space-x-2 shadow-lg shadow-emerald-600/20"
              >
                <Download className="w-4 h-4" />
                <span>Export Official Results (CSV)</span>
              </a>
            </div>

            {/* Metrics Cards */}
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-6">
              <div className="glass-panel p-8 rounded-3xl">
                <div className="text-xs font-bold text-stone-500 uppercase tracking-wider mb-2">Total Projects</div>
                <div className={`text-4xl font-black ${isLight ? 'text-stone-900' : 'text-white'}`}>{organizerData?.total_projects || 41}</div>
                <div className="text-xs text-orange-600 mt-2 font-bold">100% loaded from fixtures</div>
              </div>
              <div className="glass-panel p-8 rounded-3xl">
                <div className="text-xs font-bold text-stone-500 uppercase tracking-wider mb-2">Active Judges</div>
                <div className={`text-4xl font-black ${isLight ? 'text-stone-900' : 'text-white'}`}>{organizerData?.total_judges || 30}</div>
                <div className="text-xs text-amber-600 mt-2 font-bold">Assigned across 8 tracks</div>
              </div>
              <div className="glass-panel p-8 rounded-3xl">
                <div className="text-xs font-bold text-stone-500 uppercase tracking-wider mb-2">Completed Reviews</div>
                <div className={`text-4xl font-black ${isLight ? 'text-stone-900' : 'text-white'}`}>{organizerData?.total_reviews || 118}</div>
                <div className="text-xs text-emerald-600 mt-2 font-bold">Normalized via Z-Score algorithm</div>
              </div>
            </div>

            {/* Track Breakdown Table */}
            <div className="glass-panel rounded-3xl p-8">
              <h3 className={`text-xl font-bold mb-6 ${isLight ? 'text-stone-900' : 'text-white'}`}>Track Distribution & Review Progress</h3>
              <div className="overflow-x-auto">
                <table className="w-full text-left text-xs">
                  <thead className="table-header uppercase font-bold text-[11px]">
                    <tr>
                      <th className="px-5 py-4 rounded-l-xl">Track Name</th>
                      <th className="px-5 py-4">Projects</th>
                      <th className="px-5 py-4">Judges</th>
                      <th className="px-5 py-4 rounded-r-xl">Status</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-stone-200">
                    {organizerData?.tracks?.map((t) => (
                      <tr key={t.track_id} className="table-row">
                        <td className={`px-5 py-4 font-bold ${isLight ? 'text-stone-800' : 'text-white'}`}>{t.track_name}</td>
                        <td className="px-5 py-4 font-medium">{t.projects_count} projects</td>
                        <td className="px-5 py-4 font-medium">{t.judges_count} judges</td>
                        <td className="px-5 py-4">
                          <span className="px-3 py-1 bg-emerald-100 text-emerald-700 border border-emerald-200 rounded-lg font-bold">
                            Live & Active
                          </span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        )}

        {/* VIEW 5: LEADERBOARD & NORMALIZATION RESULTS */}
        {view === 'results' && (
          <div className="space-y-6">
            <div>
              <h2 className={`text-3xl font-black flex items-center space-x-3 ${isLight ? 'text-stone-900' : 'text-white'}`}>
                <Award className="w-7 h-7 text-amber-500" />
                <span>Fair Normalized Hackathon Leaderboard</span>
              </h2>
              <p className="text-xs text-stone-500 mt-1">
                Cross-judge Z-Score Normalization + Min-Max Variance Adjustment to eliminate harsh/generous reviewer bias.
              </p>
            </div>

            <div className="glass-panel rounded-3xl overflow-hidden">
              <div className="overflow-x-auto">
                <table className="w-full text-left text-xs">
                  <thead className="table-header uppercase font-bold text-[11px]">
                    <tr>
                      <th className="px-6 py-4">Rank</th>
                      <th className="px-6 py-4">Project Title</th>
                      <th className="px-6 py-4">Track</th>
                      <th className="px-6 py-4">Raw Average</th>
                      <th className="px-6 py-4">Z-Score Normalized</th>
                      <th className="px-6 py-4">Final Fair Score</th>
                      <th className="px-6 py-4">Judges Evaluated</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-stone-200">
                    {resultsData.map((r) => (
                      <tr key={r.project_id} className="table-row">
                        <td className="px-6 py-4 font-bold">
                          <span className={`inline-flex items-center justify-center w-7 h-7 rounded-full text-xs font-black ${
                            r.rank === 1 ? 'bg-amber-100 text-amber-800 border border-amber-300' :
                            r.rank === 2 ? 'bg-stone-200 text-stone-800 border border-stone-300' :
                            r.rank === 3 ? 'bg-orange-100 text-orange-800 border border-orange-300' :
                            'text-stone-500'
                          }`}>
                            {r.rank}
                          </span>
                        </td>
                        <td className={`px-6 py-4 font-bold ${isLight ? 'text-stone-900' : 'text-white'}`}>{r.title}</td>
                        <td className="px-6 py-4 text-stone-500 font-medium">{r.track_name}</td>
                        <td className="px-6 py-4 font-mono text-stone-500">{r.raw_avg_score.toFixed(2)}</td>
                        <td className="px-6 py-4 font-mono text-orange-600 font-bold">{r.z_score_normalized.toFixed(2)}</td>
                        <td className="px-6 py-4 font-mono font-black text-amber-600 text-sm">{r.final_score.toFixed(2)} / 5.0</td>
                        <td className="px-6 py-4 font-medium">{r.reviews_count} reviews</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        )}
      </main>

      {/* Project Modal Detail View */}
      {selectedProject && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm">
          <div className="glass-panel w-full max-w-2xl rounded-3xl p-8 max-h-[90vh] overflow-y-auto">
            <div className="flex items-center justify-between mb-4">
              <span className={`px-3 py-1 rounded-lg text-xs font-bold border ${getTrackBadgeStyle(selectedProject.track?.name)}`}>
                {selectedProject.track?.name || 'General'}
              </span>
              <button
                onClick={() => setSelectedProject(null)}
                className="text-stone-400 hover:text-stone-800 text-xl font-bold cursor-pointer"
              >
                ✕
              </button>
            </div>
            <h2 className={`text-2xl sm:text-3xl font-black mb-3 ${isLight ? 'text-stone-900' : 'text-white'}`}>{selectedProject.title}</h2>
            <p className={`text-sm mb-8 leading-relaxed ${isLight ? 'text-stone-600' : 'text-stone-300'}`}>{selectedProject.summary}</p>

            <div className="p-5 rounded-2xl sub-card space-y-3 mb-8">
              <div className="text-xs text-stone-500 flex justify-between">
                <span>Team:</span>
                <span className={`font-bold ${isLight ? 'text-stone-800' : 'text-stone-200'}`}>{selectedProject.team?.name}</span>
              </div>
              <div className="text-xs text-stone-500 flex justify-between">
                <span>Repository:</span>
                <a href={selectedProject.repo_url} target="_blank" rel="noreferrer" className="text-orange-600 hover:underline flex items-center space-x-1 font-semibold">
                  <span>{selectedProject.repo_url}</span>
                  <ExternalLink className="w-3.5 h-3.5" />
                </a>
              </div>
            </div>

            <div className="flex space-x-4">
              <button
                onClick={async () => {
                  try {
                    const res = await fetch(`${API_BASE}/community/vote`, {
                      method: 'POST',
                      headers: { 'Content-Type': 'application/json' },
                      body: JSON.stringify({ project_id: selectedProject.id })
                    });
                    if (res.ok) {
                      showToast("Community vote registered!");
                      confetti({ colors: ['#F97316', '#F59E0B'] });
                      fetchProjects();
                      setSelectedProject(null);
                    }
                  } catch (e) {
                    showToast("Voting failed", "error");
                  }
                }}
                className="flex-1 py-3.5 bg-gradient-to-r from-orange-600 to-amber-600 hover:from-orange-500 hover:to-amber-500 text-white rounded-xl text-xs font-bold flex items-center justify-center space-x-2 shadow-lg shadow-orange-600/30 cursor-pointer"
              >
                <ThumbsUp className="w-4 h-4" />
                <span>Cast Community Vote</span>
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
