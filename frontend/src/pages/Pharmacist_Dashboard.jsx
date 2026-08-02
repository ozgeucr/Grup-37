import { useMemo, useState, useEffect } from "react";
import {
  Activity,
  AlertTriangle,
  Bell,
  CheckCircle2,
  ClipboardList,
  Clock,
  Database,
  FileText,
  History,
  Info,
  LogOut,
  Pill,
  Plus,
  Search,
  Settings,
  ShieldCheck,
  Stethoscope,
  Trash2,
  User,
  Users,
  X,
  Zap,
} from "lucide-react";

/* ------------------------------------------------------------------ */
/*  Yardımcı Fonksiyonlar & Bileşenler                                 */
/* ------------------------------------------------------------------ */

const SEVERITY = {
  Kritik: {
    badge: "bg-rose-100 text-rose-700 ring-rose-200",
    dot: "bg-rose-500",
    bar: "bg-rose-500",
    text: "text-rose-600",
    soft: "bg-rose-50 border-rose-200",
  },
  Orta: {
    badge: "bg-amber-100 text-amber-700 ring-amber-200",
    dot: "bg-amber-500",
    bar: "bg-amber-500",
    text: "text-amber-600",
    soft: "bg-amber-50 border-amber-200",
  },
  Güvenli: {
    badge: "bg-emerald-100 text-emerald-700 ring-emerald-200",
    dot: "bg-emerald-500",
    bar: "bg-emerald-500",
    text: "text-emerald-600",
    soft: "bg-emerald-50 border-emerald-200",
  },
};

function SeverityBadge({ level, className = "" }) {
  const s = SEVERITY[level] ?? SEVERITY.Güvenli;
  return (
    <span
      className={`inline-flex items-center gap-1.5 rounded-full px-2.5 py-0.5 text-xs font-semibold ring-1 ring-inset ${s.badge} ${className}`}
    >
      <span className={`h-1.5 w-1.5 rounded-full ${s.dot}`} />
      {level}
    </span>
  );
}

function NavItem({ icon: Icon, label, active, onClick, badge }) {
  return (
    <button
      onClick={onClick}
      className={`group flex w-full items-center gap-3 rounded-xl px-3.5 py-2.5 text-sm font-medium transition-all duration-200 ${
        active
          ? "bg-white text-sky-700 shadow-sm ring-1 ring-sky-100"
          : "text-sky-100/80 hover:bg-white/10 hover:text-white"
      }`}
    >
      <Icon
        className={`h-[18px] w-[18px] ${active ? "text-sky-600" : "text-sky-200/70 group-hover:text-white"}`}
        strokeWidth={2}
      />
      <span className="flex-1 text-left">{label}</span>
      {badge != null && badge > 0 && (
        <span className="rounded-full bg-rose-500 px-1.5 py-0.5 text-[10px] font-bold text-white">
          {badge}
        </span>
      )}
    </button>
  );
}

function StatCard({ icon: Icon, label, value, tone }) {
  const tones = {
    sky: "from-sky-500/10 to-sky-500/5 text-sky-600 ring-sky-100",
    emerald: "from-emerald-500/10 to-emerald-500/5 text-emerald-600 ring-emerald-100",
    amber: "from-amber-500/10 to-amber-500/5 text-amber-600 ring-amber-100",
    rose: "from-rose-500/10 to-rose-500/5 text-rose-600 ring-rose-100",
  };
  return (
    <div className="rounded-2xl border border-white/60 bg-white/70 p-4 shadow-sm backdrop-blur-md">
      <div className="flex items-center justify-between">
        <div>
          <p className="text-xs font-medium text-slate-500">{label}</p>
          <p className="mt-1 text-2xl font-bold tracking-tight text-slate-800">{value}</p>
        </div>
        <div
          className={`flex h-11 w-11 items-center justify-center rounded-xl bg-gradient-to-br ring-1 ${tones[tone]}`}
        >
          <Icon className="h-5 w-5" strokeWidth={2.2} />
        </div>
      </div>
    </div>
  );
}

/* ------------------------------------------------------------------ */
/*  Ana Bileşen (App)                                                  */
/* ------------------------------------------------------------------ */

