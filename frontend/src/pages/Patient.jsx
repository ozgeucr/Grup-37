import { useState, useEffect } from 'react';
import {
  Home,
  FileText,
  Pill,
  HeartPulse,
  CalendarDays,
  Settings,
  Shield,
  Bell,
  LogOut,
  Search,
  ChevronRight,
  Clock,
  AlertTriangle,
  Info,
  CheckCircle2,
  TrendingUp,
  Calendar,
  X,
  Stethoscope,
  Sparkles,
  Activity
} from 'lucide-react';

const navItems = [
  { icon: Home, label: 'Ana Sayfa', active: true },
  { icon: FileText, label: 'Reçetelerim', active: false },
  { icon: Pill, label: 'İlaçlarım', active: false },
  { icon: HeartPulse, label: 'Sağlık Geçmişi', active: false },
  { icon: CalendarDays, label: 'Randevular', active: false },
  { icon: Settings, label: 'Ayarlar', active: false },
];

const metrics = [
  { icon: Pill, label: 'Aktif İlaçlar', value: 'Güncel', sub: 'durum iyi', color: 'text-blue-500', bg: 'bg-blue-50' },
  { icon: AlertTriangle, label: 'Etkileşim Uyarısı', value: '0', sub: 'sorun yok', color: 'text-orange-500', bg: 'bg-orange-50' },
  { icon: Calendar, label: 'Randevu Sistemi', value: 'Yakında', sub: 'aktif olacak', color: 'text-teal-500', bg: 'bg-teal-50' },
  { icon: Activity, label: 'Sağlık Skoru', value: '82', sub: 'iyi seviye', color: 'text-green-500', bg: 'bg-green-50' },
];

const safetyNotes = [
  {
    level: 'DİKKAT',
    levelColor: 'orange',
    icon: AlertTriangle,
    title: 'Sistem Uyarıları Analizi',
    description: 'Şu an için yeni eklenen ilaçlarınızla ilgili yapay zeka arka planda analiz yapmaktadır.',
    advice: 'Beklenmeyen bir yan etki görürseniz lütfen "Yan Etki Bildir" kısmından sisteme kayıt girin.',
  },
  {
    level: 'GÜVENLİ',
    levelColor: 'green',
    icon: CheckCircle2,
    title: 'İlaç saatleriniz uyumlu',
    description: 'Mevcut ilaçlarınızın alım saatleri arasında çakışma veya doz aşımı riski bulunmuyor.',
    advice: 'İlaçlarınızı her gün aynı saatte almaya devam edin.',
  },
];

function StatusBadge({ status, color }) {
  const styles = {
    green: 'bg-green-100 text-green-700 border border-green-200',
    gray: 'bg-gray-100 text-gray-600 border border-gray-200',
    blue: 'bg-blue-100 text-blue-700 border border-blue-200',
    orange: 'bg-orange-100 text-orange-700 border border-orange-200',
  };
  const appliedClass = styles[color] || styles.gray;
  return (
    <span className={`px-2.5 py-1 rounded-full text-xs font-medium ${appliedClass}`}>{status}</span>
  );
}

function DrugTag({ name }) {
  return (
    <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-xs font-medium bg-teal-50 text-teal-700 border border-teal-100">
      <Pill className="w-2.5 h-2.5" />
      {name}
    </span>
  );
}

