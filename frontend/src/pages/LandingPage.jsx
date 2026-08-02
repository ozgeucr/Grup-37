import { useState, useEffect } from 'react';
import {
  Activity,
  ShieldCheck,
  Stethoscope,
  Pill,
  Users,
  Ambulance,
  ArrowRight,
  Menu,
  X,
  Brain,
  FileText,
  AlertTriangle,
  Sparkles,
  Lock,
  Zap,
  HeartPulse,
  ChevronRight,
} from 'lucide-react';

const NAV_LINKS = [
  { label: 'Özellikler', href: '#features' },
  { label: 'Kullanıcılar', href: '#audience' },
  { label: 'Platform', href: '#platform' },
  { label: 'Güvenlik', href: '#security' },
];

const FEATURES = [
  {
    icon: FileText,
    title: 'Merkezi Hasta Profilleri',
    description:
      'Aktif ilaçlar, kronik rahatsızlıklar ve etken madde alerjileri kurumlar arası erişilebilen tek bir güvenli, birleşik kayıtta toplanır.',
    accent: 'from-sky-500/20 to-cyan-500/5',
    glow: 'group-hover:shadow-sky-500/20',
    iconColor: 'text-sky-300',
  },
  {
    icon: Brain,
    title: 'Gerçek Zamanlı DDI & Alerji Analizi',
    description:
      'Yapay zeka destekli anlık İlaç-İlaç ve İlaç-Alerji etkileşim tespiti; polifarmasi risklerini hastaya ulaşmadan önce proaktif olarak azaltır.',
    accent: 'from-cyan-500/20 to-teal-500/5',
    glow: 'group-hover:shadow-cyan-500/20',
    iconColor: 'text-cyan-300',
  },
  {
    icon: Sparkles,
    title: 'Akıllı Alternatif Önerileri',
    description:
      'Riskli bir etkileşim tespit edildiği an, güvenli alternatif etken maddeler veya ilaçlar için kanıt temelli proaktif öneriler sunar.',
    accent: 'from-teal-500/20 to-emerald-500/5',
    glow: 'group-hover:shadow-teal-500/20',
    iconColor: 'text-teal-300',
  },
  {
    icon: Lock,
    title: 'Rol Tabanlı Yetkilendirme',
    description:
      'Doktorlar, Eczacılar ve Hastalar için özel güvenli portallar — her rol yalnızca yetkisi ölçüsünde veri ve işlemle karşılaşır.',
    accent: 'from-sky-500/20 to-indigo-500/5',
    glow: 'group-hover:shadow-sky-500/20',
    iconColor: 'text-sky-300',
  },
  {
    icon: Zap,
    title: 'Acil Durum Entegrasyonu',
    description:
      'Ambulanslar ve acil servisler için hızlı tarama erişimi; travma bakımı sırasında kritik alerji ve ilaç geçmişine anında ulaşır.',
    accent: 'from-rose-500/20 to-orange-500/5',
    glow: 'group-hover:shadow-rose-500/20',
    iconColor: 'text-rose-300',
  },
  {
    icon: Activity,
    title: 'Polifarmasi Korkulukları',
    description:
      'Çok ilaçlı tedavilerin sürekli izlenmesi; birikimli risk, tekrarlanan tedaviler ve tehlikeli etken madde örtüşmelerini gerçek zamanlı işaretler.',
    accent: 'from-cyan-500/20 to-sky-500/5',
    glow: 'group-hover:shadow-cyan-500/20',
    iconColor: 'text-cyan-300',
  },
];

