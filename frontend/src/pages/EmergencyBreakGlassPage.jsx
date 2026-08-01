import { useState, useRef, useEffect } from "react";
import {
  AlertTriangle,
  ShieldAlert,
  Siren,
  Loader2,
  HeartPulse,
  AlertOctagon,
  Activity,
  Stethoscope,
  Ban,
  Clock,
  User,
  UserCog,
  FileText,
  ChevronRight,
} from "lucide-react";

const PRESET_REASONS = [
  "Acil Müdahale",
  "Kardiyak Arrest",
  "Trafik Kazası",
  "Anafilaksi Şüphesi",
  "Bilinç Kaybı",
  "Şiddetli Kanama",
  "Diğer",
];

const severityStyles = {
  Kritik: "bg-red-600 text-white border-red-400",
  Yüksek: "bg-rose-500 text-white border-rose-300",
  Orta: "bg-amber-500 text-slate-900 border-amber-300",
  Düşük: "bg-yellow-200 text-slate-900 border-yellow-400",
};

function formatDate(value) {
  if (!value) return "-";
  const d = new Date(value);
  if (Number.isNaN(d.getTime())) return value;
  return d.toLocaleDateString("tr-TR", {
    day: "2-digit",
    month: "2-digit",
    year: "numeric",
  });
}

