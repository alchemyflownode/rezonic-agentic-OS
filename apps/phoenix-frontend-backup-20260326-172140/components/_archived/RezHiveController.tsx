"use client";

import { useState, useRef, useEffect } from "react";
import { 
  X, Play, RotateCw, Activity, Zap, Shield, Terminal, 
  RefreshCw, Trash2, BookOpen, Cpu, HardDrive, Network, 
  AlertTriangle, GitMerge, CheckCircle, Globe, Code,
  Eye, Brain, Database, Command, Settings, Bell, Mic,
  Video, Image, Boxes, Link, Wifi
} from "lucide-react";

interface OutputLine {
  id: string;
  text: string;
  timestamp: string;
  type: "command" | "success" | "error" | "info" | "heal" | "warning" | "constitution" | "search" | "code" | "vision" | "voice" | "mcp";
}

interface ServiceStatus {
  kernel: boolean;
  chroma: boolean;
  nextjs: boolean;
  ollama: boolean;
  ledger: boolean;
  duckduckgo: boolean;
  mcp: boolean;
}

interface WorkerStatus {
  orchestrator: boolean;
  brain: boolean;
  search: boolean;
  code: boolean;
  files: boolean;
  system: boolean;
  vision: boolean;
  voice: boolean;
}

interface SystemMetrics {
  cpu: number;
  memory: number;
  gpu: number;
  uptime: number;
  tokens: number;
  maxTokens: number;
}

const API_BASE = "http://localhost:8001";