const AUDIENCE = [
  {
    icon: Stethoscope,
    role: 'Doktorlar ve Klinik Uzmanlar',
    value: 'Bakım noktasında proaktif risk görünürlüğü sunan güvenli reçete iş akışları.',
    accent: 'text-sky-300',
    ring: 'hover:border-sky-500/40',
  },
  {
    icon: Pill,
    role: 'Eczacılar',
    value: 'Tek görünümde ilaç dağıtımı, alternatif kontrolü ve reçete doğrulaması.',
    accent: 'text-cyan-300',
    ring: 'hover:border-cyan-500/40',
  },
  {
    icon: Users,
    role: 'Hastalar ve Polifarmasi Kullanıcıları',
    value: 'Alerjileri veya karmaşık çok ilaçlı tedavileri olan bireyler; bilgilendirilen ve korunan.',
    accent: 'text-teal-300',
    ring: 'hover:border-teal-500/40',
  },
  {
    icon: Ambulance,
    role: 'Acil Ekipler',
    value: 'Travma ve acil durum senaryolarında paramedikler için ışık hızında kritik veri erişimi.',
    accent: 'text-rose-300',
    ring: 'hover:border-rose-500/40',
  },
];

const STATS = [
  { value: '12M+', label: 'Analiz edilen etkileşim' },
  { value: '%99.98', label: 'Çalışma süresi SLA' },
  { value: '<200ms', label: 'Tarama-sonuç' },
  { value: '340+', label: 'Bağlı kurum' },
];

function Logo() {
  return (
    <div className="flex items-center gap-2.5">
      <div className="relative">
        <div className="absolute inset-0 rounded-xl bg-sky-500/40 blur-md" />
        <div className="relative flex h-9 w-9 items-center justify-center rounded-xl border border-sky-400/30 bg-gradient-to-br from-sky-500/30 to-cyan-500/10">
          <HeartPulse className="h-5 w-5 text-sky-300" strokeWidth={2.2} />
        </div>
      </div>
      <div className="flex flex-col leading-none">
        <span className="text-base font-semibold tracking-tight text-white">
          Drug<span className="text-sky-300">Sense</span>
        </span>
        <span className="text-[10px] font-medium uppercase tracking-[0.2em] text-slate-500">
          Klinik Karar Destek
        </span>
      </div>
    </div>
  );
}

function Navbar({ onEnterPortal, onEmergency }) {
  const [scrolled, setScrolled] = useState(false);
  const [open, setOpen] = useState(false);

  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 20);
    onScroll();
    window.addEventListener('scroll', onScroll);
    return () => window.removeEventListener('scroll', onScroll);
  }, []);

  return (
    <header
      className={`fixed inset-x-0 top-0 z-50 transition-all duration-300 ${
        scrolled
          ? 'border-b border-white/5 bg-slate-950/80 backdrop-blur-xl'
          : 'border-b border-transparent bg-transparent'
      }`}
    >
      <nav className="mx-auto flex max-w-7xl items-center justify-between px-6 py-4 lg:px-8">
        <Logo />
        
        <div className="hidden items-center gap-8 md:flex">
          {NAV_LINKS.map((link) => (
            <a
              key={link.label}
              href={link.href}
              className="text-sm font-medium text-slate-300 transition-colors hover:text-white"
            >
              {link.label}
            </a>
          ))}
        </div>

        <div className="hidden md:flex items-center gap-3">
          {/* YENİ: Acil Durum Butonu */}
          <button
            onClick={onEmergency}
            className="group inline-flex items-center gap-2 rounded-full border border-rose-400/30 bg-rose-500/10 px-5 py-2 text-sm font-semibold text-rose-200 transition-all hover:border-rose-400/60 hover:bg-rose-500/20 hover:text-white"
          >
            <Ambulance className="h-4 w-4" />
            Acil Giriş
          </button>
          
          <button
            onClick={onEnterPortal}
            className="group inline-flex items-center gap-2 rounded-full border border-sky-400/30 bg-sky-500/10 px-5 py-2 text-sm font-semibold text-sky-200 transition-all hover:border-sky-400/60 hover:bg-sky-500/20 hover:text-white"
          >
            Portala Gir
            <ArrowRight className="h-4 w-4 transition-transform group-hover:translate-x-0.5" />
          </button>
        </div>

        <button
          onClick={() => setOpen((v) => !v)}
          className="flex h-9 w-9 items-center justify-center rounded-lg border border-white/10 text-slate-300 md:hidden"
          aria-label="Menüyü aç/kapat"
        >
          {open ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
        </button>
      </nav>

      {/* Mobil Menü */}
      {open && (
        <div className="border-t border-white/5 bg-slate-950/95 px-6 py-4 backdrop-blur-xl md:hidden">
          <div className="flex flex-col gap-3">
            {NAV_LINKS.map((link) => (
              <a
                key={link.label}
                href={link.href}
                onClick={() => setOpen(false)}
                className="text-sm font-medium text-slate-300 hover:text-white"
              >
                {link.label}
              </a>
            ))}
            <div className="mt-4 flex flex-col gap-2">
              <button
                onClick={() => {
                  setOpen(false);
                  onEmergency();
                }}
                className="inline-flex items-center justify-center gap-2 rounded-full border border-rose-400/30 bg-rose-500/10 px-5 py-2.5 text-sm font-semibold text-rose-200"
              >
                <Ambulance className="h-4 w-4" />
                Acil Giriş (Kırmızı Kod)
              </button>
              
              <button
                onClick={() => {
                  setOpen(false);
                  onEnterPortal();
                }}
                className="inline-flex items-center justify-center gap-2 rounded-full border border-sky-400/30 bg-sky-500/10 px-5 py-2.5 text-sm font-semibold text-sky-200"
              >
                Portala Gir
                <ArrowRight className="h-4 w-4" />
              </button>
            </div>
          </div>
        </div>
      )}
    </header>
  );
}

