import { Outlet } from "react-router-dom";
import { Navbar } from "@/components/Navbar";

export function AppShellLayout() {
  return (
    <>
      <Navbar />
      <div className="app-shell">
        <Outlet />
      </div>
    </>
  );
}