export default function PharmacistDashboard({ user, onLogout }) {
  const [activeNav, setActiveNav] = useState("panel");
  // TC numarası varsayılanı boş bırakıldı
  const [tcQuery, setTcQuery] = useState(""); 
  const [patient, setPatient] = useState(null);
  const [patientError, setPatientError] = useState("");
  const [searching, setSearching] = useState(false);

  const [manualDrugs, setManualDrugs] = useState([]);
  const [drugInput, setDrugInput] = useState("");

  const [history, setHistory] = useState([]);

  const [activePrescription, setActivePrescription] = useState(null);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [analysis, setAnalysis] = useState({ alerts: [], overall: "Güvenli", recommendation: "" });

  const pharmacistName = user?.name || "Ecz. Ali Kaya";

  const analysisDrugs = useMemo(() => {
    if (manualDrugs.length > 0) return manualDrugs.map((d) => d.name);
    if (activePrescription) return activePrescription.drugs;
    return [];
  }, [manualDrugs, activePrescription]);

  // 1. ADIM: BACKEND'DEN HASTA VE REÇETE SORGULAMA
  async function handleSearchPatient() {
    setPatientError("");
    setPatient(null);
    setActivePrescription(null);
    setManualDrugs([]);
    const q = tcQuery.trim();
    
    if (q.length < 11) {
      setPatientError("Geçerli bir 11 haneli TC Kimlik No giriniz.");
      return;
    }
    
    setSearching(true);
    try {
      const profileRes = await fetch(`http://localhost:8000/patient/profile/${q}`);
      if (!profileRes.ok) throw new Error("Bu TC numarasına ait hasta kaydı bulunamadı.");
      const profileData = await profileRes.json();

      const rxRes = await fetch(`http://localhost:8000/pharmacist/active-prescriptions/${q}`);
      let prescriptionsList = [];
      
      if (rxRes.ok) {
        const rxData = await rxRes.json();
        const groupedRx = {};
        
        rxData.prescriptions.forEach(rx => {
          if (!groupedRx[rx.prescription_id]) {
            groupedRx[rx.prescription_id] = {
              id: rx.prescription_id,
              date: new Date(rx.created_at).toLocaleDateString('tr-TR'),
              doctor: rx.doctor_name,
              department: "Klinik",
              drugs: [],
              status: rx.status,
            };
          }
          groupedRx[rx.prescription_id].drugs.push(rx.drug_name);
        });
        
        prescriptionsList = Object.values(groupedRx);
      }

      setPatient({
        tc: q,
        name: profileData.full_name,
        age: profileData.age,
        gender: profileData.gender || "Belirtilmedi",
        conditions: profileData.diseases.map(d => d.disease_name),
        allergies: profileData.allergies.map(a => a.allergen_name),
        prescriptions: prescriptionsList,
      });

      if (prescriptionsList.length > 0) {
        setActivePrescription(prescriptionsList[0]);
      }

    } catch (err) {
      setPatientError(err.message || "Veri çekilirken bir hata oluştu.");
    } finally {
      setSearching(false);
    }
  }

  // OTOMATİK HASTA SORGULAMASI KALDIRILDI
  useEffect(() => {
    // Component ilk yüklendiğinde otomatik sorgu yapmıyoruz
  }, []);

  // 2. ADIM: BACKEND'den GERÇEK ZAMANLI YZ GÜVENLİK ANALİZİ ÇEKME
  useEffect(() => {
    if (analysisDrugs.length === 0 || !patient) {
      setAnalysis({ alerts: [], overall: "Güvenli", recommendation: "" });
      return;
    }

    async function checkDrugs() {
      setIsAnalyzing(true);
      let allAlerts = [];
      let maxSeverityRank = 1; // 1: Güvenli, 2: Orta, 3: Kritik
      let finalRecommendation = "İlaç güvenle teslim edilebilir.";

      for (const drug of analysisDrugs) {
        try {
          const res = await fetch(`http://localhost:8000/pharmacist/check-safety/${patient.tc}/${drug}`);
          if (!res.ok) continue;
          
          const data = await res.json();
          
          if (data.status === "MANUAL_REVIEW") {
            allAlerts.push({
              severity: "Orta",
              type: "Bilinmeyen İlaç",
              title: drug,
              desc: data.recommendation
            });
            if (maxSeverityRank < 2) maxSeverityRank = 2;
            continue;
          }

          const statRank = data.status === "CRITICAL" ? 3 : data.status === "WARNING" ? 2 : 1;
          
          if (statRank > maxSeverityRank) {
            maxSeverityRank = statRank;
            finalRecommendation = data.recommendation; 
          }

          data.disease_warnings?.forEach(w => {
            allAlerts.push({
              severity: data.status === "CRITICAL" ? "Kritik" : "Orta",
              type: "Hastalık Çatışması",
              title: drug,
              desc: w
            });
          });

          data.food_warnings?.forEach(w => {
            allAlerts.push({
              severity: w.includes("[Major]") ? "Kritik" : "Orta",
              type: "Besin Etkileşimi",
              title: drug,
              desc: w
            });
          });

          data.interactions?.forEach(int => {
            allAlerts.push({
              severity: int.level === "Major" ? "Kritik" : "Orta",
              type: "İlaç Etkileşimi",
              title: `${drug} + ${int.drug}`,
              desc: `${int.drug} ile ${int.level} düzeyinde etkileşim bulundu.`
            });
          });

          data.warnings?.forEach(w => {
            allAlerts.push({
              severity: w.includes("KRİTİK") || w.includes("CRITICAL") ? "Kritik" : "Orta",
              type: "Genel Uyarı",
              title: drug,
              desc: w
            });
          });
        } catch (err) {
          console.error("Analiz hatası:", err);
        }
      }

      const uniqueAlerts = [];
      const seen = new Set();
      for (const a of allAlerts) {
        if (!seen.has(a.desc)) {
          seen.add(a.desc);
          uniqueAlerts.push(a);
        }
      }

      const overallState = maxSeverityRank === 3 ? "Kritik" : maxSeverityRank === 2 ? "Orta" : "Güvenli";

      setAnalysis({
        alerts: uniqueAlerts,
        overall: overallState,
        recommendation: finalRecommendation
      });
      setIsAnalyzing(false);
    }

    checkDrugs();
  }, [analysisDrugs, patient]);

  // Yeni Manuel İlaç Ekleme Fonksiyonu
  function handleAddManualDrug(e) {
    e.preventDefault();
    const name = drugInput.trim();
    if (!name) return;
    
    if (manualDrugs.some((d) => d.name.toLowerCase() === name.toLowerCase())) return;
    
    setManualDrugs((prev) => [...prev, { name: name, class: "Manuel Giriş" }]);
    setDrugInput("");
    setActivePrescription(null);
  }

  function removeManualDrug(name) {
    setManualDrugs((prev) => prev.filter((d) => d.name !== name));
  }

  function selectPrescription(rx) {
    setActivePrescription(rx);
    setManualDrugs([]);
  }

  // 3. ADIM: REÇETEYİ VEYA REÇETESİZ SATIŞI TESLİM ETME LOGİĞİ
  async function logOperation(result) {
    // EĞER RESMİ REÇETE İSE:
    if (activePrescription && activePrescription.id) {
      try {
        const res = await fetch(`http://localhost:8000/pharmacist/dispense-medication/${activePrescription.id}`, { method: 'POST' });
        if (res.ok) {
          setPatient(prev => ({
            ...prev,
            prescriptions: prev.prescriptions.map(p => p.id === activePrescription.id ? { ...p, status: "DISPENSED" } : p)
          }));
          alert("✅ Reçete başarıyla teslim edildi!");
        }
      } catch (err) {
        console.error("Reçete teslim hatası:", err);
      }
    } 
    // EĞER MANUEL (REÇETESİZ OTC) SATIŞ İSE:
    else if (manualDrugs.length > 0) {
      alert("✅ Reçetesiz ilaç teslimatı başarıyla sisteme kaydedildi!");
      setManualDrugs([]); // Teslimattan sonra sepeti temizle
    }

    // Ortak Tarihçe Eklemesi
    const now = new Date();
    const time = `Bugün ${String(now.getHours()).padStart(2, "0")}:${String(now.getMinutes()).padStart(2, "0")}`;
    setHistory((prev) => [
      {
        id: activePrescription ? activePrescription.id : `OP-${Math.floor(2042 + Math.random() * 900)}`,
        patient: patient ? patient.name : "Manuel Giriş",
        tc: patient ? tcQuery : "-",
        time,
        drugs: analysisDrugs.length,
        result,
        source: activePrescription ? "Reçete" : "Manuel",
      },
      ...prev,
    ]);
  }

  const navItemsMenu = [
    { id: "panel", label: "Eczane Paneli", icon: Activity },
    { id: "sorgula", label: "Reçete Sorgula", icon: Search },
    { id: "manuel", label: "Manuel İlaç Kontrolü", icon: Pill },
    { id: "gecmis", label: "Geçmiş İşlemler", icon: History },
    { id: "ayarlar", label: "Ayarlar", icon: Settings },
  ];

  return (
    <div className="min-h-screen bg-gradient-to-br from-sky-50 via-white to-blue-50 font-sans text-slate-800">
      <div className="flex min-h-screen">
        {/* Sidebar */}
        <aside className="sticky top-0 hidden h-screen w-64 shrink-0 flex-col bg-gradient-to-b from-sky-700 via-sky-800 to-blue-900 p-5 lg:flex">
          <div className="flex items-center gap-2.5 px-1">
            <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-white/15 ring-1 ring-white/25 backdrop-blur">
              <ShieldCheck className="h-6 w-6 text-white" strokeWidth={2.2} />
            </div>
            <div>
              <p className="text-base font-bold leading-tight text-white">DrugSense</p>
              <p className="text-[11px] font-medium text-sky-200/80">Klinik Karar Desteği</p>
            </div>
          </div>

          <div className="mt-8 mb-3 px-2 text-[11px] font-semibold uppercase tracking-wider text-sky-300/70">
            Eczane Menüsü
          </div>
          <nav className="flex flex-1 flex-col gap-1.5">
            {navItemsMenu.map((item) => (
              <NavItem
                key={item.id}
                icon={item.icon}
                label={item.label}
                active={activeNav === item.id}
                onClick={() => setActiveNav(item.id)}
                badge={item.id === "sorgula" ? patient?.prescriptions?.filter(p => p.status !== "DISPENSED").length : undefined}
              />
            ))}
          </nav>

          <div className="mt-auto rounded-2xl bg-white/10 p-4 ring-1 ring-white/15 backdrop-blur">
            <div className="flex items-center gap-3">
              <div className="flex h-9 w-9 items-center justify-center rounded-full bg-white/20 text-sm font-bold text-white">
                {pharmacistName.split(" ").map(n => n[0]).join("").slice(0, 2)}
              </div>
              <div className="min-w-0">
                <p className="truncate text-sm font-semibold text-white">{pharmacistName}</p>
                <p className="truncate text-[11px] text-sky-200/80">Merkez Eczanesi</p>
              </div>
            </div>
            <button 
              onClick={onLogout}
              className="mt-3 flex w-full items-center justify-center gap-2 rounded-lg bg-white/10 py-2 text-xs font-medium text-sky-100 transition hover:bg-white/20"
            >
              <LogOut className="h-3.5 w-3.5" />
              Çıkış Yap
            </button>
          </div>
        </aside>

        {/* Main Content */}
        <main className="flex min-w-0 flex-1 flex-col">
          {/* Top header */}
          <header className="sticky top-0 z-20 border-b border-sky-100/70 bg-white/70 backdrop-blur-xl">
            <div className="flex items-center justify-between gap-4 px-5 py-3.5 sm:px-8">
              <div className="flex items-center gap-3">
                <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-sky-600 text-white shadow-sm shadow-sky-600/30 lg:hidden">
                  <ShieldCheck className="h-5 w-5" />
                </div>
                <div>
                  <h1 className="text-base font-bold text-slate-800 sm:text-lg">
                    Eczacı Paneli <span className="text-sky-600">- Merkez Eczanesi</span>
                  </h1>
                  <p className="hidden text-xs text-slate-500 sm:block">
                    Yapay zeka destekli ilaç güvenliği ve etkileşim kontrolü
                  </p>
                </div>
              </div>
              <div className="flex items-center gap-2.5">
                <button className="relative flex h-10 w-10 items-center justify-center rounded-xl bg-white text-slate-500 ring-1 ring-slate-200 transition hover:bg-slate-50 hover:text-sky-600">
                  <Bell className="h-5 w-5" />
                  <span className="absolute right-2 top-2 h-2 w-2 rounded-full bg-rose-500 ring-2 ring-white" />
                </button>
                <button onClick={onLogout} className="flex h-10 w-10 items-center justify-center rounded-xl bg-rose-50 text-rose-600 ring-1 ring-rose-100 transition hover:bg-rose-100" title="Çıkış Yap">
                  <LogOut className="h-5 w-5" />
                </button>
                <div className="hidden items-center gap-2.5 rounded-xl bg-white px-3 py-1.5 ring-1 ring-slate-200 sm:flex">
                  <div className="flex h-8 w-8 items-center justify-center rounded-full bg-sky-100 text-xs font-bold text-sky-700">
                    {pharmacistName.split(" ").map(n => n[0]).join("").slice(0, 2)}
                  </div>
                  <div className="leading-tight">
                    <p className="text-xs font-semibold text-slate-700">{pharmacistName}</p>
                    <p className="text-[11px] text-slate-400">Sorumlu Eczacı</p>
                  </div>
                </div>
              </div>
            </div>
          </header>

          <div className="flex-1 px-5 py-6 sm:px-8">
            {/* Stat row */}
            <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
              <StatCard icon={Activity} label="Bugünkü İşlem" value="14" tone="sky" />
              <StatCard icon={AlertTriangle} label="Kritik Uyarı" value="3" tone="rose" />
              <StatCard icon={ShieldCheck} label="Güvenli Onay" value="9" tone="emerald" />
              <StatCard icon={Clock} label="Bekleyen Reçete" value={patient?.prescriptions?.filter(p => p.status !== "DISPENSED").length || "0"} tone="amber" />
            </div>

            {/* Main grid */}
            <div className="mt-6 grid grid-cols-1 gap-6 xl:grid-cols-12">
              
              <div className="flex flex-col gap-6 xl:col-span-7">
                {/* Patient Search Section */}
                <section className="rounded-2xl border border-white/70 bg-white/70 p-5 shadow-sm backdrop-blur-md">
                  <div className="flex items-center gap-2.5">
                    <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-sky-100 text-sky-600">
                      <Search className="h-5 w-5" />
                    </div>
                    <div>
                      <h2 className="text-sm font-bold text-slate-800">Hasta Reçete Sorgulama</h2>
                      <p className="text-xs text-slate-500">
                        TC Kimlik No ile hastanın reçete geçmişini getirin
                      </p>
                    </div>
                  </div>

                  <div className="mt-4 flex flex-col gap-2.5 sm:flex-row">
                    <div className="relative flex-1">
                      <Users className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" />
                      <input
                        value={tcQuery}
                        onChange={(e) => setTcQuery(e.target.value.replace(/\D/g, "").slice(0, 11))}
                        onKeyDown={(e) => e.key === "Enter" && handleSearchPatient()}
                        placeholder="TC Kimlik No"
                        className="w-full rounded-xl border border-slate-200 bg-white py-2.5 pl-10 pr-3 text-sm text-slate-700 placeholder:text-slate-400 outline-none transition focus:border-sky-400 focus:ring-2 focus:ring-sky-100"
                      />
                    </div>
                    <button
                      onClick={handleSearchPatient}
                      disabled={searching || tcQuery.length < 11}
                      className="flex items-center justify-center gap-2 rounded-xl bg-sky-600 px-5 py-2.5 text-sm font-semibold text-white shadow-sm shadow-sky-600/30 transition hover:bg-sky-700 disabled:opacity-60"
                    >
                      {searching ? (
                        <>
                          <span className="h-4 w-4 animate-spin rounded-full border-2 border-white/40 border-t-white" />
                          Sorgulanıyor
                        </>
                      ) : (
                        <>
                          <Database className="h-4 w-4" />
                          Reçeteleri Getir
                        </>
                      )}
                    </button>
                  </div>

                  {patientError && (
                    <div className="mt-3 flex items-center gap-2 rounded-lg bg-rose-50 px-3 py-2 text-xs font-medium text-rose-600 ring-1 ring-rose-100">
                      <AlertTriangle className="h-4 w-4" />
                      {patientError}
                    </div>
                  )}

                  {/* Patient Info Card */}
                  {patient && (
                    <div className="mt-5 rounded-2xl border border-sky-100 bg-gradient-to-br from-sky-50 to-white p-4">
                      <div className="flex flex-wrap items-start justify-between gap-3">
                        <div className="flex items-center gap-3">
                          <div className="flex h-11 w-11 items-center justify-center rounded-full bg-sky-600 text-sm font-bold text-white">
                            {patient.name.split(" ").map((n) => n[0]).join("")}
                          </div>
                          <div>
                            <p className="text-sm font-bold text-slate-800">{patient.name}</p>
                            <p className="text-xs text-slate-500">
                              {patient.age} yaş · {patient.gender} · TC: {tcQuery}
                            </p>
                          </div>
                        </div>
                        <div className="flex flex-wrap gap-1.5">
                          {patient.conditions.map((c, idx) => (
                            <span key={idx} className="rounded-full bg-white px-2.5 py-0.5 text-[11px] font-medium text-slate-600 ring-1 ring-slate-200">
                              {c.disease_name || c}
                            </span>
                          ))}
                        </div>
                      </div>

                      {patient.allergies.length > 0 && (
                        <div className="mt-3 flex items-center gap-2 rounded-lg bg-rose-50 px-3 py-2 text-xs font-medium text-rose-700 ring-1 ring-rose-100">
                          <AlertTriangle className="h-4 w-4" />
                          Alerjiler: {patient.allergies.join(", ")}
                        </div>
                      )}

                      {/* Prescriptions List */}
                      <div className="mt-4">
                        <p className="mb-2 text-xs font-semibold uppercase tracking-wide text-slate-500">
                          Bekleyen Reçeteler ({patient.prescriptions.filter(p => p.status !== "DISPENSED").length})
                        </p>
                        <div className="flex flex-col gap-2.5">
                          {patient.prescriptions.length === 0 ? (
                            <div className="text-xs text-slate-500 py-2">Hastaya ait bekleyen aktif reçete bulunamadı.</div>
                          ) : (
                            patient.prescriptions.map((rx) => {
                              const isActive = activePrescription?.id === rx.id;
                              const isCompleted = rx.status === "DISPENSED";
                              return (
                                <button
                                  key={rx.id}
                                  onClick={() => selectPrescription(rx)}
                                  className={`rounded-xl border p-3.5 text-left transition ${
                                    isActive
                                      ? "border-sky-300 bg-white ring-2 ring-sky-100"
                                      : "border-slate-200 bg-white/60 hover:border-sky-200 hover:bg-white"
                                  } ${isCompleted ? "opacity-60 bg-slate-50" : ""}`}
                                >
                                  <div className="flex flex-wrap items-center justify-between gap-2">
                                    <div className="flex items-center gap-2.5">
                                      <FileText className="h-4 w-4 text-sky-600" />
                                      <div>
                                        <p className="text-sm font-semibold text-slate-800">
                                          #{rx.id}
                                        </p>
                                        <p className="text-[11px] text-slate-500">
                                          {rx.date} · Hekim: {rx.doctor}
                                        </p>
                                      </div>
                                    </div>
                                    <span
                                      className={`rounded-full px-2.5 py-0.5 text-[11px] font-semibold ${
                                        isCompleted
                                          ? "bg-slate-200 text-slate-700"
                                          : "bg-emerald-100 text-emerald-700"
                                      }`}
                                    >
                                      {isCompleted ? "Teslim Edildi" : "Bekliyor"}
                                    </span>
                                  </div>
                                  <div className="mt-2.5 flex flex-wrap gap-1.5">
                                    {rx.drugs.map((d, idx) => (
                                      <span key={idx} className="rounded-md bg-sky-50 px-2 py-0.5 text-[11px] font-medium text-sky-700 ring-1 ring-sky-100">
                                        {d}
                                      </span>
                                    ))}
                                  </div>
                                </button>
                              );
                            })
                          )}
                        </div>
                      </div>
                    </div>
                  )}
                </section>

                {/* Dinamik Manuel Drug Input Section */}
                <section className="rounded-2xl border border-white/70 bg-white/70 p-5 shadow-sm backdrop-blur-md">
                  <div className="flex items-center gap-2.5">
                    <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-indigo-100 text-indigo-600">
                      <Pill className="h-5 w-5" />
                    </div>
                    <div>
                      <h2 className="text-sm font-bold text-slate-800">Manuel İlaç Kontrolü</h2>
                      <p className="text-xs text-slate-500">
                        Reçetesiz satışlar için doğrudan veritabanı sorgulama
                      </p>
                    </div>
                  </div>

                  <form onSubmit={handleAddManualDrug} className="mt-4 flex gap-2">
                    <div className="relative flex-1">
                      <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" />
                      <input
                        value={drugInput}
                        onChange={(e) => setDrugInput(e.target.value)}
                        placeholder="İlaç adı veya etken madde yazıp Enter'a basın..."
                        className="w-full rounded-xl border border-slate-200 bg-white py-2.5 pl-10 pr-3 text-sm text-slate-700 placeholder:text-slate-400 outline-none transition focus:border-sky-400 focus:ring-2 focus:ring-sky-100"
                      />
                    </div>
                    <button
                      type="submit"
                      disabled={!drugInput.trim()}
                      className="flex items-center justify-center gap-1.5 rounded-xl bg-indigo-600 px-5 py-2.5 text-sm font-semibold text-white shadow-sm shadow-indigo-600/30 transition hover:bg-indigo-700 disabled:opacity-50"
                    >
                      <Plus className="h-4 w-4" />
                      Ekle
                    </button>
                  </form>

                  {manualDrugs.length > 0 ? (
                    <div className="mt-4">
                      <p className="mb-2 text-xs font-semibold uppercase tracking-wide text-slate-500">
                        Seçilen İlaçlar ({manualDrugs.length})
                      </p>
                      <div className="flex flex-col gap-2">
                        {manualDrugs.map((d) => (
                          <div
                            key={d.name}
                            className="flex items-center justify-between rounded-xl border border-slate-200 bg-white px-3.5 py-2.5"
                          >
                            <div className="flex items-center gap-2.5">
                              <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-sky-50 text-sky-600">
                                <Pill className="h-4 w-4" />
                              </div>
                              <div>
                                <p className="text-sm font-semibold text-slate-800">{d.name}</p>
                                <p className="text-[11px] text-slate-400">{d.class}</p>
                              </div>
                            </div>
                            <button
                              onClick={() => removeManualDrug(d.name)}
                              className="flex h-8 w-8 items-center justify-center rounded-lg text-slate-400 transition hover:bg-rose-50 hover:text-rose-500"
                            >
                              <Trash2 className="h-4 w-4" />
                            </button>
                          </div>
                        ))}
                      </div>
                    </div>
                  ) : (
                    <div className="mt-4 flex flex-col items-center justify-center rounded-xl border border-dashed border-slate-200 bg-slate-50/50 px-4 py-8 text-center">
                      <Stethoscope className="h-7 w-7 text-slate-300" />
                      <p className="mt-2 text-xs text-slate-400">
                        Yukarıdaki alana ilaç adı yazarak analize ekleyin.
                      </p>
                    </div>
                  )}
                </section>

                {/* History Section */}
                <section className="rounded-2xl border border-white/70 bg-white/70 p-5 shadow-sm backdrop-blur-md">
                  <div className="flex items-center gap-2.5">
                    <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-slate-100 text-slate-600">
                      <History className="h-5 w-5" />
                    </div>
                    <div>
                      <h2 className="text-sm font-bold text-slate-800">Geçmiş İşlemler</h2>
                      <p className="text-xs text-slate-500">Son güvenlik kontrol kayıtları</p>
                    </div>
                  </div>

                  <div className="mt-4 overflow-x-auto">
                    <table className="w-full text-left text-sm">
                      <thead>
                        <tr className="border-b border-slate-100 text-[11px] font-semibold uppercase tracking-wide text-slate-400">
                          <th className="py-2 pr-3 font-semibold">İşlem</th>
                          <th className="py-2 pr-3 font-semibold">Hasta</th>
                          <th className="py-2 pr-3 font-semibold">İlaç</th>
                          <th className="py-2 pr-3 font-semibold">Kaynak</th>
                          <th className="py-2 pr-3 font-semibold">Saat</th>
                          <th className="py-2 font-semibold">Sonuç</th>
                        </tr>
                      </thead>
                      <tbody>
                        {history.map((h) => (
                          <tr key={h.id} className="border-b border-slate-50 last:border-0 hover:bg-sky-50/40">
                            <td className="py-2.5 pr-3 font-mono text-xs font-semibold text-slate-600">{h.id}</td>
                            <td className="py-2.5 pr-3">
                              <p className="font-medium text-slate-700">{h.patient}</p>
                              <p className="text-[11px] text-slate-400">{h.tc}</p>
                            </td>
                            <td className="py-2.5 pr-3 text-slate-600">{h.drugs} ilaç</td>
                            <td className="py-2.5 pr-3">
                              <span className={`rounded-full px-2 py-0.5 text-[11px] font-medium ${h.source === "Reçete" ? "bg-sky-100 text-sky-700" : "bg-violet-100 text-violet-700"}`}>
                                {h.source}
                              </span>
                            </td>
                            <td className="py-2.5 pr-3 text-xs text-slate-500">{h.time}</td>
                            <td className="py-2.5">
                              <SeverityBadge level={h.result} />
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </section>
              </div>

              {/* AI Safety Checker Column */}
              <div className="xl:col-span-5">
                <section className="sticky top-24 rounded-2xl border border-white/70 bg-white/70 shadow-sm backdrop-blur-md">
                  <div className="flex items-center justify-between gap-3 border-b border-slate-100 p-5">
                    <div className="flex items-center gap-2.5">
                      <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-gradient-to-br from-sky-500 to-blue-600 text-white shadow-sm shadow-sky-500/30">
                        <Zap className="h-5 w-5" />
                      </div>
                      <div>
                        <h2 className="text-sm font-bold text-slate-800">
                          AI Güvenlik & Etkileşim Kontrolü
                        </h2>
                        <p className="text-xs text-slate-500">FastAPI & BigQuery entegrasyonu</p>
                      </div>
                    </div>
                    {isAnalyzing ? (
                      <span className="flex items-center gap-1.5 rounded-full bg-amber-50 px-2.5 py-1 text-[11px] font-semibold text-amber-600 ring-1 ring-amber-100">
                        <span className="h-4 w-4 animate-spin rounded-full border-2 border-amber-600/40 border-t-amber-600" />
                        Analiz Ediliyor
                      </span>
                    ) : (
                      <span className="flex items-center gap-1.5 rounded-full bg-emerald-50 px-2.5 py-1 text-[11px] font-semibold text-emerald-600 ring-1 ring-emerald-100">
                        <span className="h-1.5 w-1.5 animate-pulse rounded-full bg-emerald-500" />
                        Canlı
                      </span>
                    )}
                  </div>

                  <div className="p-5">
                    <div className="mb-4">
                      <p className="mb-2 text-xs font-semibold uppercase tracking-wide text-slate-500">
                        Analiz Edilen İlaçlar ({analysisDrugs.length})
                      </p>
                      {analysisDrugs.length === 0 ? (
                        <div className="flex flex-col items-center justify-center rounded-xl border border-dashed border-slate-200 bg-slate-50/50 px-4 py-6 text-center">
                          <ClipboardList className="h-6 w-6 text-slate-300" />
                          <p className="mt-2 text-xs text-slate-400">
                            Lütfen hasta profilini sorgulayıp bir reçete seçin veya manuel ilaç ekleyin.
                          </p>
                        </div>
                      ) : (
                        <div className="flex flex-wrap gap-1.5">
                          {analysisDrugs.map((d, idx) => (
                            <span key={idx} className="rounded-md bg-sky-50 px-2 py-1 text-[11px] font-medium text-sky-700 ring-1 ring-sky-100">
                              {d}
                            </span>
                          ))}
                        </div>
                      )}
                    </div>

                    {!isAnalyzing && analysisDrugs.length > 0 && (
                      <div className={`mb-4 rounded-2xl border p-4 ${SEVERITY[analysis.overall]?.soft || SEVERITY.Güvenli.soft}`}>
                        <div className="flex items-center justify-between">
                          <div className="flex items-center gap-2.5">
                            {analysis.overall === "Kritik" ? (
                              <AlertTriangle className="h-6 w-6 text-rose-500" />
                            ) : analysis.overall === "Orta" ? (
                              <Info className="h-6 w-6 text-amber-500" />
                            ) : (
                              <CheckCircle2 className="h-6 w-6 text-emerald-500" />
                            )}
                            <div>
                              <p className="text-xs font-medium text-slate-500">Genel Durum</p>
                              <p className="text-lg font-bold text-slate-800">
                                {analysis.overall === "Kritik"
                                  ? "Kritik Risk Tespit Edildi"
                                  : analysis.overall === "Orta"
                                  ? "Orta Düzeyde Risk"
                                  : "Güvenli Kombinasyon"}
                              </p>
                            </div>
                          </div>
                          <SeverityBadge level={analysis.overall} />
                        </div>
                        
                        <div className="mt-3 h-2 w-full overflow-hidden rounded-full bg-slate-100">
                          <div
                            className={`h-full rounded-full transition-all duration-500 ${SEVERITY[analysis.overall]?.bar || SEVERITY.Güvenli.bar}`}
                            style={{
                              width: analysis.overall === "Kritik" ? "92%" : analysis.overall === "Orta" ? "55%" : "18%",
                            }}
                          />
                        </div>
                        <p className="mt-2 text-[11px] font-medium text-slate-600">
                          {analysis.recommendation}
                        </p>
                      </div>
                    )}

                    {!isAnalyzing && analysisDrugs.length > 0 && (
                      <div>
                        <p className="mb-2 text-xs font-semibold uppercase tracking-wide text-slate-500">
                          Detaylı Uyarılar ({analysis.alerts.length})
                        </p>
                        {analysis.alerts.length === 0 ? (
                          <div className="flex items-center gap-2.5 rounded-xl bg-emerald-50 px-3.5 py-3 text-xs font-medium text-emerald-700 ring-1 ring-emerald-100">
                            <CheckCircle2 className="h-4 w-4 shrink-0" />
                            BigQuery kayıtlarında bilinen bir etkileşim veya kontrendikasyon bulunamadı.
                          </div>
                        ) : (
                          <div className="flex max-h-[320px] flex-col gap-2.5 overflow-y-auto pr-1">
                            {analysis.alerts.map((a, i) => (
                              <div key={i} className={`rounded-xl border p-3.5 ${SEVERITY[a.severity]?.soft || SEVERITY.Güvenli.soft}`}>
                                <div className="flex items-start justify-between gap-2">
                                  <div className="flex items-center gap-2">
                                    {a.severity === "Kritik" ? (
                                      <AlertTriangle className="h-4 w-4 text-rose-500" />
                                    ) : a.severity === "Orta" ? (
                                      <Info className="h-4 w-4 text-amber-500" />
                                    ) : (
                                      <CheckCircle2 className="h-4 w-4 text-emerald-500" />
                                    )}
                                    <p className="text-sm font-semibold text-slate-800">{a.title}</p>
                                  </div>
                                  <SeverityBadge level={a.severity} />
                                </div>
                                <span className="mt-1.5 inline-block rounded bg-white/70 px-2 py-0.5 text-[10px] font-medium text-slate-500 ring-1 ring-slate-200">
                                  {a.type}
                                </span>
                                <p className="mt-2 text-xs leading-relaxed text-slate-600">{a.desc}</p>
                              </div>
                            ))}
                          </div>
                        )}
                      </div>
                    )}

                    {/* DÜZELTME: Buton metni dinamik hale getirildi */}
                    {!isAnalyzing && analysisDrugs.length > 0 && (
                      <div className="mt-5 flex gap-2.5">
                        <button
                          onClick={() => logOperation(analysis.overall)}
                          disabled={activePrescription?.status === "DISPENSED"}
                          className="flex flex-1 items-center justify-center gap-2 rounded-xl bg-sky-600 px-4 py-2.5 text-sm font-semibold text-white shadow-sm shadow-sky-600/30 transition hover:bg-sky-700 disabled:opacity-50"
                        >
                          <CheckCircle2 className="h-4 w-4" />
                          {activePrescription 
                            ? (activePrescription.status === "DISPENSED" ? "Zaten Teslim Edildi" : "Reçeteyi Teslim Et (Onayla)") 
                            : "İlacı Teslim Et (Satışı Kaydet)"}
                        </button>
                        <button
                          onClick={() => {
                            setManualDrugs([]);
                            setActivePrescription(null);
                          }}
                          className="flex items-center justify-center gap-2 rounded-xl bg-white px-4 py-2.5 text-sm font-semibold text-slate-600 ring-1 ring-slate-200 transition hover:bg-slate-50"
                        >
                          <X className="h-4 w-4" />
                          Temizle
                        </button>
                      </div>
                    )}
                  </div>
                </section>
              </div>
            </div>
          </div>
        </main>
      </div>
    </div>
  );
}