import { useState } from "react";

import LandingPage from "./pages/LandingPage";
import Login from "./pages/Login";
import DoctorDashboard from "./pages/Doctor_DashBoard";
import PharmacistDashboard from "./pages/Pharmacist_DashBoard";
import PatientDashboard from "./pages/Patient";
import EmergencyBreakGlassPage from "./pages/EmergencyBreakGlassPage";

export default function App() {
  const [view, setView] = useState("landing");
  const [currentUser, setCurrentUser] = useState(null);

  // Landing -> Login
  const handleEnterPortal = () => {
    setView("login");
  };

  // Landing -> Emergency (Acil Durum)
  const handleEmergency = () => {
    setView("emergency");
  };

  // Login -> Dashboard
  const handleLoginSuccess = (role, userData) => {
    setCurrentUser({
      ...userData,
      role,
    });

    setView("dashboard");
  };

  // Logout
  const handleLogout = () => {
    setCurrentUser(null);
    setView("landing");
  };

  // Landing
  if (view === "landing") {
    return (
      <LandingPage 
        onEnterPortal={handleEnterPortal} 
        onEmergency={handleEmergency} 
      />
    );
  }

  // Login
  if (view === "login") {
    return (
      <Login
        onLoginSuccess={handleLoginSuccess}
        onBackToLanding={() => setView("landing")}
      />
    );
  }

  // Acil Durum (Kırmızı Kod) Ekranı
  if (view === "emergency") {
    return (
      <EmergencyBreakGlassPage 
        onBack={() => setView("landing")}
      />
    );
  }

  // Dashboard - Rol Kontrolü (Küçük harfe çevrilerek güvenli hale getirildi)
  if (view === "dashboard" && currentUser) {
    const userRole = (currentUser.role || "").toLowerCase().trim();

    switch (userRole) {
      case "doctor":
      case "doktor":
        return (
          <DoctorDashboard
            user={currentUser}
            onLogout={handleLogout}
          />
        );

      case "pharmacist":
      case "eczacı":
      case "eczaci":
        return (
          <PharmacistDashboard
            user={currentUser}
            onLogout={handleLogout}
          />
        );

      case "patient":
      case "hasta":
      default:
        return (
          <PatientDashboard
            user={currentUser}
            onLogout={handleLogout}
          />
        );
    }
  }

  return null;
}