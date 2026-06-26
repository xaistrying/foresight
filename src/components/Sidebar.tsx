"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { HomeIcon, ChatIcon, SettingsIcon } from "@/src/components/icons";
import { iconColors } from "@/src/constants/colors";

const navItems = [
  { label: "Dashboard", href: "/dashboard", icon: HomeIcon },
  { label: "Chat", href: "/chatops", icon: ChatIcon },
  { label: "Settings", href: "/settings", icon: SettingsIcon },
];

export default function Sidebar() {
  const pathname = usePathname();

  return (
    <aside className="h-screen bg-bg-base border-r border-border flex flex-col items-center py-4 px-2">
      <nav className="flex flex-col gap-2">
        {navItems.map((item) => {
          const isActive = pathname === item.href;
          const Icon = item.icon;
          return (
            <Link
              key={item.href}
              href={item.href}
              title={item.label}
              className={`flex items-center justify-center w-12 h-12 rounded-lg transition-colors ${
                isActive
                  ? "bg-bg-selected"
                  : "hover:bg-bg-hover"
              }`}
            >
              <Icon
                size={22}
                color={isActive ? iconColors.active : iconColors.default}
              />
            </Link>
          );
        })}
      </nav>
    </aside>
  );
}