function Hero({ onEnterPortal, onEmergency }) {
  return (
    <section className="relative overflow-hidden pt-36 pb-24 lg:pt-44 lg:pb-32">
      {/* Ambient glow */}
      <div className="pointer-events-none absolute inset-0 -z-10">
        <div className="absolute left-1/2 top-0 h-[500px] w-[700px] -translate-x-1/2 rounded-full bg-sky-600/20 blur-[120px]" />
        <div className="absolute right-[10%] top-1/3 h-[400px] w-[400px] rounded-full bg-cyan-500/15 blur-[120px]" />
        <div className="absolute left-[5%] bottom-0 h-[350px] w-[350px] rounded-full bg-teal-500/10 blur-[120px]" />
      </div>
      {/* Grid overlay */}
      <div
        className="pointer-events-none absolute inset-0 -z-10 opacity-[0.04]"
        style={{
          backgroundImage:
            'linear-gradient(to right, white 1px, transparent 1px), linear-gradient(to bottom, white 1px, transparent 1px)',
          backgroundSize: '56px 56px',
          maskImage: 'radial-gradient(ellipse 80% 60% at 50% 30%, black, transparent)',
        }}
      />

      <div className="mx-auto max-w-7xl px-6 lg:px-8">
        <div className="mx-auto max-w-4xl text-center">
          <div className="mx-auto mb-6 inline-flex items-center gap-2 rounded-full border border-sky-400/20 bg-sky-500/5 px-4 py-1.5 text-xs font-medium text-sky-200">
            <span className="relative flex h-2 w-2">
              <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-sky-400 opacity-75" />
              <span className="relative inline-flex h-2 w-2 rounded-full bg-sky-400" />
            </span>
            Yapay Zeka Destekli Klinik Karar Destek Sistemi
          </div>

          <h1 className="text-balance text-4xl font-semibold leading-[1.1] tracking-tight text-white sm:text-5xl lg:text-6xl">
            Güvenle reçete yazın.
            <br />
            <span className="bg-gradient-to-r from-sky-300 via-cyan-200 to-teal-200 bg-clip-text text-transparent">
              Her etkileşimi yakalayın.
            </span>
          </h1>

          <p className="mx-auto mt-6 max-w-2xl text-pretty text-lg leading-relaxed text-slate-300">
            DrugSense etken madde temelli ilaç etkileşim analizi yapar, alerjik
            reaksiyon risklerini proaktif yönetir ve polifarmasi tehlikelerini önler —
            parçalanmış sağlık verisini doktorlar, eczacılar ve hastalar için tek bir
            akıllı ağda birleştirir.
          </p>

          <div className="mt-10 flex flex-col items-center justify-center gap-4 sm:flex-row">
            <button
              onClick={onEnterPortal}
              className="group relative inline-flex items-center gap-2 overflow-hidden rounded-full bg-gradient-to-r from-sky-500 to-cyan-500 px-8 py-3.5 text-base font-semibold text-slate-950 shadow-lg shadow-sky-500/25 transition-all hover:shadow-xl hover:shadow-sky-500/40 hover:brightness-110"
            >
              <span className="absolute inset-0 -translate-x-full bg-gradient-to-r from-transparent via-white/30 to-transparent transition-transform duration-700 group-hover:translate-x-full" />
              Portala Gir
              <ArrowRight className="h-5 w-5 transition-transform group-hover:translate-x-1" />
            </button>
            
            {/* YENİ: Hero Acil Durum Butonu */}
            <button
              onClick={onEmergency}
              className="group inline-flex items-center gap-2 rounded-full border border-rose-500/40 bg-rose-500/10 px-7 py-3.5 text-base font-medium text-rose-200 backdrop-blur-sm transition-all hover:border-rose-500/60 hover:bg-rose-500/20"
            >
              <Ambulance className="h-4 w-4" />
              Paramedik Acil Erişim
            </button>
          </div>

          {/* Stats strip */}
          <div className="mx-auto mt-16 grid max-w-3xl grid-cols-2 gap-px overflow-hidden rounded-2xl border border-white/5 bg-white/5 sm:grid-cols-4">
            {STATS.map((s) => (
              <div key={s.label} className="bg-slate-950/40 px-4 py-5 text-center">
                <div className="text-2xl font-semibold text-white">{s.value}</div>
                <div className="mt-1 text-xs font-medium text-slate-400">{s.label}</div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </section>
  );
}

function FeatureCard({ feature }) {
  const Icon = feature.icon;
  return (
    <div
      className={`group relative overflow-hidden rounded-2xl border border-white/10 bg-gradient-to-br ${feature.accent} p-6 backdrop-blur-sm transition-all duration-300 hover:-translate-y-1 hover:border-white/20 ${feature.glow} hover:shadow-2xl`}
    >
      <div className="pointer-events-none absolute -right-8 -top-8 h-32 w-32 rounded-full bg-white/5 opacity-0 blur-2xl transition-opacity duration-500 group-hover:opacity-100" />
      <div className="relative">
        <div className="mb-5 inline-flex h-12 w-12 items-center justify-center rounded-xl border border-white/10 bg-slate-950/40">
          <Icon className={`h-6 w-6 ${feature.iconColor}`} strokeWidth={1.8} />
        </div>
        <h3 className="text-lg font-semibold text-white">{feature.title}</h3>
        <p className="mt-2.5 text-sm leading-relaxed text-slate-300">{feature.description}</p>
      </div>
    </div>
  );
}

function Features() {
  return (
    <section id="features" className="relative py-24 lg:py-32">
      <div className="mx-auto max-w-7xl px-6 lg:px-8">
        <div className="mx-auto max-w-2xl text-center">
          <p className="text-sm font-semibold uppercase tracking-[0.2em] text-sky-400">
            Platform Mimarisi
          </p>
          <h2 className="mt-3 text-3xl font-semibold tracking-tight text-white sm:text-4xl">
            Daha güvenli reçetenin altı direği
          </h2>
          <p className="mt-4 text-base leading-relaxed text-slate-400">
            DrugSense'in her katmanı riski daha erken yakalamak, alternatifleri daha
            hızlı yüzeye çıkarmak ve doğru veriyi doğru ellere ulaştırmak için
            tasarlandı.
          </p>
        </div>

        <div className="mt-16 grid gap-5 sm:grid-cols-2 lg:grid-cols-3">
          {FEATURES.map((f) => (
            <FeatureCard key={f.title} feature={f} />
          ))}
        </div>
      </div>
    </section>
  );
}

function AudienceCard({ item }) {
  const Icon = item.icon;
  return (
    <div
      className={`group rounded-2xl border border-white/10 bg-white/[0.03] p-7 backdrop-blur-sm transition-all duration-300 hover:-translate-y-1 hover:bg-white/[0.06] ${item.ring}`}
    >
      <div className="flex items-center gap-4">
        <div className="inline-flex h-12 w-12 items-center justify-center rounded-xl border border-white/10 bg-slate-950/50 transition-transform duration-300 group-hover:scale-110">
          <Icon className={`h-6 w-6 ${item.accent}`} strokeWidth={1.8} />
        </div>
        <h3 className="text-lg font-semibold text-white">{item.role}</h3>
      </div>
      <p className="mt-4 text-sm leading-relaxed text-slate-400">{item.value}</p>
    </div>
  );
}

function Audience() {
  return (
    <section id="audience" className="relative py-24 lg:py-32">
      <div className="pointer-events-none absolute inset-0 -z-10">
        <div className="absolute left-1/2 top-1/2 h-[400px] w-[800px] -translate-x-1/2 -translate-y-1/2 rounded-full bg-cyan-700/10 blur-[120px]" />
      </div>
      <div className="mx-auto max-w-7xl px-6 lg:px-8">
        <div className="mx-auto max-w-2xl text-center">
          <p className="text-sm font-semibold uppercase tracking-[0.2em] text-cyan-400">
            Her Rol İçin Tasarlandı
          </p>
          <h2 className="mt-3 text-3xl font-semibold tracking-tight text-white sm:text-4xl">
            Tek ağ, dört kritik iş akışı
          </h2>
          <p className="mt-4 text-base leading-relaxed text-slate-400">
            Reçete yazan klinisyenden yoldaki paramediğe kadar DrugSense, bakım
            anına göre yüzeyini uyarlar.
          </p>
        </div>

        <div className="mt-16 grid gap-5 sm:grid-cols-2 lg:grid-cols-4">
          {AUDIENCE.map((a) => (
            <AudienceCard key={a.role} item={a} />
          ))}
        </div>
      </div>
    </section>
  );
}

function Platform() {
  const steps = [
    {
      n: '01',
      title: 'Topla',
      desc: 'Hastanın ilaçları, rahatsızlıkları ve alerjileri kurumlar arası tek bir birleşik profile toplanır.',
    },
    {
      n: '02',
      title: 'Analiz Et',
      desc: 'Yapay zeka motoru etken maddeleri çapraz referanslayarak ilaç-ilaç ve ilaç-alerji etkileşimlerini gerçek zamanlı bulur.',
    },
    {
      n: '03',
      title: 'Öner',
      desc: 'Risk tespit edildiğinde güvenli alternatif etken maddeler veya ilaçlar anında yüzeye çıkar.',
    },
    {
      n: '04',
      title: 'Yetkilendir',
      desc: 'Rol tabanlı erişim; doktorların, eczacıların ve hastaların yalnızca görmesi gerekenleri görmesini sağlar.',
    },
  ];

  return (
    <section id="platform" className="relative py-24 lg:py-32">
      <div className="mx-auto max-w-7xl px-6 lg:px-8">
        <div className="mx-auto max-w-2xl text-center">
          <p className="text-sm font-semibold uppercase tracking-[0.2em] text-teal-400">
            Nasıl Çalışır
          </p>
          <h2 className="mt-3 text-3xl font-semibold tracking-tight text-white sm:text-4xl">
            Parçalanmış veriden güvenli reçeteye
          </h2>
        </div>

        <div className="mt-16 grid gap-6 md:grid-cols-2 lg:grid-cols-4">
          {steps.map((s, i) => (
            <div key={s.n} className="relative">
              <div className="rounded-2xl border border-white/10 bg-white/[0.03] p-6 backdrop-blur-sm">
                <div className="flex items-center justify-between">
                  <span className="text-sm font-semibold text-sky-400">{s.n}</span>
                  {i < steps.length - 1 && (
                    <ArrowRight className="hidden h-4 w-4 text-slate-600 lg:block" />
                  )}
                </div>
                <h3 className="mt-4 text-lg font-semibold text-white">{s.title}</h3>
                <p className="mt-2 text-sm leading-relaxed text-slate-400">{s.desc}</p>
              </div>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}

function Security({ onEnterPortal }) {
  return (
    <section id="security" className="relative py-24 lg:py-32">
      <div className="mx-auto max-w-7xl px-6 lg:px-8">
        <div className="relative overflow-hidden rounded-3xl border border-sky-400/20 bg-gradient-to-br from-sky-500/10 via-slate-900/40 to-cyan-500/10 p-10 backdrop-blur-sm lg:p-16">
          <div className="pointer-events-none absolute -right-10 -top-10 h-64 w-64 rounded-full bg-sky-500/20 blur-[100px]" />
          <div className="pointer-events-none absolute -bottom-10 -left-10 h-64 w-64 rounded-full bg-cyan-500/15 blur-[100px]" />
          <div className="relative grid items-center gap-10 lg:grid-cols-2">
            <div>
              <div className="inline-flex h-12 w-12 items-center justify-center rounded-xl border border-sky-400/30 bg-sky-500/10">
                <ShieldCheck className="h-6 w-6 text-sky-300" />
              </div>
              <h2 className="mt-5 text-3xl font-semibold tracking-tight text-white sm:text-4xl">
                Tasarımdan gelen klinik sınıfı güvenlik
              </h2>
              <p className="mt-4 max-w-lg text-base leading-relaxed text-slate-300">
                Rol tabanlı yetkilendirme, şifrelenmiş sağlık kayıtları ve denetlenebilir
                erişim hassas veriyi korur — acil ekipler ise saniyelerin önem taşıdığı
                anlarda ihtiyaç duydukları hızlı erişimi elinde tutar.
              </p>
              <ul className="mt-6 space-y-3">
                {[
                  'Doktorlar, eczacılar ve hastalar için role özel portallar',
                  'Her kayıt için şifreli, denetim günlüklü erişim',
                  'Travma senaryoları için acil hızlı tarama geçişi',
                ].map((t) => (
                  <li key={t} className="flex items-start gap-3 text-sm text-slate-200">
                    <ShieldCheck className="mt-0.5 h-4 w-4 flex-shrink-0 text-sky-400" />
                    {t}
                  </li>
                ))}
              </ul>
              <button
                onClick={onEnterPortal}
                className="group mt-8 inline-flex items-center gap-2 rounded-full bg-gradient-to-r from-sky-500 to-cyan-500 px-7 py-3 text-sm font-semibold text-slate-950 shadow-lg shadow-sky-500/25 transition-all hover:shadow-xl hover:shadow-sky-500/40 hover:brightness-110"
              >
                Portala Gir
                <ArrowRight className="h-4 w-4 transition-transform group-hover:translate-x-1" />
              </button>
            </div>

            <div className="relative">
              <div className="rounded-2xl border border-white/10 bg-slate-950/60 p-6 backdrop-blur-md">
                <div className="flex items-center gap-2 border-b border-white/5 pb-3">
                  <AlertTriangle className="h-4 w-4 text-amber-400" />
                  <span className="text-xs font-semibold uppercase tracking-wider text-slate-400">
                    Canlı Etkileşim Uyarısı
                  </span>
                </div>
                <div className="mt-4 space-y-3">
                  <div className="flex items-center justify-between rounded-lg border border-rose-500/20 bg-rose-500/10 px-3 py-2.5">
                    <span className="text-sm text-rose-200">Warfarin + Ibuprofen</span>
                    <span className="rounded-full bg-rose-500/20 px-2 py-0.5 text-[10px] font-semibold text-rose-300">
                      YÜKSEK RİSK
                    </span>
                  </div>
                  <div className="flex items-center justify-between rounded-lg border border-amber-500/20 bg-amber-500/10 px-3 py-2.5">
                    <span className="text-sm text-amber-200">Penisilin alerji eşleşmesi</span>
                    <span className="rounded-full bg-amber-500/20 px-2 py-0.5 text-[10px] font-semibold text-amber-300">
                      ALERJİ
                    </span>
                  </div>
                  <div className="flex items-center justify-between rounded-lg border border-emerald-500/20 bg-emerald-500/10 px-3 py-2.5">
                    <span className="text-sm text-emerald-200">Alternatif: Apiksaban</span>
                    <span className="rounded-full bg-emerald-500/20 px-2 py-0.5 text-[10px] font-semibold text-emerald-300">
                      GÜVENLİ
                    </span>
                  </div>
                </div>
                <div className="mt-4 flex items-center gap-2 border-t border-white/5 pt-3 text-xs text-slate-500">
                  <Zap className="h-3.5 w-3.5 text-sky-400" />
                  184 ms'de analiz edildi
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}

function Footer({ onEnterPortal, onEmergency }) {
  return (
    <footer className="border-t border-white/5 bg-slate-950">
      <div className="mx-auto max-w-7xl px-6 py-14 lg:px-8">
        <div className="grid gap-10 md:grid-cols-2 lg:grid-cols-4">
          <div className="lg:col-span-2">
            <Logo />
            <p className="mt-4 max-w-sm text-sm leading-relaxed text-slate-400">
              Parçalanmış sağlık verisini kurumlar arası daha güvenli reçeteler için
              birleştiren yapay zeka destekli Klinik Karar Destek Sistemi.
            </p>
            <div className="flex items-center gap-3 mt-5">
              <button
                onClick={onEnterPortal}
                className="group inline-flex items-center gap-2 rounded-full border border-sky-400/30 bg-sky-500/10 px-5 py-2 text-sm font-semibold text-sky-200 transition-all hover:border-sky-400/60 hover:bg-sky-500/20 hover:text-white"
              >
                Portala Gir
                <ArrowRight className="h-4 w-4 transition-transform group-hover:translate-x-0.5" />
              </button>
              
              <button
                onClick={onEmergency}
                className="group inline-flex items-center gap-2 rounded-full border border-rose-400/30 bg-rose-500/10 px-5 py-2 text-sm font-semibold text-rose-200 transition-all hover:border-rose-400/60 hover:bg-rose-500/20 hover:text-white"
              >
                <Ambulance className="h-4 w-4" />
                Acil Erişim
              </button>
            </div>
          </div>
          <div>
            <h4 className="text-sm font-semibold text-white">Platform</h4>
            <ul className="mt-4 space-y-2.5 text-sm text-slate-400">
              {NAV_LINKS.map((l) => (
                <li key={l.label}>
                  <a href={l.href} className="transition-colors hover:text-sky-300">
                    {l.label}
                  </a>
                </li>
              ))}
            </ul>
          </div>
          <div>
            <h4 className="text-sm font-semibold text-white">Roller</h4>
            <ul className="mt-4 space-y-2.5 text-sm text-slate-400">
              {AUDIENCE.map((a) => (
                <li key={a.role} className="transition-colors hover:text-sky-300">
                  {a.role}
                </li>
              ))}
            </ul>
          </div>
        </div>
        <div className="mt-12 flex flex-col items-center justify-between gap-4 border-t border-white/5 pt-6 sm:flex-row">
          <p className="text-xs text-slate-500">
            © {new Date().getFullYear()} DrugSense. Tüm hakları saklıdır.
          </p>
          <p className="text-xs text-slate-500">
            Daha güvenli klinik kararlar için tasarlandı.
          </p>
        </div>
      </div>
    </footer>
  );
}

// Ana Bileşene (LandingPage) onEmergency prop'u eklendi
export default function LandingPage({ onEnterPortal = () => {}, onEmergency = () => {} }) {
  return (
    <div className="min-h-screen bg-slate-950 text-white antialiased selection:bg-sky-500/30">
      <Navbar onEnterPortal={onEnterPortal} onEmergency={onEmergency} />
      <main>
        <Hero onEnterPortal={onEnterPortal} onEmergency={onEmergency} />
        <Features />
        <Audience />
        <Platform />
        <Security onEnterPortal={onEnterPortal} />
      </main>
      <Footer onEnterPortal={onEnterPortal} onEmergency={onEmergency} />
    </div>
  );
}