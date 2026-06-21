"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { HomeIcon, ChatIcon, SettingsIcon } from "@/src/components/icons";
import { colors } from "@/src/constants/colors";

const navItems = [
  { label: "Dashboard", href: "/", icon: HomeIcon },
  { label: "Chat", href: "/chatops", icon: ChatIcon },
  { label: "Settings", href: "/settings", icon: SettingsIcon },
];

export default function Sidebar() {
  const pathname = usePathname();

  return (
    <aside className="h-screen bg-gray-900 flex flex-col items-center py-4 px-2">
      <nav className="flex flex-col gap-2">
        {navItems.map((item) => {
          const isActive = pathname === item.href;
          const Icon = item.icon;
          return (
            <Link
              key={item.href}
              href={item.href}
              title={item.label}
              className={`flex items-center justify-center w-16 h-16 rounded-lg transition-colors ${
                isActive
                  ? "bg-gray-700"
                  : "hover:bg-gray-800"
              }`}
            >
              <Icon size={28} color={colors.icon.default} />
            </Link>
          );
        })}
      </nav>
    </aside>
  );
}