export default function PatientDashboard({ user, onLogout }) {
  const [activeNav, setActiveNav] = useState(0);
  
  const [patientData, setPatientData] = useState(null);
  const [isLoading, setIsLoading] = useState(true);

  // Yan Etki Bildir Modalı State'leri
  const [showModal, setShowModal] = useState(false);
  const [seDrug, setSeDrug] = useState("");
  const [seSymptoms, setSeSymptoms] = useState("");
  const [seSeverity, setSeSeverity] = useState("Hafif");
  const [isSubmitting, setIsSubmitting] = useState(false);

  const tcNo = user?.tc_no || user?.tc || "";

  // Profil verisini çekme
  useEffect(() => {
    if (!tcNo) {
      setIsLoading(false);
      return;
    }

    fetch(`http://localhost:8000/patient/profile/${tcNo}`)
      .then(response => {
        if (!response.ok) throw new Error("Hasta verisi çekilemedi.");
        return response.json();
      })
      .then(data => {
        setPatientData(data);
        setIsLoading(false);
      })
      .catch(error => {
        console.error("Hata:", error);
        setIsLoading(false);
      });
  }, [tcNo]);

  // Yan Etki Formunu Gönderme İşlemi
  const handleSideEffectSubmit = async (e) => {
    e.preventDefault();
    if (!seDrug || !seSymptoms) {
      alert("Lütfen ilaç ve semptom alanlarını doldurun.");
      return;
    }

    setIsSubmitting(true);
    try {
      const res = await fetch(`http://localhost:8000/patient/report-side-effect`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          patient_tc: tcNo,
          drug_name: seDrug,
          symptoms: seSymptoms,
          severity: seSeverity
        })
      });

      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "Bildirim gönderilemedi");
      
      alert(`✅ ${data.message}\nTakip Numaranız: ${data.report_id}`);
      
      setShowModal(false);
      setSeSymptoms("");
      setSeSeverity("Hafif");
      setSeDrug("");
      
    } catch (err) {
      alert("Hata: " + err.message);
    } finally {
      setIsSubmitting(false);
    }
  };

  const allPrescriptions = patientData 
    ? [...patientData.active_medications, ...patientData.past_medications] 
    : [];

  return (
    <div className="flex h-screen bg-slate-100 font-sans overflow-hidden">
      
      {/* Yan Etki Bildir Modalı */}
      {showModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/50 backdrop-blur-sm p-4">
          <div className="bg-white rounded-2xl shadow-xl w-full max-w-md overflow-hidden animate-in fade-in zoom-in duration-200">
            <div className="px-6 py-4 border-b border-gray-100 flex items-center justify-between bg-orange-50/50">
              <div className="flex items-center gap-2 text-orange-600">
                <AlertTriangle className="w-5 h-5" />
                <h3 className="font-bold">Yan Etki Bildir</h3>
              </div>
              <button onClick={() => setShowModal(false)} className="text-gray-400 hover:text-gray-600 transition-colors">
                <X className="w-5 h-5" />
              </button>
            </div>
            
            <form onSubmit={handleSideEffectSubmit} className="p-6 space-y-4">
              <div>
                <label className="block text-xs font-semibold text-gray-500 uppercase tracking-wide mb-1.5">Şüpheli İlaç</label>
                <select 
                  value={seDrug}
                  onChange={(e) => setSeDrug(e.target.value)}
                  required
                  className="w-full rounded-xl border border-gray-200 bg-gray-50 px-3 py-2.5 text-sm outline-none focus:border-orange-300 focus:ring-2 focus:ring-orange-100 transition-all"
                >
                  <option value="">Lütfen aktif ilaçlarınızdan seçiniz...</option>
                  {patientData?.active_medications?.map((m, i) => (
                    <option key={i} value={m.drug_name}>{m.drug_name}</option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-xs font-semibold text-gray-500 uppercase tracking-wide mb-1.5">Semptomlar</label>
                <textarea 
                  value={seSymptoms}
                  onChange={(e) => setSeSymptoms(e.target.value)}
                  required
                  placeholder="Örn: İlacı aldıktan 1 saat sonra mide bulantısı ve baş dönmesi başladı..."
                  rows="3"
                  className="w-full rounded-xl border border-gray-200 bg-gray-50 px-3 py-2.5 text-sm outline-none focus:border-orange-300 focus:ring-2 focus:ring-orange-100 transition-all resize-none"
                ></textarea>
              </div>

              <div>
                <label className="block text-xs font-semibold text-gray-500 uppercase tracking-wide mb-1.5">Şiddet Derecesi</label>
                <select 
                  value={seSeverity}
                  onChange={(e) => setSeSeverity(e.target.value)}
                  className="w-full rounded-xl border border-gray-200 bg-gray-50 px-3 py-2.5 text-sm outline-none focus:border-orange-300 focus:ring-2 focus:ring-orange-100 transition-all"
                >
                  <option value="Hafif">Hafif (Günlük hayatı etkilemiyor)</option>
                  <option value="Orta">Orta (Rahatsız edici, işgücü kaybı)</option>
                  <option value="Şiddetli">Şiddetli (Tıbbi müdahale gerektiriyor)</option>
                </select>
              </div>

              <div className="pt-2 flex gap-3">
                <button 
                  type="button"
                  onClick={() => setShowModal(false)}
                  className="flex-1 px-4 py-2.5 rounded-xl border border-gray-200 text-sm font-semibold text-gray-600 hover:bg-gray-50 transition-colors"
                >
                  İptal
                </button>
                <button 
                  type="submit"
                  disabled={isSubmitting}
                  className="flex-1 px-4 py-2.5 rounded-xl bg-orange-500 text-sm font-semibold text-white hover:bg-orange-600 transition-colors disabled:opacity-50 flex items-center justify-center gap-2 shadow-sm shadow-orange-500/30"
                >
                  {isSubmitting ? <span className="animate-spin w-4 h-4 border-2 border-white/40 border-t-white rounded-full" /> : "Kayıt Oluştur"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Sidebar */}
      <aside className="w-56 bg-white flex flex-col border-r border-gray-100 shadow-sm flex-shrink-0">
        <div className="px-5 py-5 border-b border-gray-100">
          <div className="flex items-center gap-2.5">
            <div className="w-9 h-9 rounded-xl bg-blue-600 flex items-center justify-center shadow-sm">
              <Shield className="w-5 h-5 text-white" />
            </div>
            <div>
              <div className="text-sm font-bold text-gray-900 leading-tight">DrugSense</div>
              <div className="text-[10px] text-gray-400">Hasta Portalı</div>
            </div>
          </div>
        </div>

        <nav className="flex-1 px-3 py-4 space-y-0.5">
          {navItems.map((item, i) => {
            const Icon = item.icon;
            const isActive = activeNav === i;
            return (
              <button
                key={i}
                onClick={() => setActiveNav(i)}
                className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-medium transition-all duration-150 ${
                  isActive
                    ? 'bg-blue-600 text-white shadow-sm'
                    : 'text-gray-500 hover:bg-gray-50 hover:text-gray-800'
                }`}
              >
                <Icon className="w-4 h-4 flex-shrink-0" />
                {item.label}
              </button>
            );
          })}
        </nav>

        <div className="px-3 pb-3">
          <p className="text-[10px] font-semibold text-gray-400 uppercase tracking-wider mb-2 px-1">Sağlık Özeti</p>
          <div className="space-y-1.5">
            {metrics.map((m, i) => {
              const Icon = m.icon;
              return (
                <div key={i} className="flex items-center gap-2.5 px-2.5 py-2 rounded-xl bg-gray-50 border border-gray-100">
                  <div className={`w-7 h-7 rounded-lg ${m.bg} flex items-center justify-center flex-shrink-0`}>
                    <Icon className={`w-3.5 h-3.5 ${m.color}`} />
                  </div>
                  <div className="min-w-0">
                    <div className="text-[10px] text-gray-500 leading-tight truncate">{m.label}</div>
                    <div className="flex items-baseline gap-1">
                      <span className="text-sm font-bold text-gray-800">{m.value}</span>
                      <span className="text-[9px] text-gray-400">{m.sub}</span>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </aside>

      {/* Main Content */}
      <div className="flex-1 flex flex-col min-w-0 overflow-hidden">
        {/* Top Header */}
        <header className="bg-white border-b border-gray-100 px-6 py-3 flex items-center justify-between shadow-sm flex-shrink-0">
          <div>
            <h2 className="text-sm font-semibold text-gray-900">
              Merhaba, {isLoading ? 'Yükleniyor...' : patientData?.full_name || user?.full_name || 'Hasta'}
            </h2>
            <p className="text-xs text-gray-400">Bugün kendinizi nasıl hissediyorsunuz? İlaçlarınızı unutmayın.</p>
          </div>
          <div className="flex items-center gap-3">
            <button className="relative w-8 h-8 rounded-lg bg-gray-50 border border-gray-100 flex items-center justify-center hover:bg-gray-100 transition-colors">
              <Bell className="w-3.5 h-3.5 text-gray-500" />
            </button>
            <div className="h-8 w-px bg-gray-100" />
            <div className="flex items-center gap-2.5">
              <div className="w-8 h-8 rounded-full bg-blue-600 flex items-center justify-center text-white text-xs font-bold">
                {(patientData?.full_name || user?.full_name || 'P').charAt(0)}
              </div>
              <div>
                <div className="text-xs font-semibold text-gray-900 leading-tight">
                  {patientData?.full_name || user?.full_name || 'Kullanıcı'}
                </div>
                <div className="text-[10px] text-gray-400">
                  {patientData?.age ? `${patientData.age} yaş` : ''} TC: {tcNo || 'Belirtilmedi'}
                </div>
              </div>
            </div>
            <button onClick={onLogout} className="flex items-center gap-1.5 bg-blue-600 text-white px-3 py-1.5 rounded-lg text-xs font-semibold hover:bg-blue-700 transition-colors ml-1">
              <LogOut className="w-3 h-3" />
              Çıkış
            </button>
          </div>
        </header>

        {/* Content */}
        <div className="flex-1 overflow-auto p-6">
          <div className="mb-5 flex items-center justify-between">
            <div>
              <h1 className="text-xl font-bold text-gray-900">Sağlık Panelim</h1>
              <p className="text-sm text-gray-500 mt-0.5">
                İlaçlarınızı, reçetelerinizi ve yapay zeka güvenlik önerilerini buradan takip edin.
              </p>
            </div>
            <button 
              onClick={() => setShowModal(true)}
              className="flex items-center gap-1.5 bg-orange-500 text-white px-3.5 py-2 rounded-lg text-xs font-semibold hover:bg-orange-600 transition-colors shadow-sm"
            >
              <AlertTriangle className="w-3.5 h-3.5" />
              Yan Etki Bildir
            </button>
          </div>

          <div className="flex gap-5">
            {/* Left Column */}
            <div className="flex-1 min-w-0 space-y-5">
              
              {/* Kullandığım İlaçlar */}
              <div className="bg-white rounded-2xl border border-gray-100 shadow-sm overflow-hidden">
                <div className="px-5 py-4 border-b border-gray-100 flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <div className="w-7 h-7 rounded-lg bg-blue-50 flex items-center justify-center">
                      <Pill className="w-3.5 h-3.5 text-blue-600" />
                    </div>
                    <div>
                      <h3 className="text-sm font-bold text-gray-900">Kullandığım İlaçlar (Aktif)</h3>
                      <p className="text-[11px] text-gray-400 mt-0.5">
                        {patientData?.active_medications?.length || 0} aktif ilaç bulunuyor
                      </p>
                    </div>
                  </div>
                </div>

                <div className="divide-y divide-gray-50">
                  {isLoading ? (
                    <div className="px-5 py-6 text-center text-sm text-gray-500">İlaç bilgileri yükleniyor...</div>
                  ) : patientData?.active_medications?.length === 0 ? (
                    <div className="px-5 py-6 text-center text-sm text-gray-500">Aktif ilaç bulunamadı.</div>
                  ) : (
                    patientData?.active_medications.map((m, i) => (
                      <div key={i} className="px-5 py-3.5 flex items-start gap-3 hover:bg-blue-50/30 transition-colors">
                        <div className="w-9 h-9 rounded-xl bg-blue-50 flex items-center justify-center flex-shrink-0">
                          <Pill className="w-4 h-4 text-blue-600" />
                        </div>
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center gap-2 flex-wrap">
                            <span className="text-sm font-semibold text-gray-900">{m.drug_name}</span>
                            <StatusBadge status="Aktif" color="green" />
                          </div>
                          <p className="text-[11px] text-gray-500 mt-1.5 flex items-start gap-1">
                            <Stethoscope className="w-3 h-3 text-gray-400 flex-shrink-0 mt-0.5" />
                            Yazan Hekim: {m.prescribing_doctor || 'Bilinmiyor'}
                          </p>
                          <p className="text-[11px] text-gray-500 mt-0.5 flex items-start gap-1">
                            <Calendar className="w-3 h-3 text-gray-400 flex-shrink-0 mt-0.5" />
                            Tarih: {new Date(m.prescribed_date).toLocaleDateString('tr-TR')}
                          </p>
                        </div>
                      </div>
                    ))
                  )}
                </div>
              </div>

              {/* Reçete Geçmişi */}
              <div className="bg-white rounded-2xl border border-gray-100 shadow-sm overflow-hidden">
                <div className="px-5 py-4 border-b border-gray-100 flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <div className="w-7 h-7 rounded-lg bg-teal-50 flex items-center justify-center">
                      <FileText className="w-3.5 h-3.5 text-teal-600" />
                    </div>
                    <div>
                      <h3 className="text-sm font-bold text-gray-900">Reçetelerim</h3>
                      <p className="text-[11px] text-gray-400 mt-0.5">Tüm reçete kayıtlarınız</p>
                    </div>
                  </div>
                </div>

                <table className="w-full">
                  <thead>
                    <tr className="bg-gray-50">
                      <th className="text-left px-5 py-2.5 text-[10px] font-semibold text-gray-500 uppercase tracking-wider">Tarih</th>
                      <th className="text-left px-3 py-2.5 text-[10px] font-semibold text-gray-500 uppercase tracking-wider">Doktor</th>
                      <th className="text-left px-3 py-2.5 text-[10px] font-semibold text-gray-500 uppercase tracking-wider">İlaç</th>
                      <th className="text-left px-3 py-2.5 text-[10px] font-semibold text-gray-500 uppercase tracking-wider">Durum</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-50">
                    {isLoading ? (
                      <tr>
                        <td colSpan="4" className="text-center py-6 text-sm text-gray-500">Kayıtlar yükleniyor...</td>
                      </tr>
                    ) : allPrescriptions.length === 0 ? (
                      <tr>
                        <td colSpan="4" className="text-center py-6 text-sm text-gray-500">Reçete geçmişi bulunamadı.</td>
                      </tr>
                    ) : (
                      allPrescriptions.map((p, i) => (
                        <tr key={i} className="hover:bg-blue-50/30 transition-colors cursor-pointer">
                          <td className="px-5 py-3 text-xs font-medium text-gray-700">
                            {new Date(p.prescribed_date).toLocaleDateString('tr-TR')}
                          </td>
                          <td className="px-3 py-3">
                            <div className="flex items-center gap-1.5">
                              <Stethoscope className="w-3 h-3 text-gray-400" />
                              <span className="text-xs text-gray-700">{p.prescribing_doctor || '-'}</span>
                            </div>
                          </td>
                          <td className="px-3 py-3">
                            <DrugTag name={p.drug_name} />
                          </td>
                          <td className="px-3 py-3">
                            <StatusBadge 
                              status={p.status} 
                              color={p.status.toLowerCase() === 'aktif' ? 'green' : 'gray'} 
                            />
                          </td>
                        </tr>
                      ))
                    )}
                  </tbody>
                </table>
              </div>
            </div>

            {/* Right Column: AI Safety Notes & Coming Soon Appointment Card */}
            <div className="w-80 flex-shrink-0 space-y-5">
              <div className="bg-white rounded-2xl border border-gray-100 shadow-sm overflow-hidden">
                <div className="px-4 py-4 border-b border-gray-100 flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <div className="w-7 h-7 rounded-lg bg-blue-600 flex items-center justify-center">
                      <Shield className="w-3.5 h-3.5 text-white" />
                    </div>
                    <div>
                      <div className="text-sm font-bold text-gray-900 leading-tight">YZ Güvenlik Önerileri</div>
                      <div className="text-[10px] text-gray-400">Genel etkileşim uyarıları</div>
                    </div>
                  </div>
                </div>

                <div className="p-3 space-y-3 max-h-[calc(100vh-300px)] overflow-y-auto">
                  {safetyNotes.map((note, i) => {
                    const Icon = note.icon;
                    const levelStyles = {
                      orange: 'bg-orange-500 text-white',
                      green: 'bg-green-500 text-white',
                    };
                    const boxStyles = {
                      orange: 'bg-orange-50 text-orange-800 border border-orange-100',
                      green: 'bg-green-50 text-green-800 border border-green-100',
                    };
                    return (
                      <div key={i} className="rounded-xl border border-gray-100 bg-gray-50 p-3 hover:border-gray-200 transition-colors">
                        <div className="flex items-center justify-between mb-2">
                          <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-bold ${levelStyles[note.levelColor] || 'bg-blue-500 text-white'}`}>
                            <Icon className="w-2.5 h-2.5" />
                            {note.level}
                          </span>
                        </div>
                        <div className="text-xs font-semibold text-gray-900 mb-1.5">{note.title}</div>
                        <p className="text-[11px] text-gray-700 leading-snug mb-2">{note.description}</p>
                        <div className={`rounded-lg p-2 text-[10px] leading-snug ${boxStyles[note.levelColor] || 'bg-gray-100'}`}>
                          {note.advice}
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>

              {/* Randevu Sistemi Çok Yakında Kartı */}
              <div className="bg-gradient-to-br from-indigo-600 to-blue-700 rounded-2xl p-4 shadow-sm text-white relative overflow-hidden">
                <div className="absolute -right-6 -top-6 w-24 h-24 bg-white/10 rounded-full"></div>
                <div className="absolute -right-2 -bottom-8 w-20 h-20 bg-white/10 rounded-full"></div>
                <div className="relative">
                  <div className="flex items-center justify-between mb-3">
                    <div className="flex items-center gap-2">
                      <div className="w-7 h-7 rounded-lg bg-white/20 flex items-center justify-center">
                        <CalendarDays className="w-3.5 h-3.5 text-white" />
                      </div>
                      <span className="text-xs font-semibold">Randevu Sistemi</span>
                    </div>
                    <span className="bg-white/20 px-2 py-0.5 rounded-full text-[10px] font-bold uppercase tracking-wider flex items-center gap-1">
                      <Sparkles className="w-2.5 h-2.5" /> Çok Yakında
                    </span>
                  </div>
                  <div className="text-base font-bold leading-tight">Online Hastane Randevusu</div>
                  <div className="text-xs text-indigo-100 mt-1 leading-relaxed">
                    Hekiminizle kolayca randevu oluşturup reçete takibini tek ekrandan yönetebileceğiniz modül yakında hizmetinizde olacak.
                  </div>
                  <div className="mt-4 pt-3 border-t border-white/15 flex items-center justify-between text-[11px] text-indigo-100 font-medium">
                    <span>Geliştirme Aşamasında</span>
                    <span className="text-white font-bold">v2.0</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}