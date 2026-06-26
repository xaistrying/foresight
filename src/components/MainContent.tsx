"use client";

import { usePathname } from "next/navigation";

const DASHBOARD_PATH = "/dashboard";

interface MainContentProps {
  children: React.ReactNode;
}

export default function MainContent({ children }: MainContentProps) {
  const pathname = usePathname();
  const isDashboard = pathname === DASHBOARD_PATH || pathname === "/";

  return (
    <div className="relative flex-1 overflow-hidden">
      {/* Dashboard iframe — always mounted, never reloads */}
      <iframe
        src="https://ap-southeast-1.quicksight.aws.amazon.com/sn/account/foresight-quicksight/embed/share/accounts/560205085106/dashboards/db28b49a-e7c7-41d7-86ce-a199db18d8ae"
        className="absolute inset-0 w-full h-full border-0"
        allowFullScreen
        title="Foresight Dashboard"
      />

      {/* Overlay for non-dashboard routes — covers the iframe */}
      {!isDashboard && (
        <div className="absolute inset-0 bg-bg-base overflow-y-auto">
          <div className="p-6">{children}</div>
        </div>
      )}
    </div>
  );
}
