import { useState } from 'react';
import {
  ShieldCheck,
  User,
  Lock,
  ArrowRight,
  Activity,
  Pill,
  HeartPulse,
  AlertTriangle,
  Eye,
  EyeOff,
  Fingerprint,
  CheckCircle2,
  Stethoscope,
  Building2,
  Users
} from 'lucide-react';

const TEST_ACCOUNTS = [
  { tc: '89021458935', role: 'doctor', label: 'Doktor' },
  { tc: '35678298736', role: 'pharmacist', label: 'Eczacı' },
  { tc: '12345678901', role: 'patient', label: 'Hasta' },
];

export default function Login({ onLoginSuccess }) {
  const [tcNo, setTcNo] = useState('');
  const [password, setPassword] = useState('');
  // YENİ: Seçilen Rol State'i (Varsayılan: patient)
  const [selectedRole, setSelectedRole] = useState('patient');
  
  const [showPassword, setShowPassword] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');

  const handleLogin = async (e) => {
    e.preventDefault();
    setError('');

    if (tcNo.length < 11) {
      setError('Lütfen 11 haneli T.C. Kimlik numaranızı girin.');
      return;
    }

    setIsLoading(true);

    try {
      // Backend'e hem TC, şifre hem de seçilen rolü gönderiyoruz
      const response = await fetch('http://localhost:8000/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ tc_no: tcNo, password, role: selectedRole }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Giriş bilgileri veya yetki hatalı.');
      }

      const data = await response.json();
      if (onLoginSuccess) {
        onLoginSuccess(data.role, data.user_data);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Sunucuya bağlanılamadı.');
    } finally {
      setIsLoading(false);
    }
  };

  const fillTestAccount = (tc, role) => {
    setTcNo(tc);
    setSelectedRole(role);
    setPassword('test1234');
    setError('');
  };

  const panelItems = [
    { icon: Activity, label: 'Hekim Paneli', tc: '89021458935', role: 'doctor' },
    { icon: Pill, label: 'Eczacı Paneli', tc: '35678298736', role: 'pharmacist' },
    { icon: HeartPulse, label: 'Hasta Portalı', tc: '12345678901', role: 'patient' },
  ];

  return (
    <div className="relative min-h-screen flex items-center justify-center bg-slate-50 font-sans p-4 overflow-hidden">
      {/* Arka plan efektleri */}
      <div className="absolute inset-0 z-0 pointer-events-none">
        <div className="absolute -top-32 -left-32 w-[28rem] h-[28rem] bg-sky-200/40 rounded-full blur-3xl animate-pulse-slow" />
        <div className="absolute top-1/3 -right-24 w-[32rem] h-[32rem] bg-cyan-200/30 rounded-full blur-3xl animate-pulse-slower" />
        <div className="absolute -bottom-40 left-1/4 w-[30rem] h-[30rem] bg-blue-200/30 rounded-full blur-3xl" />
        <div
          className="absolute inset-0 opacity-[0.025]"
          style={{
            backgroundImage:
              'radial-gradient(circle at 1px 1px, #0f172a 1px, transparent 0)',
            backgroundSize: '32px 32px',
          }}
        />
      </div>

      <div className="relative z-10 w-full max-w-5xl bg-white/70 backdrop-blur-2xl rounded-[2rem] shadow-[0_20px_70px_-15px_rgba(2,132,199,0.25)] overflow-hidden flex flex-col md:flex-row border border-white/80">
        
        {/* Sol Panel - Mavi Alan */}
        <div className="relative w-full md:w-5/12 bg-gradient-to-br from-sky-700 via-sky-800 to-blue-900 p-10 text-white flex flex-col justify-between overflow-hidden">
          <div className="absolute -right-16 -bottom-16 w-64 h-64 bg-white/10 rounded-full blur-2xl" />
          <div className="absolute -top-20 -left-10 w-52 h-52 bg-cyan-400/10 rounded-full blur-2xl" />
          
          <div className="relative">
            <div className="flex items-center gap-3 mb-10">
              <div className="flex items-center justify-center w-12 h-12 bg-white/15 rounded-xl backdrop-blur-sm border border-white/25 shadow-lg">
                <ShieldCheck className="w-7 h-7 text-white" />
              </div>
              <div>
                <h1 className="text-2xl font-bold tracking-tight">DrugSense</h1>
                <p className="text-sky-200/80 text-xs font-medium tracking-wide">
                  Klinik Karar Destek Sistemi
                </p>
              </div>
            </div>

            <h2 className="text-[1.65rem] font-semibold mb-4 leading-tight">
              Yapay Zeka ile <br />
              Daha Güvenli Reçeteler.
            </h2>
            <p className="text-sky-100/80 text-sm leading-relaxed max-w-xs">
              Hekimler, eczacılar ve hastalar için entegre edilmiş akıllı ilaç
              etkileşim ve güvenlik duvarı.
            </p>
          </div>

          <div className="relative mt-12 space-y-3">
            {panelItems.map(({ icon: Icon, label, tc, role }) => (
              <button
                key={label}
                type="button"
                onClick={() => fillTestAccount(tc, role)}
                className="group flex items-center gap-3 text-sm text-sky-100/90 transition-all hover:text-white hover:translate-x-1 w-full text-left focus:outline-none"
              >
                <div className="flex items-center justify-center w-9 h-9 rounded-lg bg-white/10 border border-white/10 group-hover:bg-white/20 transition-colors">
                  <Icon className="w-4.5 h-4.5 text-sky-300" />
                </div>
                <span className="font-medium">{label}</span>
              </button>
            ))}
          </div>
        </div>

        {/* Sağ Panel - Form Alanı */}
        <div className="relative w-full md:w-7/12 p-8 sm:p-12 lg:p-14 bg-white flex flex-col justify-center">
          <div className="max-w-sm mx-auto w-full">
            <div className="mb-6">
              <span className="inline-flex items-center gap-1.5 px-2.5 py-1 mb-4 rounded-full bg-sky-50 border border-sky-100 text-[11px] font-semibold text-sky-700 uppercase tracking-wide">
                <Fingerprint className="w-3.5 h-3.5" />
                Güvenli Giriş
              </span>
              <h3 className="text-2xl font-bold text-slate-800 mb-1.5">
                Sisteme Giriş Yapın
              </h3>
              <p className="text-sm text-slate-500">
                T.C. Kimlik numaranız ve şifreniz ile portalınıza erişin.
              </p>
            </div>

            <form onSubmit={handleLogin} className="space-y-4">
              
              {/* YENİ: Giriş Rolü / Vasıf Seçimi */}
              <div>
                <label className="block text-[11px] font-semibold text-slate-500 mb-1.5 uppercase tracking-wider">
                  Giriş Vasıf / Rolü
                </label>
                <div className="grid grid-cols-3 gap-2">
                  <button
                    type="button"
                    onClick={() => setSelectedRole('doctor')}
                    className={`py-2 px-3 text-xs font-bold rounded-xl border transition-all ${
                      selectedRole === 'doctor'
                        ? 'bg-sky-600 text-white border-sky-600 shadow-sm'
                        : 'bg-slate-50 text-slate-600 border-slate-200 hover:bg-slate-100'
                    }`}
                  >
                    Doktor
                  </button>
                  <button
                    type="button"
                    onClick={() => setSelectedRole('pharmacist')}
                    className={`py-2 px-3 text-xs font-bold rounded-xl border transition-all ${
                      selectedRole === 'pharmacist'
                        ? 'bg-sky-600 text-white border-sky-600 shadow-sm'
                        : 'bg-slate-50 text-slate-600 border-slate-200 hover:bg-slate-100'
                    }`}
                  >
                    Eczacı
                  </button>
                  <button
                    type="button"
                    onClick={() => setSelectedRole('patient')}
                    className={`py-2 px-3 text-xs font-bold rounded-xl border transition-all ${
                      selectedRole === 'patient'
                        ? 'bg-sky-600 text-white border-sky-600 shadow-sm'
                        : 'bg-slate-50 text-slate-600 border-slate-200 hover:bg-slate-100'
                    }`}
                  >
                    Hasta
                  </button>
                </div>
              </div>

              {/* TC No */}
              <div>
                <label className="block text-[11px] font-semibold text-slate-500 mb-1.5 uppercase tracking-wider">
                  T.C. Kimlik Numarası
                </label>
                <div className="relative group">
                  <User className="absolute left-3.5 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-400 group-focus-within:text-sky-600 transition-colors" />
                  <input
                    type="text"
                    inputMode="numeric"
                    maxLength={11}
                    value={tcNo}
                    onChange={(e) => setTcNo(e.target.value.replace(/\D/g, ''))}
                    placeholder="11 haneli TC numaranız"
                    className="w-full pl-11 pr-4 py-3 bg-slate-50/70 border border-slate-200 rounded-xl text-sm text-slate-800 placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-sky-500/40 focus:border-sky-500 focus:bg-white transition-all"
                  />
                  {tcNo.length === 11 && (
                    <CheckCircle2 className="absolute right-3.5 top-1/2 -translate-y-1/2 w-5 h-5 text-emerald-500" />
                  )}
                </div>
              </div>

              {/* Şifre */}
              <div>
                <div className="flex items-center justify-between mb-1.5">
                  <label className="block text-[11px] font-semibold text-slate-500 uppercase tracking-wider">
                    Şifre
                  </label>
                </div>
                <div className="relative group">
                  <Lock className="absolute left-3.5 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-400 group-focus-within:text-sky-600 transition-colors" />
                  <input
                    type={showPassword ? 'text' : 'password'}
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    placeholder="••••••••"
                    className="w-full pl-11 pr-11 py-3 bg-slate-50/70 border border-slate-200 rounded-xl text-sm text-slate-800 placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-sky-500/40 focus:border-sky-500 focus:bg-white transition-all"
                  />
                  <button
                    type="button"
                    onClick={() => setShowPassword((s) => !s)}
                    className="absolute right-3.5 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600 transition-colors"
                  >
                    {showPassword ? <EyeOff className="w-5 h-5" /> : <Eye className="w-5 h-5" />}
                  </button>
                </div>
              </div>

              {/* Hata Mesajı */}
              {error && (
                <div className="flex items-start gap-2 p-3 bg-rose-50 border border-rose-200/70 rounded-xl text-xs font-medium text-rose-600">
                  <AlertTriangle className="w-4 h-4 shrink-0 mt-0.5" />
                  <span>{error}</span>
                </div>
              )}

              {/* Giriş Butonu */}
              <button
                type="submit"
                disabled={isLoading || tcNo.length < 11 || password.length === 0}
                className="w-full flex items-center justify-center gap-2 bg-sky-600 hover:bg-sky-700 active:scale-[0.99] text-white font-semibold py-3 px-4 rounded-xl shadow-lg shadow-sky-600/25 transition-all disabled:opacity-50 disabled:cursor-not-allowed disabled:hover:bg-sky-600 mt-2"
              >
                {isLoading ? (
                  <>
                    <span className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                    Giriş Yapılıyor...
                  </>
                ) : (
                  <>
                    Giriş Yap
                    <ArrowRight className="w-5 h-5" />
                  </>
                )}
              </button>
            </form>

            {/* Alt Bilgi */}
            <div className="mt-6 pt-5 border-t border-slate-100">
              <p className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider mb-2.5 text-center">
                Test Hesapları
              </p>
              <div className="grid grid-cols-3 gap-2">
                {TEST_ACCOUNTS.map((acc) => (
                  <button
                    key={acc.tc}
                    type="button"
                    onClick={() => fillTestAccount(acc.tc, acc.role)}
                    className="flex flex-col items-center gap-1 px-2 py-2 rounded-xl bg-slate-50 hover:bg-sky-50 border border-slate-200 hover:border-sky-200 transition-all group"
                  >
                    <span className="text-xs font-semibold text-slate-600 group-hover:text-sky-700">
                      {acc.label}
                    </span>
                    <span className="text-[10px] font-mono text-slate-400 group-hover:text-sky-500">
                      {acc.tc.slice(0, 4)}…{acc.tc.slice(-3)}
                    </span>
                  </button>
                ))}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}