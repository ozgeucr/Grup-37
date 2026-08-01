import { useState, useEffect } from 'react';
import {
  LayoutDashboard, FileText, Zap, Clock, Settings, Activity, AlertTriangle, Users, 
  Shield, Bell, LogOut, Search, ChevronRight, Pill, 
  ArrowRight, HelpCircle, BookOpen, CheckCircle, XCircle, PlusCircle, CheckCircle2
} from 'lucide-react';

function StatusBadge({ status, color }) {
  const styles = {
    orange: 'bg-orange-100 text-orange-700 border border-orange-200',
    green: 'bg-emerald-100 text-emerald-700 border border-emerald-200',
    red: 'bg-rose-100 text-rose-700 border border-rose-200',
    blue: 'bg-blue-100 text-blue-700 border border-blue-200',
    gray: 'bg-slate-100 text-slate-600 border border-slate-200',
  };
  const appliedClass = styles[color] || styles.gray;
  return (
    <span className={`px-2.5 py-1 rounded-full text-[10px] uppercase font-bold tracking-wider ${appliedClass}`}>
      {status}
    </span>
  );
}

export default function DoctorDashboard({ user, onLogout }) {
  const [activeNav, setActiveNav] = useState(0);
  
  // Arama ve Hasta State'leri
  const [searchTc, setSearchTc] = useState('12345678901');
  const [patientProfile, setPatientProfile] = useState(null);
  const [patientHistory, setPatientHistory] = useState([]);
  const [pendingSideEffects, setPendingSideEffects] = useState([]); // YENİ: Bekleyen bildirimler
  const [isLoadingPatient, setIsLoadingPatient] = useState(false);
  const [patientError, setPatientError] = useState('');

  // Reçete SEPETİ (Cart) State'leri
  const [prescriptionCart, setPrescriptionCart] = useState([]);
  const [isSavingPrescription, setIsSavingPrescription] = useState(false);

  // İlaç Analiz State'leri
  const [newDrugName, setNewDrugName] = useState('');
  const [aiReport, setAiReport] = useState(null);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [acceptResponsibility, setAcceptResponsibility] = useState(false);
  const [overrideReason, setOverrideReason] = useState('');
  const [analyzeError, setAnalyzeError] = useState('');

  // Doktor İstatistikleri State'i
  const [stats, setStats] = useState({
    active_prescriptions: { value: "0", sub: "+0 bugün" },
    warnings: { value: "0", sub: "0 kritik" },
    scanned_patients: { value: "0", sub: "+0 bu hafta" },
    ai_score: { value: "%0", sub: "AI Engine v3.2" }
  });

  const doctorTc = user?.tc_no || user?.tc || "";
  const doctorName = user?.full_name || user?.name || "Bilinmeyen Hekim";

  const fetchDoctorStats = async () => {
    if (!doctorTc) return;
    try {
      const res = await fetch(`http://localhost:8000/doctor/stats/${doctorTc}`);
      if (res.ok) {
        const data = await res.json();
        setStats(data);
      }
    } catch (error) {
      console.error("İstatistikler alınamadı:", error);
    }
  };

  const handleSearchPatient = async (e) => {
    e?.preventDefault();
    if (searchTc.length !== 11) {
      setPatientError("TC numarası 11 haneli olmalıdır.");
      return;
    }
    
    setIsLoadingPatient(true);
    setPatientError('');
    setAiReport(null);
    setNewDrugName('');
    setPrescriptionCart([]); 

    try {
      const profileRes = await fetch(`http://localhost:8000/patient/profile/${searchTc}`);
      if (!profileRes.ok) throw new Error("Hasta bulunamadı.");
      const profileData = await profileRes.json();
      setPatientProfile(profileData);

      // YENİ: Bekleyen yan etki bildirimlerini çek
      const pendingRes = await fetch(`http://localhost:8000/patient/pending-side-effects/${searchTc}`);
      if (pendingRes.ok) {
        const pendingData = await pendingRes.json();
        setPendingSideEffects(pendingData || []);
      }

      if (doctorTc) {
        const historyRes = await fetch(`http://localhost:8000/doctor/doctor-patient-history/${doctorTc}/${searchTc}`);
        if (historyRes.ok) {
          const historyData = await historyRes.json();
          setPatientHistory(historyData.filtered_prescriptions || []);
        }
      }
    } catch (error) {
      setPatientError(error.message);
      setPatientProfile(null);
      setPatientHistory([]);
      setPendingSideEffects([]);
    } finally {
      setIsLoadingPatient(false);
    }
  };

  // YENİ: Doktorun bildirimi onaylayıp hastaya alerji olarak eklemesi
  const handleApproveSideEffect = async (report) => {
    try {
      const res = await fetch(`http://localhost:8000/doctor/approve-side-effect`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          report_id: report.report_id,
          patient_tc: searchTc,
          allergen_name: report.drug_name,
          severity: report.severity
        })
      });

      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "Onaylama başarısız.");

      alert("✅ " + data.message);
      
      // Listeyi ve profili güncellemek için hastayı tekrar sorgula
      handleSearchPatient();

    } catch (err) {
      alert("Hata: " + err.message);
    }
  };

  const handleAnalyze = async (e) => {
    e.preventDefault();
    if (!patientProfile) {
      setAnalyzeError("Lütfen önce bir hasta arayın.");
      return;
    }
    if (!newDrugName) {
      setAnalyzeError("İlaç adı boş olamaz.");
      return;
    }

    setIsAnalyzing(true);
    setAnalyzeError('');

    try {
      const response = await fetch('http://localhost:8000/doctor/doctor/prescribe-and-analyze', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          patient_id: searchTc,
          doctor_id: doctorTc,
          new_drug_name: newDrugName,
          current_cart: prescriptionCart.map(item => item.drug_name), 
          accept_responsibility: acceptResponsibility,
          override_reason: overrideReason
        })
      });

      const data = await response.json();
      if (!response.ok) throw new Error(data.detail || "Bir hata oluştu.");

      setAiReport(data);
    } catch (err) {
      setAnalyzeError(err.message);
    } finally {
      setIsAnalyzing(false);
    }
  };

  const handleAddToCart = () => {
    if (!aiReport) return;
    setPrescriptionCart([
      ...prescriptionCart,
      {
        drug_name: aiReport.new_drug,
        status: aiReport.overall_status,
        override_reason: overrideReason
      }
    ]);
    
    setAiReport(null);
    setNewDrugName('');
    setOverrideReason('');
    setAcceptResponsibility(false);
  };

  const handleSavePrescription = async () => {
    if (prescriptionCart.length === 0) return;
    setIsSavingPrescription(true);

    try {
      const response = await fetch('http://localhost:8000/doctor/doctor/save-prescription', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          patient_id: searchTc,
          doctor_id: doctorTc,
          drugs: prescriptionCart
        })
      });

      const data = await response.json();
      if (!response.ok) throw new Error(data.detail || "Reçete kaydedilemedi.");

      alert(`✅ ${data.message}\nReçete No: ${data.prescription_id}`);
      
      setPrescriptionCart([]);
      handleSearchPatient();
      fetchDoctorStats();

    } catch (error) {
      alert("Hata: " + error.message);
    } finally {
      setIsSavingPrescription(false);
    }
  };

  useEffect(() => {
    if(searchTc) handleSearchPatient();
    fetchDoctorStats();
  }, []);

  return (
    <div className="flex h-screen bg-slate-50/50 font-sans overflow-hidden">
      
      {/* Sidebar */}
      <aside className="w-64 bg-white flex flex-col border-r border-slate-200 shadow-[2px_0_8px_-4px_rgba(0,0,0,0.1)] flex-shrink-0 z-10">
        <div className="px-6 py-6 border-b border-slate-100">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-blue-600 flex items-center justify-center shadow-lg shadow-blue-600/20">
              <Shield className="w-5 h-5 text-white" />
            </div>
            <div>
              <div className="text-base font-bold text-slate-800 leading-tight">DrugSense</div>
              <div className="text-[11px] font-medium text-slate-400">Klinik Karar Desteği</div>
            </div>
          </div>
        </div>
        
        <nav className="flex-1 px-4 py-6 space-y-1">
          <button onClick={() => setActiveNav(0)} className={`w-full flex items-center gap-3 px-4 py-3 rounded-xl text-sm font-semibold transition-all ${activeNav === 0 ? 'bg-blue-600 text-white shadow-md shadow-blue-600/20' : 'text-slate-500 hover:bg-slate-50 hover:text-slate-700'}`}>
            <LayoutDashboard className="w-4.5 h-4.5" /> Kontrol Paneli
          </button>
          <button onClick={() => setActiveNav(1)} className={`w-full flex items-center gap-3 px-4 py-3 rounded-xl text-sm font-semibold transition-all ${activeNav === 1 ? 'bg-blue-600 text-white shadow-md shadow-blue-600/20' : 'text-slate-500 hover:bg-slate-50 hover:text-slate-700'}`}>
            <FileText className="w-4.5 h-4.5" /> Reçete Modülü
          </button>
        </nav>

        <div className="p-4">
          <div className="bg-gradient-to-br from-blue-50 to-sky-50 rounded-2xl p-4 border border-blue-100/50">
            <div className="flex items-center gap-2 mb-1.5">
              <HelpCircle className="w-4 h-4 text-blue-600" />
              <span className="text-xs font-bold text-blue-900">Yardıma ihtiyacınız var mı?</span>
            </div>
            <p className="text-[11px] text-blue-700/80 mb-3 leading-relaxed">Sistemin nasıl karar verdiğini ve kaynakları inceleyin.</p>
            <button className="w-full bg-white text-blue-600 text-[11px] font-bold py-2 rounded-xl flex items-center justify-center gap-1.5 hover:bg-blue-50 transition-colors shadow-sm">
              <BookOpen className="w-3.5 h-3.5" /> Dokümanları Aç
            </button>
          </div>
        </div>
      </aside>

      {/* Main Content */}
      <div className="flex-1 flex flex-col min-w-0 overflow-hidden">
        
        {/* Header */}
        <header className="bg-white border-b border-slate-200 px-8 py-4 flex items-center justify-between shadow-sm z-0">
          <div>
            <h2 className="text-lg font-bold text-slate-800">Hoş Geldiniz, {doctorName}</h2>
            <p className="text-xs font-medium text-slate-500">Bugünkü hastaların klinik özeti ve uyarıları aşağıdadır.</p>
          </div>
          
          <div className="flex items-center gap-5">
            <form onSubmit={handleSearchPatient} className="relative flex items-center">
              <Search className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4.5 h-4.5 text-slate-400" />
              <input
                type="text"
                maxLength="11"
                value={searchTc}
                onChange={(e) => setSearchTc(e.target.value.replace(/\D/g, ''))}
                placeholder="Hasta TC Ara..."
                className="pl-10 pr-4 py-2.5 text-sm font-medium border border-slate-200 rounded-xl bg-slate-50 focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 focus:bg-white w-72 transition-all"
              />
              <button type="submit" className="absolute right-2 bg-blue-600 hover:bg-blue-700 text-white text-xs font-bold px-3 py-1.5 rounded-lg transition-colors">
                Bul
              </button>
            </form>
            
            <div className="h-8 w-px bg-slate-200" />
            
            <button className="relative p-2 text-slate-400 hover:text-slate-600 transition-colors">
              <Bell className="w-5 h-5" />
              <span className="absolute top-1.5 right-1.5 w-2 h-2 bg-rose-500 rounded-full border border-white" />
            </button>
            
            <button onClick={onLogout} className="flex items-center gap-2 bg-slate-100 text-slate-600 px-4 py-2 rounded-xl text-xs font-bold hover:bg-slate-200 transition-colors">
              <LogOut className="w-4 h-4" /> Çıkış
            </button>
          </div>
        </header>

        {/* Dashboard Body */}
        <div className="flex-1 overflow-auto p-8">
          
          {/* İstatistik Kartları */}
          <div className="grid grid-cols-4 gap-6 mb-8">
            <div className="bg-white rounded-2xl p-5 border border-slate-200 shadow-sm flex items-center gap-4 hover:shadow-md transition-shadow">
              <div className="w-12 h-12 rounded-xl bg-blue-50 flex items-center justify-center flex-shrink-0">
                <Activity className="w-6 h-6 text-blue-500" />
              </div>
              <div>
                <div className="text-xs font-bold text-slate-500 uppercase tracking-wider mb-1">Tüm Reçeteler</div>
                <div className="flex items-baseline gap-2">
                  <span className="text-2xl font-black text-slate-800 leading-none">{stats.active_prescriptions.value}</span>
                  <span className="text-[11px] font-semibold text-slate-400">{stats.active_prescriptions.sub}</span>
                </div>
              </div>
            </div>

            <div className="bg-white rounded-2xl p-5 border border-slate-200 shadow-sm flex items-center gap-4 hover:shadow-md transition-shadow">
              <div className="w-12 h-12 rounded-xl bg-orange-50 flex items-center justify-center flex-shrink-0">
                <AlertTriangle className="w-6 h-6 text-orange-500" />
              </div>
              <div>
                <div className="text-xs font-bold text-slate-500 uppercase tracking-wider mb-1">Etkileşim Uyarıları</div>
                <div className="flex items-baseline gap-2">
                  <span className="text-2xl font-black text-slate-800 leading-none">{stats.warnings.value}</span>
                  <span className="text-[11px] font-semibold text-slate-400">{stats.warnings.sub}</span>
                </div>
              </div>
            </div>

            <div className="bg-white rounded-2xl p-5 border border-slate-200 shadow-sm flex items-center gap-4 hover:shadow-md transition-shadow">
              <div className="w-12 h-12 rounded-xl bg-teal-50 flex items-center justify-center flex-shrink-0">
                <Users className="w-6 h-6 text-teal-500" />
              </div>
              <div>
                <div className="text-xs font-bold text-slate-500 uppercase tracking-wider mb-1">Taranan Hastalar</div>
                <div className="flex items-baseline gap-2">
                  <span className="text-2xl font-black text-slate-800 leading-none">{stats.scanned_patients.value}</span>
                  <span className="text-[11px] font-semibold text-slate-400">{stats.scanned_patients.sub}</span>
                </div>
              </div>
            </div>

            <div className="bg-white rounded-2xl p-5 border border-slate-200 shadow-sm flex items-center gap-4 hover:shadow-md transition-shadow">
              <div className="w-12 h-12 rounded-xl bg-blue-50 flex items-center justify-center flex-shrink-0">
                <Shield className="w-6 h-6 text-blue-600" />
              </div>
              <div>
                <div className="text-xs font-bold text-slate-500 uppercase tracking-wider mb-1">YZ Güven Skoru</div>
                <div className="flex items-baseline gap-2">
                  <span className="text-2xl font-black text-slate-800 leading-none">{stats.ai_score.value}</span>
                  <span className="text-[11px] font-semibold text-slate-400">{stats.ai_score.sub}</span>
                </div>
              </div>
            </div>
          </div>

          <div className="flex gap-6">
            
            {/* SOL KOLON: Akıllı Reçete Oluşturucu */}
            <div className="w-7/12 flex flex-col gap-6">
              
              <div className="bg-white rounded-2xl border border-slate-200 shadow-sm p-7">
                <h3 className="text-lg font-black text-slate-800 flex items-center gap-2 mb-6 pb-4 border-b border-slate-100">
                  <Zap className="text-blue-600 w-5 h-5"/> İlaç Ekle ve Analiz Et
                </h3>

                {patientProfile && (
                  <div className="mb-6 p-4 bg-sky-50 border border-sky-100 rounded-xl flex items-center gap-3">
                    <div className="w-10 h-10 rounded-full bg-sky-200 flex items-center justify-center text-sky-700 font-bold">
                      {patientProfile.full_name.charAt(0)}
                    </div>
                    <div>
                      <p className="text-[10px] text-sky-600 font-bold uppercase tracking-wider">İşlem Yapılan Hasta</p>
                      <p className="text-sm font-bold text-sky-900">{patientProfile.full_name} <span className="text-sky-600/70 font-medium">({patientProfile.tc_no})</span></p>
                    </div>
                  </div>
                )}
                
                <form onSubmit={handleAnalyze} className="space-y-5">
                  <div>
                    <label className="block text-xs font-bold text-slate-500 mb-2 uppercase tracking-wide">İlaç Adı (Ticari İsim Veya Etken Madde)</label>
                    <input
                      type="text"
                      value={newDrugName}
                      onChange={(e) => setNewDrugName(e.target.value)}
                      placeholder="Örn: Coraspin, Majezik, İbuprofen..."
                      className="w-full px-4 py-3.5 border border-slate-300 rounded-xl focus:ring-4 focus:ring-blue-500/10 focus:border-blue-500 outline-none text-sm font-medium transition-all"
                    />
                  </div>

                  {analyzeError && (
                    <div className="bg-rose-50 border border-rose-200 p-5 rounded-xl shadow-sm">
                      <p className="text-sm text-rose-800 font-bold mb-4 flex items-start gap-2.5">
                        <AlertTriangle className="w-5 h-5 flex-shrink-0 mt-0.5" />
                        {analyzeError}
                      </p>
                      
                      {analyzeError.includes('sorumluluk') && (
                        <div className="space-y-4 bg-white p-4 rounded-xl border border-rose-100 shadow-sm">
                          <label className="flex items-start gap-3 text-sm text-slate-700 font-medium cursor-pointer">
                            <input 
                              type="checkbox" 
                              checked={acceptResponsibility}
                              onChange={(e) => setAcceptResponsibility(e.target.checked)}
                              className="w-5 h-5 mt-0.5 text-blue-600 rounded border-slate-300 focus:ring-blue-500" 
                            />
                            Sistemin majör risk uyarısını okudum. Klinik yasal sorumluluğu kabul ediyorum.
                          </label>
                          {acceptResponsibility && (
                            <input
                              type="text"
                              value={overrideReason}
                              onChange={(e) => setOverrideReason(e.target.value)}
                              placeholder="Klinik gerekçenizi yazınız (Zorunlu alan)"
                              className="w-full px-4 py-3 border border-slate-300 rounded-xl text-sm font-medium outline-none focus:border-rose-500 focus:ring-2 focus:ring-rose-500/20"
                              required
                            />
                          )}
                        </div>
                      )}
                    </div>
                  )}

                  <button 
                    type="submit" 
                    disabled={isAnalyzing || !newDrugName || !patientProfile}
                    className="w-full bg-slate-800 hover:bg-slate-900 active:scale-[0.99] text-white font-bold py-4 rounded-xl transition-all disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
                  >
                    {isAnalyzing ? <span className="animate-spin w-5 h-5 border-2 border-white/30 border-t-white rounded-full" /> : <Search className="w-5 h-5" />}
                    Riski Analiz Et
                  </button>
                </form>
              </div>

              {/* YZ Rapor Kartı & Sepete Ekleme */}
              {aiReport && (
                <div className={`rounded-2xl border shadow-sm p-7 animate-in fade-in slide-in-from-bottom-4 duration-500 ${
                  aiReport.overall_status === 'CRITICAL' ? 'bg-rose-50 border-rose-200' :
                  aiReport.overall_status === 'WARNING' ? 'bg-orange-50 border-orange-200' :
                  aiReport.overall_status === 'OVERRIDDEN_BY_DOCTOR' ? 'bg-blue-50 border-blue-200' : 
                  aiReport.overall_status === 'MANUAL_REVIEW' ? 'bg-slate-50 border-slate-200' : 'bg-emerald-50 border-emerald-200'
                }`}>
                  <div className="flex items-center justify-between mb-6 pb-4 border-b border-black/5">
                    <h3 className="text-lg font-black text-slate-800 flex items-center gap-2">
                      <Shield className="w-5 h-5" /> Karar Destek Raporu
                    </h3>
                    
                    <StatusBadge 
                      status={
                        aiReport.overall_status === 'CRITICAL' ? 'RİSKLİ / ENGELLENDİ' : 
                        aiReport.overall_status === 'OVERRIDDEN_BY_DOCTOR' ? 'HEKİM İNİSİYATİFİ' : 
                        aiReport.overall_status === 'WARNING' ? 'DİKKAT' : 
                        aiReport.overall_status === 'MANUAL_REVIEW' ? 'BİLİNMEYEN İLAÇ / MANUEL ONAY' : 'GÜVENLİ'
                      } 
                      color={
                        aiReport.overall_status === 'CRITICAL' ? 'red' : 
                        aiReport.overall_status === 'WARNING' ? 'orange' : 
                        aiReport.overall_status === 'OVERRIDDEN_BY_DOCTOR' ? 'blue' : 
                        aiReport.overall_status === 'MANUAL_REVIEW' ? 'gray' : 'green'
                      } 
                    />
                  </div>
                  
                  <div className="space-y-3 mb-6">
                    {aiReport.suggestions?.map((sugg, i) => (
                      <div key={i} className="flex items-start gap-3 bg-white/60 p-4 rounded-xl text-sm text-slate-800 font-semibold shadow-sm border border-white">
                        <ArrowRight className="w-4.5 h-4.5 mt-0.5 text-slate-400 flex-shrink-0" /> 
                        <span className="leading-relaxed">{sugg}</span>
                      </div>
                    ))}
                  </div>
                  
                  <div className="flex items-center gap-2 text-sm font-black text-slate-800 bg-white/50 p-4 rounded-xl border border-black/5 mb-6">
                    {aiReport.overall_status === 'CRITICAL' ? <XCircle className="w-5 h-5 text-rose-600" /> : 
                     aiReport.overall_status === 'MANUAL_REVIEW' ? <HelpCircle className="w-5 h-5 text-slate-500" /> : <CheckCircle className="w-5 h-5 text-emerald-600" />}
                    Sistem Kararı: <span className="font-semibold">{aiReport.recommendation}</span>
                  </div>

                  <button 
                    onClick={handleAddToCart}
                    className="w-full bg-blue-600 hover:bg-blue-700 active:scale-[0.99] text-white font-bold py-4 rounded-xl transition-all flex items-center justify-center gap-2 shadow-lg shadow-blue-600/25"
                  >
                    <PlusCircle className="w-5 h-5" />
                    İlacı Listeye (Reçeteye) Ekle
                  </button>
                </div>
              )}

              {/* REÇETE SEPETİ */}
              {prescriptionCart.length > 0 && (
                <div className="bg-sky-50/80 rounded-2xl border border-sky-200 shadow-inner p-6 mt-2 animate-in fade-in">
                  <h3 className="text-md font-black text-sky-900 flex items-center gap-2 mb-4">
                    <Pill className="w-5 h-5" /> Oluşturulan Reçete Listesi ({prescriptionCart.length} İlaç)
                  </h3>
                  
                  <ul className="space-y-3 mb-6">
                    {prescriptionCart.map((item, idx) => (
                      <li key={idx} className="flex items-center justify-between bg-white p-4 rounded-xl shadow-sm border border-sky-100">
                        <span className="font-bold text-slate-800 text-sm">{item.drug_name}</span>
                        <StatusBadge 
                          status={
                            item.status === 'CRITICAL' ? 'RİSKLİ' : 
                            item.status === 'OVERRIDDEN_BY_DOCTOR' ? 'HEKİM İNİSİYATİFİ' : 
                            item.status === 'WARNING' ? 'DİKKAT' : 
                            item.status === 'MANUAL_REVIEW' ? 'MANUEL ONAY' : 'GÜVENLİ'
                          } 
                          color={
                            item.status === 'CRITICAL' ? 'red' : 
                            item.status === 'WARNING' ? 'orange' : 
                            item.status === 'OVERRIDDEN_BY_DOCTOR' ? 'blue' : 
                            item.status === 'MANUAL_REVIEW' ? 'gray' : 'green'
                          } 
                        />
                      </li>
                    ))}
                  </ul>

                  <button 
                    onClick={handleSavePrescription}
                    disabled={isSavingPrescription}
                    className="w-full bg-emerald-600 hover:bg-emerald-700 active:scale-[0.99] text-white font-black py-4 rounded-xl transition-all disabled:opacity-50 flex items-center justify-center gap-2 shadow-lg shadow-emerald-600/25"
                  >
                    {isSavingPrescription ? <span className="animate-spin w-5 h-5 border-2 border-white/30 border-t-white rounded-full" /> : <CheckCircle2 className="w-6 h-6" />}
                    Tüm Reçeteyi İmzala ve Tamamla
                  </button>
                </div>
              )}

            </div>

            {/* SAĞ KOLON: Hasta Profili, Bekleyen Onaylar ve Geçmiş Reçeteler */}
            <div className="w-5/12 flex flex-col gap-6">
              
              {isLoadingPatient ? (
                <div className="bg-white p-8 rounded-2xl border border-slate-200 text-center flex flex-col items-center justify-center gap-3">
                  <span className="animate-spin w-8 h-8 border-4 border-blue-600/20 border-t-blue-600 rounded-full" />
                  <span className="text-sm font-bold text-slate-500">Hasta verileri BigQuery'den alınıyor...</span>
                </div>
              ) : patientError ? (
                <div className="bg-rose-50 p-6 rounded-2xl border border-rose-200 text-center font-bold text-rose-600 shadow-sm">{patientError}</div>
              ) : patientProfile ? (
                <>
                  {/* Profil Kartı */}
                  <div className="bg-white rounded-2xl border border-slate-200 shadow-sm p-6 relative overflow-hidden">
                    <div className="absolute top-0 left-0 w-1.5 h-full bg-blue-500" />
                    
                    <div className="flex justify-between items-start mb-6 pl-2">
                      <div>
                        <h3 className="text-xl font-black text-slate-800 mb-1">{patientProfile.full_name}</h3>
                        <p className="text-xs font-semibold text-slate-500 flex items-center gap-2">
                          TC: {patientProfile.tc_no} 
                          <span className="w-1 h-1 rounded-full bg-slate-300" /> 
                          {patientProfile.age} Yaş 
                          <span className="w-1 h-1 rounded-full bg-slate-300" /> 
                          {patientProfile.blood_type} Kan Grubu
                        </p>
                      </div>
                      <span className="px-3 py-1.5 bg-emerald-100 text-emerald-700 text-xs font-black rounded-lg uppercase tracking-wide">Aktif Sigortalı</span>
                    </div>

                    <div className="grid grid-cols-2 gap-4 pl-2">
                      <div className="bg-rose-50/50 p-4 rounded-xl border border-rose-100">
                        <span className="text-[10px] font-black text-rose-500 uppercase tracking-wider mb-2 block">Alerjiler</span>
                        {patientProfile.allergies.length > 0 ? (
                          <ul className="text-sm text-rose-900 list-disc pl-4 font-semibold space-y-1">
                            {patientProfile.allergies.map((a, i) => <li key={i}>{a.allergen_name} ({a.severity})</li>)}
                          </ul>
                        ) : <p className="text-xs font-medium text-slate-400">Kayıtlı alerji yok.</p>}
                      </div>
                      
                      <div className="bg-orange-50/50 p-4 rounded-xl border border-orange-100">
                        <span className="text-[10px] font-black text-orange-500 uppercase tracking-wider mb-2 block">Kronik Hastalıklar</span>
                        {patientProfile.diseases.length > 0 ? (
                          <ul className="text-sm text-orange-900 list-disc pl-4 font-semibold space-y-1">
                            {patientProfile.diseases.map((d, i) => <li key={i}>{d.disease_name}</li>)}
                          </ul>
                        ) : <p className="text-xs font-medium text-slate-400">Kayıtlı hastalık yok.</p>}
                      </div>
                    </div>
                  </div>

                  {/* YENİ: Bekleyen Alerji / Yan Etki Onay Paneli */}
                  {pendingSideEffects.length > 0 && (
                    <div className="bg-amber-50 rounded-2xl border border-amber-200 shadow-sm p-6">
                      <h3 className="text-sm font-black text-amber-900 uppercase tracking-wider mb-3 flex items-center gap-2">
                        <AlertTriangle className="w-4.5 h-4.5 text-amber-600" /> Hastadan Gelen Yan Etki / Alerji Bildirimleri ({pendingSideEffects.length})
                      </h3>
                      <div className="space-y-3">
                        {pendingSideEffects.map((item, idx) => (
                          <div key={idx} className="bg-white p-4 rounded-xl border border-amber-100 shadow-sm flex items-center justify-between gap-3">
                            <div>
                              <p className="text-xs font-bold text-slate-800">Şüpheli İlaç: <span className="text-amber-700">{item.drug_name}</span> ({item.severity})</p>
                              <p className="text-[11px] text-slate-600 mt-1">Semptom: {item.symptoms}</p>
                            </div>
                            <button
                              onClick={() => handleApproveSideEffect(item)}
                              className="bg-emerald-600 hover:bg-emerald-700 text-white text-xs font-bold px-3 py-2 rounded-lg transition-colors flex-shrink-0 shadow-sm"
                            >
                              Onayla & Ekle
                            </button>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Reçete Geçmişi */}
                  <div className="bg-white rounded-2xl border border-slate-200 shadow-sm flex-1 flex flex-col overflow-hidden">
                    <div className="px-6 py-5 border-b border-slate-100 flex justify-between items-center bg-slate-50/50">
                      <h3 className="text-sm font-black text-slate-800 uppercase tracking-wider">Geçmiş Reçeteler</h3>
                      <Clock className="w-4.5 h-4.5 text-slate-400" />
                    </div>
                    
                    <div className="overflow-auto">
                      <table className="w-full text-left">
                        <thead>
                          <tr className="border-b border-slate-100">
                            <th className="px-6 py-3 text-[10px] font-black text-slate-400 uppercase tracking-wider">İlaç Adı</th>
                            <th className="px-6 py-3 text-[10px] font-black text-slate-400 uppercase tracking-wider">Durum</th>
                            <th className="px-6 py-3 text-[10px] font-black text-slate-400 uppercase tracking-wider">Tarih</th>
                          </tr>
                        </thead>
                        <tbody className="divide-y divide-slate-50">
                          {patientHistory.length === 0 ? (
                            <tr><td colSpan="3" className="text-center py-8 text-sm font-semibold text-slate-400">Geçmiş reçete bulunamadı.</td></tr>
                          ) : (
                            patientHistory.map((record, i) => (
                              <tr key={i} className="hover:bg-blue-50/30 transition-colors group">
                                <td className="px-6 py-4 text-xs font-black text-slate-800">{record.drug_name}</td>
                                <td className="px-6 py-4">
                                  <StatusBadge
                                    status={
                                      record.status === 'CRITICAL' ? 'RİSKLİ' :
                                      record.status === 'WARNING' ? 'UYARI' :
                                      record.status === 'OVERRIDDEN_BY_DOCTOR' ? 'HEKİM İNİSİYATİFİ' : 
                                      record.status === 'MANUAL_REVIEW' ? 'MANUEL' : 'GÜVENLİ'
                                    }
                                    color={
                                      record.status === 'CRITICAL' ? 'red' :
                                      record.status === 'WARNING' ? 'orange' :
                                      record.status === 'OVERRIDDEN_BY_DOCTOR' ? 'blue' : 
                                      record.status === 'MANUAL_REVIEW' ? 'gray' : 'green'
                                    }
                                  />
                                </td>
                                <td className="px-6 py-4 text-xs font-semibold text-slate-500 group-hover:text-blue-600 transition-colors">
                                  <div className="flex flex-col">
                                    <span>{new Date(record.created_at).toLocaleDateString('tr-TR')}</span>
                                    <span className="text-[10px] text-blue-500">{record.time_label}</span>
                                  </div>
                                </td>
                              </tr>
                            ))
                          )}
                        </tbody>
                      </table>
                    </div>
                  </div>
                </>
              ) : null}
            </div>

          </div>
        </div>
      </div>
    </div>
  );
}