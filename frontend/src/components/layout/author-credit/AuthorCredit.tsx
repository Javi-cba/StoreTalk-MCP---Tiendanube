import { footer } from "@/content/site";
import { cn } from "@/lib/utils/cn";

/** "Powered by Javier Córdoba" con el nombre en degradé. Se usa en el footer y en el login. */
export function AuthorCredit({ className }: { className?: string }) {
  return (
    <span className={cn("text-sm text-slate-600", className)}>
      {footer.author.prefix}{" "}
      <span className="bg-linear-to-r from-blue-600 to-sky-500 bg-clip-text text-base font-semibold text-transparent">
        {footer.author.name}
      </span>
    </span>
  );
}
