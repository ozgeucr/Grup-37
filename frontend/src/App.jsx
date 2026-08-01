import { useState } from "react";

import LandingPage from "./pages/LandingPage";
import Login from "./pages/Login";
import DoctorDashboard from "./pages/Doctor_DashBoard";
import PharmacistDashboard from "./pages/Pharmacist_DashBoard";
import PatientDashboard from "./pages/Patient";

export default function App() {
  const [view, setView] = useState("landing");
  const [currentUser, setCurrentUser] = useState(null);

  // Landing -> Login
  const handleEnterPortal = () => {
    setView("login");
  };

  // Login -> Dashboard
  // Login componentinden: onLoginSuccess(data.role, data.user_data)
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
    return <LandingPage onEnterPortal={handleEnterPortal} />;
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

  // Dashboard
  if (view === "dashboard" && currentUser) {
    switch ((currentUser.role || "").toLowerCase()) {
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