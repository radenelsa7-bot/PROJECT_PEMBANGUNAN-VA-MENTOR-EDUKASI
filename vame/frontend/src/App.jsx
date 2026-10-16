import { Navigate, Outlet, Route, Routes } from "react-router-dom";
import { useAuth } from "./auth.jsx";
import Navbar from "./components/Navbar.jsx";
import Login from "./pages/Login.jsx";
import Dashboard from "./pages/Dashboard.jsx";
import Curricula from "./pages/Curricula.jsx";
import Catalog from "./pages/Catalog.jsx";
import Reading from "./pages/Reading.jsx";
import Mentoring from "./pages/Mentoring.jsx";
import Evaluation from "./pages/Evaluation.jsx";
import Progress from "./pages/Progress.jsx";
import Resume from "./pages/Resume.jsx";
import Admin from "./pages/Admin.jsx";

function Shell({ role }) {
  const { user, loading } = useAuth();
  if (loading) return <div className="center-note">Memuat…</div>;
  if (!user) return <Navigate to="/login" replace />;
  if (role && user.role !== role) return <Navigate to="/" replace />;
  return (
    <>
      <Navbar />
      <main className="container">
        <Outlet />
      </main>
    </>
  );
}

function Home() {
  const { user } = useAuth();
  return <Navigate to={user?.role === "admin" ? "/admin" : "/dashboard"} replace />;
}

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<Login />} />
      <Route element={<Shell role="learner" />}>
        <Route path="/dashboard" element={<Dashboard />} />
        <Route path="/curricula" element={<Curricula />} />
        <Route path="/curricula/:cid" element={<Curricula />} />
        <Route path="/catalog" element={<Catalog />} />
        <Route path="/reading/:rid" element={<Reading />} />
        <Route path="/mentoring" element={<Resume />} />
        <Route path="/mentoring/:rid" element={<Mentoring />} />
        <Route path="/evaluation/:rid" element={<Evaluation />} />
        <Route path="/progress" element={<Progress />} />
      </Route>
      <Route element={<Shell role="admin" />}>
        <Route path="/admin" element={<Admin />} />
      </Route>
      <Route path="*" element={<Home />} />
    </Routes>
  );
}
