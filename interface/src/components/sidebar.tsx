"use client"

import Link from "next/link"
import { usePathname } from "next/navigation"

const navItems = [
  { href: "/", label: "Dashboard", icon: "◇" },
  { href: "/specs/graph", label: "Spec Graph", icon: "◈" },
  { href: "/specs/speculate", label: "Speculative Explorer", icon: "◉" },
  { href: "/verification", label: "Verification", icon: "◍" },
  { href: "/agents", label: "Agent Monitor", icon: "◎" },
]

export function Sidebar() {
  const pathname = usePathname()

  return (
    <aside className="fixed left-0 top-0 bottom-0 w-64 border-r bg-card flex flex-col z-50">
      <div className="p-6 border-b">
        <Link href="/" className="flex items-center gap-2">
          <span className="text-xl font-bold tracking-tight">SpecWeave</span>
        </Link>
        <p className="text-xs text-muted-foreground mt-1">v2.0.0 Dashboard</p>
      </div>

      <nav className="flex-1 p-4 space-y-1">
        {navItems.map((item) => {
          const isActive =
            item.href === "/"
              ? pathname === "/"
              : pathname.startsWith(item.href)
          return (
            <Link
              key={item.href}
              href={item.href}
              className={`flex items-center gap-3 px-3 py-2.5 rounded-md text-sm font-medium transition-colors ${
                isActive
                  ? "bg-primary text-primary-foreground"
                  : "text-muted-foreground hover:bg-muted hover:text-foreground"
              }`}
            >
              <span className="text-lg">{item.icon}</span>
              {item.label}
            </Link>
          )
        })}
      </nav>

      <div className="p-4 border-t text-xs text-muted-foreground">
        <p>Backend: localhost:8000</p>
        <p className="mt-1">
          <span className="inline-block w-2 h-2 rounded-full bg-green-500 mr-1" />
          Connected
        </p>
      </div>
    </aside>
  )
}
