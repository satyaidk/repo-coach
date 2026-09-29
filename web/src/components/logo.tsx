import { Compass } from "lucide-react";

export function Logo() {
  return (
    <span className="inline-flex items-center gap-2.5 text-[17px] font-extrabold tracking-tight">
      <span className="grid size-8 place-items-center rounded-lg bg-accent text-white shadow-sm">
        <Compass className="size-[18px]" strokeWidth={2.4} aria-hidden />
      </span>
      RepoCompass
    </span>
  );
}
