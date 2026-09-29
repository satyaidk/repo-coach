"use client";

import { useEffect, useState } from "react";

import { cn } from "@/lib/format";

export interface NavItem {
  id: string;
  label: string;
}

/** Jump links to each section; highlights the one you're reading. */
export function SectionNav({ items }: { items: NavItem[] }) {
  const [active, setActive] = useState<string | null>(null);
  const ids = items.map((item) => item.id).join(",");

  useEffect(() => {
    const visible = new Set<string>();
    const order = ids.split(",");
    const observer = new IntersectionObserver(
      (entries) => {
        for (const entry of entries) {
          if (entry.isIntersecting) visible.add(entry.target.id);
          else visible.delete(entry.target.id);
        }
        const first = order.find((id) => visible.has(id));
        if (first) setActive(first);
      },
      { rootMargin: "-20% 0px -55% 0px" },
    );
    for (const id of order) {
      const el = document.getElementById(id);
      if (el) observer.observe(el);
    }
    return () => observer.disconnect();
  }, [ids]);

  return (
    <nav aria-label="Sections" className="-mx-1 overflow-x-auto [scrollbar-width:none] [&::-webkit-scrollbar]:hidden">
      <ul className="flex min-w-max gap-1 px-1">
        {items.map((item) => (
          <li key={item.id}>
            <a
              href={`#${item.id}`}
              aria-current={active === item.id ? "location" : undefined}
              className={cn(
                "block rounded-lg px-3 py-1.5 text-sm font-medium whitespace-nowrap text-muted transition-colors hover:bg-surface-2 hover:text-fg",
                active === item.id && "bg-accent-soft text-accent-text hover:bg-accent-soft hover:text-accent-text",
              )}
            >
              {item.label}
            </a>
          </li>
        ))}
      </ul>
    </nav>
  );
}