export default function EmergencyBreakGlassPortal() {
  const [paramedicTc, setParamedicTc] = useState("");
  const [patientTc, setPatientTc] = useState("");
  const [reason, setReason] = useState("Acil Müdahale");
  const [customReason, setCustomReason] = useState("");
  const [loading, setLoading] = useState(false);
  const [vitalData, setVitalData] = useState(null);
  const [error, setError] = useState(null);
  const [accessLog, setAccessLog] = useState(null);

  const resultRef = useRef(null);

  useEffect(() => {
    if (vitalData && resultRef.current) {
      resultRef.current.scrollIntoView({ behavior: "smooth", block: "start" });
    }
  }, [vitalData]);

  const handleTcChange = (value, setter) => {
    const digits = value.replace(/\D/g, "").slice(0, 11);
    setter(digits);
  };

  const canSubmit =
    paramedicTc.length === 11 && patientTc.length === 11 && !loading;

  const effectiveReason =
    reason === "Diğer" ? customReason.trim() || "Acil Müdahale" : reason;

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!canSubmit) return;

    setLoading(true);
    setError(null);
    setVitalData(null);
    setAccessLog(null);

    try {
      const res = await fetch("http://localhost:8000/break-glass", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          paramedic_tc: paramedicTc,
          patient_tc: patientTc,
          reason: effectiveReason,
        }),
      });

      if (!res.ok) {
        let msg = `Sunucu hatası (HTTP ${res.status})`;
        try {
          const body = await res.json();
          if (body?.detail) msg = body.detail;
          else if (body?.message) msg = body.message;
        } catch {
          /* ignore parse error */
        }
        throw new Error(msg);
      }

      const payload = await res.json();
      
      // Backend'den gelen vital_data yapısını JSX formatına güvenli şekilde map'liyoruz
      const rawVital = payload.vital_data ?? {};
      
      const mappedAllergies = (rawVital.allergies ?? []).map((a) => ({
        name: a.allergen ?? a.name,
        severity: a.severity ?? "Orta",
      }));

      const mappedDiseases = (rawVital.chronic_diseases ?? []).map((d) => ({
        name: d.disease ?? d.name,
        diagnosed_date: d.date ?? d.diagnosed_date,
      }));

      const mappedSurgeries = (rawVital.surgeries ?? []).map((s) => ({
        name: s.surgery ?? s.name,
        date: s.date ?? "",
        notes: s.notes,
      }));

      setVitalData({
        allergies: mappedAllergies,
        chronic_diseases: mappedDiseases,
        surgeries: mappedSurgeries,
      });

      setAccessLog(
        payload.access_log_id ?? payload.log_id ?? `BG-${Date.now()}`,
      );
    } catch (err) {
      const msg =
        err instanceof TypeError
          ? "Sunucuya ulaşılamıyor. Acil durum protokollerini manuel olarak uygulayın."
          : err instanceof Error
            ? err.message
            : "Bilinmeyen hata.";
      setError(msg);
    } finally {
      setLoading(false);
    }
  };

  const handleReset = () => {
    setVitalData(null);
    setError(null);
    setAccessLog(null);
    setPatientTc("");
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 selection:bg-rose-600 selection:text-white">
      {/* Top hazard stripe */}
      <div className="h-2 w-full bg-[repeating-linear-gradient(45deg,#f59e0b_0_24px,#0f172a_24px_48px)]" />

      <div className="mx-auto w-full max-w-3xl px-4 py-6 sm:px-6 sm:py-8">
        {/* Header */}
        <header className="mb-5 flex items-center gap-3">
          <div className="flex h-12 w-12 shrink-0 items-center justify-center rounded-xl bg-rose-600 shadow-lg shadow-rose-600/30">
            <Siren className="h-7 w-7 text-white" />
          </div>
          <div>
            <h1 className="text-2xl font-black leading-tight tracking-tight text-white sm:text-3xl">
              KIRMIZI ALARM
            </h1>
            <p className="text-sm font-semibold text-rose-400">
              Acil Erişim Portalı · Break-Glass Modu
            </p>
          </div>
        </header>

        {/* Warning banner */}
        <div
          role="alert"
          className="mb-6 flex items-start gap-3 rounded-xl border-2 border-rose-500 bg-rose-950/60 p-4 shadow-lg shadow-rose-900/20"
        >
          <ShieldAlert className="mt-0.5 h-6 w-6 shrink-0 text-rose-400" />
          <p className="text-sm font-bold leading-relaxed text-rose-100 sm:text-base">
            <span className="font-black text-white">DİKKAT: </span>
            Bu sistem sadece hayati acil müdahaleler içindir. Tüm acil erişimler
            yasal denetim için loglanmakta ve hastaya bildirilmektedir.
          </p>
        </div>

        {/* Form */}
        <form
          onSubmit={handleSubmit}
          className="rounded-2xl border border-slate-800 bg-slate-900/80 p-5 shadow-xl sm:p-6"
        >
          <div className="grid gap-5">
            {/* Paramedic TC */}
            <div>
              <label
                htmlFor="paramedic-tc"
                className="mb-2 flex items-center gap-2 text-sm font-bold text-slate-200"
              >
                <UserCog className="h-4 w-4 text-amber-400" />
                Paramedik TC No
              </label>
              <input
                id="paramedic-tc"
                inputMode="numeric"
                autoComplete="off"
                placeholder="11 haneli TC kimlik no"
                value={paramedicTc}
                onChange={(e) => handleTcChange(e.target.value, setParamedicTc)}
                className="w-full rounded-lg border-2 border-slate-700 bg-slate-950 px-4 py-4 text-xl font-bold tracking-widest text-white placeholder:font-normal placeholder:tracking-normal placeholder:text-slate-600 focus:border-amber-400 focus:outline-none focus:ring-2 focus:ring-amber-400/40"
              />
              <p className="mt-1 text-xs text-slate-500">
                {paramedicTc.length}/11 hane
              </p>
            </div>

            {/* Patient TC */}
            <div>
              <label
                htmlFor="patient-tc"
                className="mb-2 flex items-center gap-2 text-sm font-bold text-slate-200"
              >
                <User className="h-4 w-4 text-rose-400" />
                Hasta TC No
              </label>
              <input
                id="patient-tc"
                inputMode="numeric"
                autoComplete="off"
                placeholder="11 haneli TC kimlik no"
                value={patientTc}
                onChange={(e) => handleTcChange(e.target.value, setPatientTc)}
                className="w-full rounded-lg border-2 border-slate-700 bg-slate-950 px-4 py-4 text-xl font-bold tracking-widest text-white placeholder:font-normal placeholder:tracking-normal placeholder:text-slate-600 focus:border-rose-400 focus:outline-none focus:ring-2 focus:ring-rose-400/40"
              />
              <p className="mt-1 text-xs text-slate-500">
                {patientTc.length}/11 hane
              </p>
            </div>

            {/* Reason */}
            <div>
              <label
                htmlFor="reason"
                className="mb-2 flex items-center gap-2 text-sm font-bold text-slate-200"
              >
                <FileText className="h-4 w-4 text-slate-400" />
                Acil Gerekçe
              </label>
              <select
                id="reason"
                value={reason}
                onChange={(e) => setReason(e.target.value)}
                className="w-full rounded-lg border-2 border-slate-700 bg-slate-950 px-4 py-3 text-base font-semibold text-white focus:border-amber-400 focus:outline-none focus:ring-2 focus:ring-amber-400/40"
              >
                {PRESET_REASONS.map((r) => (
                  <option key={r} value={r} className="bg-slate-900">
                    {r}
                  </option>
                ))}
              </select>
              {reason === "Diğer" && (
                <input
                  type="text"
                  value={customReason}
                  onChange={(e) => setCustomReason(e.target.value)}
                  placeholder="Gerekçeyi açıklayın..."
                  className="mt-3 w-full rounded-lg border-2 border-slate-700 bg-slate-950 px-4 py-3 text-base font-semibold text-white placeholder:font-normal placeholder:text-slate-600 focus:border-amber-400 focus:outline-none focus:ring-2 focus:ring-amber-400/40"
                />
              )}
            </div>
          </div>

          {/* Submit button */}
          <button
            type="submit"
            disabled={!canSubmit}
            className={[
              "group mt-6 flex w-full items-center justify-center gap-3 rounded-xl px-6 py-6 text-lg font-black uppercase tracking-wide transition-all sm:text-xl",
              canSubmit
                ? "bg-rose-600 text-white shadow-xl shadow-rose-600/40 hover:bg-rose-500 hover:shadow-rose-500/50 active:scale-[0.99]"
                : "cursor-not-allowed bg-slate-800 text-slate-500",
            ].join(" ")}
          >
            {loading ? (
              <>
                <Loader2 className="h-7 w-7 animate-spin" />
                ERİŞİM SAĞLANIYOR...
              </>
            ) : (
              <>
                <Siren className="h-7 w-7" />
                KIRMIZI ALARM: ACİL ERİŞİM BAŞLAT (CAMI KIR)
              </>
            )}
          </button>

          {!canSubmit && !loading && (
            <p className="mt-3 text-center text-xs font-semibold text-amber-400">
              Devam etmek için her iki TC no da 11 haneli olmalıdır.
            </p>
          )}
        </form>

        {/* Loading state */}
        {loading && (
          <div className="mt-6 flex items-center justify-center gap-3 rounded-xl border-2 border-amber-500 bg-amber-950/40 px-5 py-4">
            <span className="relative flex h-4 w-4">
              <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-amber-400 opacity-75" />
              <span className="relative inline-flex h-4 w-4 rounded-full bg-amber-500" />
            </span>
            <p className="text-base font-bold text-amber-200">
              Hayati veriler acilen getiriliyor... Lütfen bekleyin.
            </p>
          </div>
        )}

        {/* Error */}
        {error && !loading && (
          <div
            role="alert"
            className="mt-6 flex items-start gap-3 rounded-xl border-2 border-rose-500 bg-rose-950/60 p-4"
          >
            <AlertTriangle className="mt-0.5 h-6 w-6 shrink-0 text-rose-400" />
            <div>
              <p className="text-sm font-black uppercase tracking-wide text-rose-300">
                Erişim Başarısız
              </p>
              <p className="mt-1 text-sm font-semibold text-rose-100">{error}</p>
            </div>
          </div>
        )}

        {/* Results */}
        {vitalData && !loading && (
          <div ref={resultRef} className="mt-6 scroll-mt-4 space-y-5">
            {/* Access confirmation banner */}
            <div className="flex items-center justify-between gap-3 rounded-xl border border-amber-500/60 bg-amber-950/40 px-4 py-3">
              <div className="flex items-center gap-2">
                <HeartPulse className="h-5 w-5 text-amber-400" />
                <p className="text-sm font-bold text-amber-100">
                  Acil erişim etkinleştirildi. Veriler gösteriliyor.
                </p>
              </div>
              <span className="rounded-md bg-amber-500/20 px-2 py-1 font-mono text-xs font-bold text-amber-300">
                LOG: {accessLog}
              </span>
            </div>

            {/* Allergies */}
            <section className="rounded-2xl border-2 border-rose-500 bg-slate-900/80 p-5 shadow-lg shadow-rose-900/20">
              <div className="mb-4 flex items-center gap-2">
                <AlertOctagon className="h-6 w-6 text-rose-400" />
                <h2 className="text-xl font-black uppercase tracking-wide text-white">
                  Alerjiler
                </h2>
              </div>

              {vitalData.allergies.length === 0 ? (
                <div className="flex items-center gap-2 rounded-lg bg-slate-800/60 px-4 py-3">
                  <Ban className="h-5 w-5 text-slate-500" />
                  <p className="text-base font-bold text-slate-400">
                    Kayıtlı Alerji Yok
                  </p>
                </div>
              ) : (
                <ul className="space-y-3">
                  {vitalData.allergies.map((a, i) => {
                    const style =
                      severityStyles[a.severity] ??
                      "bg-slate-700 text-white border-slate-500";
                    return (
                      <li
                        key={i}
                        className="flex flex-col gap-2 rounded-lg border border-slate-700 bg-slate-950/60 p-3 sm:flex-row sm:items-center sm:justify-between"
                      >
                        <span className="text-lg font-bold text-white">
                          {a.name}
                        </span>
                        <span
                          className={`inline-flex w-fit items-center rounded-full border px-3 py-1 text-sm font-black uppercase tracking-wide ${style}`}
                        >
                          {a.severity}
                        </span>
                      </li>
                    );
                  })}
                </ul>
              )}
            </section>

            {/* Chronic diseases */}
            <section className="rounded-2xl border border-slate-700 bg-slate-900/80 p-5 shadow-lg">
              <div className="mb-4 flex items-center gap-2">
                <Activity className="h-6 w-6 text-amber-400" />
                <h2 className="text-xl font-black uppercase tracking-wide text-white">
                  Kronik Hastalıklar
                </h2>
              </div>

              {vitalData.chronic_diseases.length === 0 ? (
                <div className="flex items-center gap-2 rounded-lg bg-slate-800/60 px-4 py-3">
                  <Ban className="h-5 w-5 text-slate-500" />
                  <p className="text-base font-bold text-slate-400">
                    Kayıtlı Kronik Hastalık Yok
                  </p>
                </div>
              ) : (
                <ul className="space-y-2">
                  {vitalData.chronic_diseases.map((d, i) => (
                    <li
                      key={i}
                      className="flex items-center justify-between gap-3 rounded-lg border border-slate-700 bg-slate-950/60 px-4 py-3"
                    >
                      <span className="text-lg font-bold text-white">
                        {d.name}
                      </span>
                      <span className="flex items-center gap-1.5 text-sm font-semibold text-slate-400">
                        <Clock className="h-4 w-4" />
                        {formatDate(d.diagnosed_date)}
                      </span>
                    </li>
                  ))}
                </ul>
              )}
            </section>

            {/* Surgeries */}
            <section className="rounded-2xl border border-slate-700 bg-slate-900/80 p-5 shadow-lg">
              <div className="mb-4 flex items-center gap-2">
                <Stethoscope className="h-6 w-6 text-amber-400" />
                <h2 className="text-xl font-black uppercase tracking-wide text-white">
                  Geçmiş Cerrahi
                </h2>
              </div>

              {vitalData.surgeries.length === 0 ? (
                <div className="flex items-center gap-2 rounded-lg bg-slate-800/60 px-4 py-3">
                  <Ban className="h-5 w-5 text-slate-500" />
                  <p className="text-base font-bold text-slate-400">
                    Kayıtlı Cerrahi Yok
                  </p>
                </div>
              ) : (
                <ul className="space-y-2">
                  {vitalData.surgeries.map((s, i) => (
                    <li
                      key={i}
                      className="rounded-lg border border-slate-700 bg-slate-950/60 px-4 py-3"
                    >
                      <div className="flex items-center justify-between gap-3">
                        <span className="text-lg font-bold text-white">
                          {s.name}
                        </span>
                        <span className="flex items-center gap-1.5 text-sm font-semibold text-slate-400">
                          <Clock className="h-4 w-4" />
                          {formatDate(s.date)}
                        </span>
                      </div>
                      {s.notes && (
                        <p className="mt-1.5 text-sm text-slate-500">
                          {s.notes}
                        </p>
                      )}
                    </li>
                  ))}
                </ul>
              )}
            </section>

            {/* Reset */}
            <button
              onClick={handleReset}
              className="flex w-full items-center justify-center gap-2 rounded-xl border border-slate-700 bg-slate-900 px-6 py-3 text-sm font-bold uppercase tracking-wide text-slate-300 transition-colors hover:bg-slate-800 hover:text-white"
            >
              Yeni Erişim
              <ChevronRight className="h-4 w-4" />
            </button>
          </div>
        )}

        {/* Footer */}
        <footer className="mt-8 border-t border-slate-800 pt-4 text-center">
          <p className="text-xs font-semibold text-slate-600">
            Tüm erişimler KVKK ve acil durum mevzuatı kapsamında loglanır.
          </p>
        </footer>
      </div>
    </div>
  );
}