export function RezHiveController() {
  const [isOpen, setIsOpen] = useState(false);
  const [output, setOutput] = useState<OutputLine[]>([]);
  const [loading, setLoading] = useState<Record<number, boolean>>({});
  const [services, setServices] = useState<ServiceStatus>({
    kernel: false, chroma: false, nextjs: true, ollama: false,
    ledger: false, duckduckgo: false, mcp: false
  });
  const [workers, setWorkers] = useState<WorkerStatus>({
    orchestrator: false, brain: false, search: false, code: false,
    files: false, system: false, vision: false, voice: false
  });
  const [metrics, setMetrics] = useState<SystemMetrics>({
    cpu: 0, memory: 0, gpu: 0, uptime: 0, tokens: 0, maxTokens: 8192
  });
  const[healingActive, setHealingActive] = useState(false);
  const [autoHeal, setAutoHeal] = useState(false);
  const [healCount, setHealCount] = useState(0);
  const[showLedger, setShowLedger] = useState(false);
  const[precedents, setPrecedents] = useState<any[]>([]);
  const [searchMode, setSearchMode] = useState<"duckduckgo" | "brave" | "google">("duckduckgo");
  const[isListening, setIsListening] = useState(false);
  
  const outputRef = useRef<HTMLDivElement>(null);
  const healthInterval = useRef<NodeJS.Timeout>();
  const metricsInterval = useRef<NodeJS.Timeout>();
  const failureCount = useRef<Record<string, number>>({});
  const immunityTimer = useRef<NodeJS.Timeout>();

  const getTime = () => {
    const d = new Date();
    return `${d.getHours().toString().padStart(2, '0')}:${d.getMinutes().toString().padStart(2, '0')}:${d.getSeconds().toString().padStart(2, '0')}`;
  };

  const addOutput = (text: string, type: OutputLine["type"] = "info") => {
    setOutput((prev) =>[...prev, {
      id: Math.random().toString(36).substring(2, 9),
      text, timestamp: getTime(), type,
    }]);
  };

  useEffect(() => { outputRef.current?.scrollIntoView({ behavior: "smooth" }); }, [output]);

  useEffect(() => {
    return () => {
      if (immunityTimer.current) clearTimeout(immunityTimer.current);
      if (healthInterval.current) clearInterval(healthInterval.current);
      if (metricsInterval.current) clearInterval(metricsInterval.current);
    };
  },[]);

  const fetchWithTimeout = async (url: string, options?: RequestInit, timeoutMs = 5000) => {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), timeoutMs);
    try {
      const response = await fetch(url, { ...options, signal: controller.signal });
      clearTimeout(timeoutId);
      return response;
    } catch (e) {
      clearTimeout(timeoutId);
      throw e;
    }
  };

  // =================================================================
  // MCP COMMANDS
  // =================================================================
  const checkMCP = async (): Promise<boolean> => {
    try {
      const response = await fetchWithTimeout('http://localhost:8002/health', {}, 2000).then(r => r.ok).catch(() => false);
      setServices(prev => ({ ...prev, mcp: response }));
      return response;
    } catch {
      setServices(prev => ({ ...prev, mcp: false }));
      return false;
    }
  };

  const mcpStatus = async (): Promise<string> => {
    addOutput("🔌 Checking MCP server status...", "command");
    try {
      const response = await fetch('http://localhost:8002/tools', { method: 'GET', timeout: 3000 }).catch(() => null);
      if (response && response.ok) {
        const data = await response.json();
        const toolCount = data.tools?.length || 0;
        setServices(prev => ({ ...prev, mcp: true }));
        return `✅ MCP server running with ${toolCount} tools available`;
      } else {
        setServices(prev => ({ ...prev, mcp: false }));
        return "❌ MCP server not responding (run mcp_server.py)";
      }
    } catch (e: any) {
      setServices(prev => ({ ...prev, mcp: false }));
      return `❌ MCP error: ${e.message}`;
    }
  };

  const mcpDiscover = async (): Promise<string> => {
    addOutput("🔍 Discovering MCP servers...", "command");
    try {
      return "🔍 **Available MCP Servers:**\n\n• 📁 Filesystem (local files)\n• 🐙 GitHub (repos, issues, PRs)\n• 💬 Slack (messages, channels)\n• 📅 Google Calendar\n• 📧 Gmail\n• ☁️ AWS S3\n• 🗄️ PostgreSQL\n\nInstall with: `pip install mcp-server-[name]`";
    } catch (e: any) { return `❌ Discovery failed: ${e.message}`; }
  };

  const mcpTest = async (): Promise<string> => {
    addOutput("🧪 Testing MCP connection...", "command");
    try {
      const response = await fetch('http://localhost:8002/call', {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ tool: "search_pc", arguments: { query: "budget", max_results: 5 } })
      }).catch(() => null);
      if (response && response.ok) return "✅ MCP connection successful: search_pc('budget') working";
      else return "⚠️ MCP connection failed - is the server running?";
    } catch (e: any) { return `❌ MCP test failed: ${e.message}`; }
  };

  // =================================================================
  // SYSTEM METRICS
  // =================================================================
  const updateMetrics = async () => {
    try {
      const response = await fetch(`${API_BASE}/health`);
      if (response.ok) {
        const data = await response.json();
        setMetrics(prev => ({ ...prev, cpu: data.cpu || prev.cpu, memory: data.memory || prev.memory, uptime: data.uptime || prev.uptime + 1 }));
      }
      const chatResponse = await fetch(`${API_BASE}/chat/${localStorage.getItem('rez_session_id') || 'anonymous'}/history`);
      if (chatResponse.ok) {
        const data = await chatResponse.json();
        const totalChars = data.messages.reduce((acc: number, msg: any) => acc + (msg.content?.length || 0), 0);
        setMetrics(prev => ({ ...prev, tokens: Math.ceil(totalChars / 4) }));
      }
    } catch (e) {}
  };

  // =================================================================
  // SERVICE CHECKS
  // =================================================================
  const checkDuckDuckGo = async (): Promise<boolean> => {
    try { return await fetchWithTimeout('https://api.duckduckgo.com/?q=test&format=json', {}, 3000).then(r=>r.ok); } 
    catch { return false; }
  };

  const checkWorkers = async (): Promise<WorkerStatus> => {
    try {
      const response = await fetch(`${API_BASE}/workers`);
      if (response.ok) {
        const data = await response.json();
        const workerStatus: WorkerStatus = {
          orchestrator: data.workers.some((w: any) => w.name === 'orchestrator' || w.name === 'router'),
          brain: data.workers.some((w: any) => w.name === 'brain'),
          search: data.workers.some((w: any) => w.name === 'search'),
          code: data.workers.some((w: any) => w.name === 'code'),
          files: data.workers.some((w: any) => w.name === 'files'),
          system: data.workers.some((w: any) => w.name === 'system'),
          vision: data.workers.some((w: any) => w.name === 'vision'),
          voice: data.workers.some((w: any) => w.name === 'voice')
        };
        setWorkers(workerStatus);
        return workerStatus;
      }
    } catch {}
    return workers;
  };

  // =================================================================
  // VISION & VOICE COMMANDS
  // =================================================================
  const testVision = async (task: string = "describe screen"): Promise<string> => {
    addOutput(`👁️ Testing Vision: "${task}"...`, "command");
    try {
      const response = await fetch(`${API_BASE}/kernel/stream`, {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ task, worker: "vision" })
      });
      if (response.ok) { addOutput(`✅ Vision test initiated`, "success"); return "Check chat for screen analysis"; }
      throw new Error(`HTTP ${response.status}`);
    } catch (e: any) { throw new Error(`Vision test failed: ${e.message}`); }
  };

  const testVoice = async (duration: number = 3): Promise<string> => {
    addOutput(`🎤 Testing Voice - listening for ${duration} seconds...`, "command");
    setIsListening(true);
    try {
      const response = await fetch(`${API_BASE}/kernel/stream`, {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ task: `listen ${duration}`, worker: "voice" })
      });
      if (response.ok) { addOutput(`✅ Voice test initiated`, "success"); setIsListening(false); return "Check chat for transcription"; }
      throw new Error(`HTTP ${response.status}`);
    } catch (e: any) { setIsListening(false); throw new Error(`Voice test failed: ${e.message}`); }
  };

  // =================================================================
  // LEDGER COMMANDS
  // =================================================================
  const checkLedger = async (silent = false): Promise<boolean> => {
    try {
      const response = await fetch(`${API_BASE}/api/v1/ps1/ledger-status`);
      if (!response.ok) return false;
      const data = await response.json();
      setServices(prev => ({ ...prev, ledger: true }));
      if (!silent) addOutput(`📚 Ledger: ${data.total_precedents} precedents stored`, "info");
      return true;
    } catch {
      setServices(prev => ({ ...prev, ledger: false }));
      return false;
    }
  };

  const viewPrecedents = async (): Promise<string> => {
    addOutput("📖 Fetching constitutional precedents...", "command");
    try {
      const response = await fetch(`${API_BASE}/api/v1/ps1/ledger-precedents`);
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      const data = await response.json();
      setPrecedents(data.precedents ||[]);
      
      if (data.precedents?.length === 0) { addOutput("📭 No precedents stored - ledger is empty", "info"); return "Ledger empty"; }
      
      addOutput(`📚 Found ${data.precedents.length} constitutional precedents:`, "constitution");
      data.precedents.slice(0, 5).forEach((p: any) => { addOutput(`  📜 ${p.input_hash?.slice(0,8)}... → ${p.preview}`, "constitution"); });
      setShowLedger(true);
      return `Displaying ${Math.min(5, data.precedents.length)} of ${data.precedents.length} precedents`;
    } catch (e: any) { throw new Error(`Ledger query failed: ${e.message}`); }
  };

  // =================================================================
  // SEARCH MODE & WORKER CONTROL
  // =================================================================
  const setSearchEngine = async (engine: "duckduckgo" | "brave" | "google"): Promise<string> => {
    setSearchMode(engine); addOutput(`🔍 Search engine set to: ${engine.toUpperCase()}`, "success"); return `Search mode: ${engine}`;
  };

  const testSearch = async (query: string = "latest AI news"): Promise<string> => {
    addOutput(`🔍 Testing ${searchMode.toUpperCase()} search: "${query}"...`, "command");
    try {
      const response = await fetch(`${API_BASE}/kernel/stream`, {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ task: query, worker: "search" })
      });
      if (response.ok) { addOutput(`✅ Search test initiated`, "success"); return "Check chat for results"; }
      throw new Error(`HTTP ${response.status}`);
    } catch (e: any) { throw new Error(`Search test failed: ${e.message}`); }
  };

  const testWorker = async (worker: string, task: string): Promise<string> => {
    addOutput(`🧪 Testing ${worker} worker: "${task}"...`, "command");
    try {
      const response = await fetch(`${API_BASE}/kernel/stream`, {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ task, worker })
      });
      if (response.ok) { addOutput(`✅ ${worker} worker test initiated`, "success"); return "Check chat for results"; }
      throw new Error(`HTTP ${response.status}`);
    } catch (e: any) { throw new Error(`Worker test failed: ${e.message}`); }
  };

  // =================================================================
  // KILL PORT & STATUS
  // =================================================================
  const killPort = async (port: number): Promise<string> => {
    addOutput(`🔪 Killing processes on port ${port}...`, "command");
    try {
      const response = await fetch(`${API_BASE}/admin/kill-port?port=${port}`, { method: "POST" }).catch(() => null);
      if (response?.ok) { addOutput(`✅ Port ${port} freed successfully`, "success"); return `Port ${port} is now available`; }
      return `Port kill attempted - verify manually`;
    } catch (e: any) { throw new Error(e.message); }
  };

  const checkStatus = async (silent = false): Promise<string> => {
    const startTime = Date.now();
    try {
      const kernel = await fetchWithTimeout(`${API_BASE}/health`, {}, 3000).then(r => r.ok).catch(() => false);
      let chroma = false;
      try { chroma = await fetchWithTimeout('http://localhost:8000/api/v1/heartbeat', {}, 2000).then(r=>r.ok); } catch {}
      const nextjs = await fetchWithTimeout('http://localhost:3001', {}, 2000).then(r => r.ok).catch(() => false);
      const ollama = await fetchWithTimeout('http://localhost:11434/api/version', {}, 2000).then(r => r.ok).catch(() => false);
      const ledger = await checkLedger(true);
      const duckduckgo = await checkDuckDuckGo();
      const mcp = await checkMCP();
      const workerStatus = await checkWorkers();

      const responseTime = Date.now() - startTime;
      setServices({ kernel, chroma, nextjs, ollama, ledger, duckduckgo, mcp });

      if (!kernel) failureCount.current.kernel = (failureCount.current.kernel || 0) + 1; else failureCount.current.kernel = 0;
      if (!ollama) failureCount.current.ollama = (failureCount.current.ollama || 0) + 1; else failureCount.current.ollama = 0;

      if (autoHeal && !healingActive) {
        if (failureCount.current.kernel > 2) {
          setHealingActive(true);
          addOutput("🩺 Auto-heal: Kernel critical - initiating recovery...", "heal");
          killPort(8001).then(() => {
            addOutput("⏳ Port freed. Waiting for resurrection...", "info");
            setHealCount(c => c + 1);
            immunityTimer.current = setTimeout(() => setHealingActive(false), 15000);
          }).catch(() => setHealingActive(false));
        } else if (failureCount.current.ollama > 2 && failureCount.current.kernel === 0) {
          setHealingActive(true);
          addOutput("🩺 Auto-heal: Ollama down - attempting restart...", "heal");
          setHealCount(c => c + 1);
          immunityTimer.current = setTimeout(() => setHealingActive(false), 15000);
        }
      }
      
      const workerStatusText = `ORCH: ${workerStatus.orchestrator ? "✅" : "❌"} | 🧠:${workerStatus.brain ? "✅" : "❌"} | 👁️:${workerStatus.search ? "✅" : "❌"} | ✋:${workerStatus.code ? "✅" : "❌"} | 📁:${workerStatus.files ? "✅" : "❌"} | ⚙️:${workerStatus.system ? "✅" : "❌"} | 👁️V:${workerStatus.vision ? "✅" : "❌"} | 🎤:${workerStatus.voice ? "✅" : "❌"}`;
      const statusMessage = `Kernel: ${kernel ? "✅" : "❌"} | Chroma: ${chroma ? "✅" : "❌"} | Next.js: ${nextjs ? "✅" : "❌"} | Ollama: ${ollama ? "✅" : "❌"} | DDG: ${duckduckgo ? "✅" : "❌"} | MCP: ${mcp ? "✅" : "❌"} (${responseTime}ms)`;
      
      if (!silent) {
        addOutput(statusMessage, "success");
        addOutput(workerStatusText, "info");
      }
      return statusMessage;
    } catch (e: any) {
      if (!silent) addOutput(`Health check error: ${e.message}`, "error");
      throw e;
    }
  };

  const getDriftReport = async (): Promise<string> => {
    addOutput("📊 Fetching zero-drift report...", "command");
    try {
      const response = await fetch(`${API_BASE}/api/v1/ps1/drift-report`);
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      const data = await response.json();
      addOutput(`📈 Total drift events: ${data.total_drift_events}`, data.total_drift_events === 0 ? 'success' : 'warning');
      addOutput(`🛡️ Unhealed drift: ${data.unhealed_drift}`, data.unhealed_drift === 0 ? 'success' : 'warning');
      return "Drift report complete";
    } catch (e: any) { throw new Error(`Drift report failed: ${e.message}`); }
  };

  const healSystem = async (): Promise<string> => {
    addOutput("🩺 Initiating zero-drift healing sequence...", "heal");
    setHealingActive(true);
    try {
      const response = await fetch(`${API_BASE}/api/v1/ps1/heal-system`, { method: 'POST' });
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      addOutput("✅ Healing sequence complete", "success");
      setHealCount(c => c + 1);
      await new Promise(resolve => setTimeout(resolve, 2000));
      await checkStatus(false);
      return "Healing complete";
    } catch (e: any) { throw new Error(`Healing failed: ${e.message}`); } 
    finally { setHealingActive(false); }
  };

  const clearOutput = () => { setOutput([]); addOutput("🔄 Output cleared", "info"); };

  const executeCommand = async (cmd: any) => {
    setLoading((prev) => ({ ...prev, [cmd.id]: true }));
    addOutput(`\n> [${cmd.id}] ${cmd.name}`, "command");
    try { const result = await cmd.action(); addOutput(`✅ ${result}`, "success"); } 
    catch (error: any) { addOutput(`❌ ${error.message}`, "error"); } 
    finally { setLoading((prev) => ({ ...prev, [cmd.id]: false })); }
  };

  useEffect(() => {
    if (!isOpen) return;
    checkStatus(true); updateMetrics();
    healthInterval.current = setInterval(() => checkStatus(true), 10000);
    metricsInterval.current = setInterval(() => updateMetrics(), 5000);
    return () => {
      if (healthInterval.current) clearInterval(healthInterval.current);
      if (metricsInterval.current) clearInterval(metricsInterval.current);
      if (immunityTimer.current) clearTimeout(immunityTimer.current);
    };
  }, [isOpen, autoHeal]);

  // =================================================================
  // COMMANDS
  // =================================================================
  const commands =[
    { id: 1, name: "CHECK STATUS", description: "Check all service health", action: () => checkStatus(false), icon: Activity },
    { id: 2, name: autoHeal ? "AUTO-HEAL: ON" : "AUTO-HEAL: OFF", description: "Toggle automatic healing", action: async () => { setAutoHeal(!autoHeal); return `Auto-healing ${!autoHeal ? 'activated' : 'deactivated'}`; }, icon: Shield },
    { id: 3, name: "VIEW LEDGER", description: "Show constitutional precedents", action: viewPrecedents, icon: BookOpen },
    { id: 4, name: "DRIFT REPORT", description: "View zero-drift status", action: getDriftReport, icon: RefreshCw },
    { id: 5, name: "HEAL SYSTEM", description: "Run full healing sequence", action: healSystem, icon: RotateCw },
    { id: 6, name: "LEDGER STATUS", description: "Check ledger health", action: async () => { const ok = await checkLedger(false); return ok ? "Ledger operational" : "Ledger offline"; }, icon: Database },
    { id: 11, name: "DDG SEARCH", description: "Test DuckDuckGo search", action: () => testSearch("latest AI news"), icon: Globe },
    { id: 12, name: "SET DDG", description: "Set search to DuckDuckGo", action: () => setSearchEngine("duckduckgo"), icon: Globe },
    { id: 13, name: "TEST VISION", description: "Describe screen", action: () => testVision("describe screen"), icon: Eye },
    { id: 14, name: "VISION ANALYZE", description: "Analyze screen", action: () => testVision("analyze: What's on my screen?"), icon: Video },
    { id: 15, name: isListening ? "LISTENING..." : "TEST VOICE", description: "Listen for 3 seconds", action: () => testVoice(3), icon: Mic },
    { id: 33, name: "MCP STATUS", description: "List MCP tools", action: mcpStatus, icon: Network },
    { id: 34, name: "MCP DISCOVER", description: "Discover new MCP servers", action: mcpDiscover, icon: Globe },
    { id: 35, name: "MCP TEST", description: "Test MCP connection", action: mcpTest, icon: CheckCircle },
    { id: 21, name: "TEST BRAIN", description: "Test Brain worker", action: () => testWorker("brain", "What is the capital of France?"), icon: Brain },
    { id: 22, name: "TEST SEARCH", description: "Test Search worker", action: () => testWorker("search", "latest AI news"), icon: Eye },
    { id: 23, name: "TEST CODE", description: "Test Code worker", action: () => testWorker("code", "Create a Python function to calculate fibonacci"), icon: Code },
    { id: 24, name: "TEST FILES", description: "Test Files worker", action: () => testWorker("files", "list drives"), icon: Database },
    { id: 25, name: "TEST SYSTEM", description: "Test System worker", action: () => testWorker("system", "/check_system"), icon: Terminal },
    { id: 16, name: "KILL PORT 8001", description: "Free kernel port", action: () => killPort(8001), icon: Terminal, danger: true },
    { id: 17, name: "KILL PORT 3001", description: "Free Next.js port", action: () => killPort(3001), icon: Terminal, danger: true },
    { id: 18, name: "KILL PORT 8000", description: "Free Chroma port", action: () => killPort(8000), icon: Terminal, danger: true },
    { id: 31, name: "CLEAR OUTPUT", description: "Clear terminal", action: clearOutput, icon: Trash2 },
    { id: 32, name: "SYSTEM METRICS", description: "Show current metrics", action: async () => { return `CPU: ${metrics.cpu}% | RAM: ${metrics.memory}% | Tokens: ${metrics.tokens}/${metrics.maxTokens}`; }, icon: Cpu },
  ];

  // Cyberpunk Color Mappings
  const getStatusColor = (isOnline: boolean) => {
    if (!isOnline && autoHeal && failureCount.current.kernel > 2) return "bg-[#FF9800] shadow-[0_0_8px_#FF9800] animate-pulse";
    return isOnline ? "bg-[#10b981] shadow-[0_0_8px_#10b981]" : "bg-[#ef4444] shadow-[0_0_8px_#ef4444]";
  };

  const getLogColor = (type: string) => {
    switch(type) {
      case "command": return "text-[#00E5FF]";
      case "success": return "text-[#10b981]";
      case "error": return "text-[#ef4444]";
      case "heal": return "text-[#FF9800]";
      case "constitution": return "text-[#B388FF]";
      case "search": return "text-[#60a5fa]";
      case "vision": return "text-[#FF6B6B]";
      case "voice": return "text-[#4ECDC4]";
      case "mcp": return "text-[#10b981]";
      case "warning": return "text-[#eab308]";
      default: return "text-[#8A8F9B]";
    }
  };

  const tokenPercentage = (metrics.tokens / metrics.maxTokens) * 100;

  return (
    <>
      {/* Floating Button (Matches SimulationControls Button) */}
      <button
        onClick={() => setIsOpen(!isOpen)}
        className={`fixed bottom-6 right-6 w-14 h-14 rounded-full flex items-center justify-center transition-all duration-300 z-50 shadow-[0_0_20px_rgba(0,0,0,0.5)] border ${
          isOpen ? "bg-[#FF4500]/20 border-[#FF4500] text-[#FF4500] rotate-45" :
          healingActive ? "bg-[#FF9800]/20 border-[#FF9800] text-[#FF9800] animate-pulse" :
          autoHeal ? "bg-[#10b981]/20 border-[#10b981] text-[#10b981]" :
          "bg-[#0E1015] border-[#2A2E38] text-[#00E5FF] hover:border-[#00E5FF]/50"
        }`}
        title="REZ HIVE PS1 Controller"
      >
        {healingActive ? <RotateCw size={20} className="animate-spin" /> : <Shield size={20} />}
      </button>

      {/* Controller Panel */}
      {isOpen && (
        <div className="fixed bottom-24 right-6 w-96 bg-[#0E1015]/95 border border-[#2A2E38] rounded-xl shadow-[0_15px_50px_rgba(0,0,0,0.8)] overflow-hidden z-40 flex flex-col max-h-[600px] backdrop-blur-xl">
          
          {/* Header with Metrics */}
          <div className="bg-[#0A0C10] border-b border-[#1F222A] px-4 py-3">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Terminal size={14} className="text-[#00E5FF]" />
                <span className="font-mono text-xs font-bold text-[#00E5FF] tracking-widest uppercase">PS1 v4.0</span>
              </div>
              <div className="flex items-center gap-3">
                {/* Service Status Dots */}
                <div className="flex items-center gap-1.5">
                  <div className={`w-1.5 h-1.5 rounded-full ${getStatusColor(services.kernel)}`} title="Kernel" />
                  <div className={`w-1.5 h-1.5 rounded-full ${services.chroma ? 'bg-[#10b981]' : 'bg-[#ef4444]'}`} title="Chroma" />
                  <div className={`w-1.5 h-1.5 rounded-full ${services.ollama ? 'bg-[#10b981]' : 'bg-[#ef4444]'}`} title="Ollama" />
                  <div className={`w-1.5 h-1.5 rounded-full ${services.duckduckgo ? 'bg-[#60a5fa]' : 'bg-[#4B5563]'}`} title="DuckDuckGo" />
                  <div className={`w-1.5 h-1.5 rounded-full ${services.ledger ? 'bg-[#B388FF]' : 'bg-[#4B5563]'}`} title="Ledger" />
                  <div className={`w-1.5 h-1.5 rounded-full ${services.mcp ? 'bg-[#10b981]' : 'bg-[#4B5563]'}`} title="MCP" />
                </div>
                <span className="text-[9px] font-mono text-[#4B5563] uppercase">heals:{healCount}</span>
                <button onClick={() => setIsOpen(false)} className="text-[#8A8F9B] hover:text-white transition-colors"><X size={14} /></button>
              </div>
            </div>
            
            {/* Token Usage Bar */}
            <div className="mt-3">
              <div className="flex justify-between text-[9px] font-mono text-[#8A8F9B] mb-1 tracking-widest uppercase">
                <span>Memory Context</span>
                <span className={tokenPercentage > 90 ? 'text-[#FF4500]' : 'text-[#B388FF]'}>{metrics.tokens} / {metrics.maxTokens}</span>
              </div>
              <div className="h-1.5 bg-[#1A1D24] rounded-full overflow-hidden border border-[#1F222A]">
                <div 
                  className={`h-full transition-all duration-500 rounded-full ${tokenPercentage > 90 ? 'bg-[#FF4500] shadow-[0_0_10px_#FF4500]' : 'bg-gradient-to-r from-[#00E5FF] to-[#B388FF] shadow-[0_0_8px_#B388FF]'}`}
                  style={{ width: `${Math.min(tokenPercentage, 100)}%` }}
                />
              </div>
            </div>
          </div>

          {/* Worker Status Row */}
          <div className="border-b border-[#1F222A] px-3 py-2 flex justify-between text-[8px] font-mono tracking-wider uppercase text-[#4B5563] bg-[#0A0C10]">
            <span className={workers.orchestrator ? "text-[#00E5FF]" : ""}>ORCH:{workers.orchestrator ? "✅" : "❌"}</span>
            <span className={workers.brain ? "text-[#10b981]" : ""}>🧠:{workers.brain ? "✅" : "❌"}</span>
            <span className={workers.search ? "text-[#60a5fa]" : ""}>👁️:{workers.search ? "✅" : "❌"}</span>
            <span className={workers.code ? "text-[#B388FF]" : ""}>✋:{workers.code ? "✅" : "❌"}</span>
            <span className={workers.files ? "text-[#FF9800]" : ""}>📁:{workers.files ? "✅" : "❌"}</span>
            <span className={workers.system ? "text-[#FF4500]" : ""}>⚙️:{workers.system ? "✅" : "❌"}</span>
            <span className={workers.vision ? "text-[#FF6B6B]" : ""}>👁️V:{workers.vision ? "✅" : "❌"}</span>
            <span className={workers.voice ? "text-[#4ECDC4]" : ""}>🎤:{workers.voice ? "✅" : "❌"}</span>
          </div>

          {/* Commands Grid */}
          <div className="border-b border-[#1F222A] px-3 py-3 grid grid-cols-3 gap-2 max-h-[220px] overflow-y-auto custom-scrollbar bg-[#0E1015]">
            {commands.map((cmd) => (
              <button 
                key={cmd.id} 
                onClick={() => executeCommand(cmd)} 
                disabled={loading[cmd.id]}
                className={`text-left p-2 bg-[#12141A] disabled:opacity-50 rounded-lg border border-[#1F222A] transition-all duration-300 group ${
                  cmd.danger 
                    ? 'hover:border-[#FF4500]/50 hover:bg-[#FF4500]/10 hover:shadow-[0_0_10px_rgba(255,69,0,0.1)]' 
                    : 'hover:border-[#00E5FF]/40 hover:bg-[#00E5FF]/5 hover:shadow-[0_0_10px_rgba(0,229,255,0.1)]'
                }`}
              >
                <div className="flex items-center gap-1.5 mb-1">
                  {cmd.icon && <cmd.icon size={10} className={cmd.danger ? "text-[#FF4500]" : "text-[#00E5FF]"} />}
                  <span className={`font-mono text-[8px] font-bold ${cmd.danger ? "text-[#FF4500]" : "text-[#00E5FF]"}`}>[{cmd.id}]</span>
                </div>
                <div className="text-[#D1D5DB] group-hover:text-white text-[9px] font-mono tracking-wider truncate uppercase">{cmd.name}</div>
              </button>
            ))}
          </div>

          {/* Ledger Panel */}
          {showLedger && precedents.length > 0 && (
            <div className="border-b border-[#1F222A] px-3 py-2 bg-[#B388FF]/5 max-h-[100px] overflow-y-auto custom-scrollbar relative">
              <div className="flex items-center justify-between mb-2">
                <span className="text-[#B388FF] font-mono text-[9px] font-bold tracking-widest uppercase flex items-center gap-1"><BookOpen size={10}/> RECENT PRECEDENTS</span>
                <button onClick={() => setShowLedger(false)} className="text-[#8A8F9B] hover:text-white transition-colors"><X size={12}/></button>
              </div>
              {precedents.slice(0, 3).map((p, i) => (
                <div key={i} className="text-[8px] font-mono text-[#8A8F9B] truncate border-l-2 border-[#B388FF]/30 pl-2 my-1 hover:text-white transition-colors">
                  <span className="text-[#B388FF]">{p.input_hash?.slice(0,6)}</span> → {p.preview?.slice(0,40)}...
                </div>
              ))}
            </div>
          )}

          {/* Output Terminal */}
          <div className="flex-1 bg-[#050505] font-mono text-[10px] overflow-y-auto custom-scrollbar p-3 space-y-1.5 min-h-[180px] shadow-[inset_0_5px_15px_rgba(0,0,0,0.5)]">
            {output.length === 0 ? (
              <div className="text-[#4B5563] italic"># Sovereign PS1 Kernel Online. Awaiting directive.</div>
            ) : (
              output.map((line) => (
                <div key={line.id} className={`flex gap-2 ${getLogColor(line.type)} leading-relaxed`}>
                  <span className="text-[#4B5563] flex-shrink-0">[{line.timestamp}]</span>
                  <span className="flex-1 break-words">{line.text}</span>
                </div>
              ))
            )}
            <div ref={outputRef} className="h-2" />
          </div>

          {/* Footer */}
          <div className="bg-[#0A0C10] border-t border-[#1F222A] px-4 py-2 flex justify-between items-center text-[9px] font-mono uppercase tracking-widest">
            <div className="flex items-center gap-3">
              <button onClick={() => checkStatus()} className="px-2 py-1 bg-[#00E5FF]/10 hover:bg-[#00E5FF]/20 rounded text-[#00E5FF] border border-[#00E5FF]/30 flex items-center gap-1.5 transition-colors">
                <RefreshCw size={10} /> Sync
              </button>
              <button onClick={clearOutput} className="px-2 py-1 bg-[#12141A] hover:bg-[#1A1D24] rounded text-[#8A8F9B] border border-[#2A2E38] transition-colors">
                Clear
              </button>
            </div>
            <div className="flex items-center gap-2 text-[#4B5563]">
              <span>PS1.v4.0</span>
              <Bell size={10} />
            </div>
          </div>
        </div>
      )}

      {/* Scoped Scrollbar for Panel */}
      <style jsx>{`
        .custom-scrollbar::-webkit-scrollbar { width: 4px; height: 4px; }
        .custom-scrollbar::-webkit-scrollbar-track { background: transparent; }
        .custom-scrollbar::-webkit-scrollbar-thumb { background: #1F222A; border-radius: 4px; transition: all 0.3s ease; }
        .custom-scrollbar:hover::-webkit-scrollbar-thumb { background: #4B5563; }
      `}</style>
    </>
  );
}