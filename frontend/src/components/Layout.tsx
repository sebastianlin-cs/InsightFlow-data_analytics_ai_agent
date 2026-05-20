import { Link, Outlet, useNavigate } from "react-router-dom";
import { clearToken, getToken } from "../api/client";

export function Layout() {
  const navigate = useNavigate();
  const isLoggedIn = Boolean(getToken());

  function handleLogout() {
    clearToken();
    navigate("/login");
  }

  return (
    <div className="min-h-screen bg-slate-50">
      <header className="border-b border-slate-200 bg-white">
        <div className="mx-auto flex max-w-6xl items-center justify-between px-4 py-4">
          <Link to="/workspace" className="text-xl font-semibold text-slate-950">
            InsightFlow
          </Link>
          {isLoggedIn ? (
            <button
              onClick={handleLogout}
              className="rounded-md border border-slate-300 px-3 py-2 text-sm font-medium text-slate-700 hover:bg-slate-100"
            >
              Logout
            </button>
          ) : (
            <div className="flex gap-2">
              <Link className="rounded-md px-3 py-2 text-sm font-medium text-slate-700 hover:bg-slate-100" to="/login">
                Login
              </Link>
              <Link className="rounded-md bg-slate-900 px-3 py-2 text-sm font-medium text-white" to="/register">
                Register
              </Link>
            </div>
          )}
        </div>
      </header>
      <main className="mx-auto max-w-6xl px-4 py-6">
        <Outlet />
      </main>
    </div>
  );
}
