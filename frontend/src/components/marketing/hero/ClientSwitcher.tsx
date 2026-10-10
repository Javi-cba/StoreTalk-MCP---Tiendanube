import { GlassPanel } from "@/components/ui/glass";
import { heroUseCases } from "@/content/home";
import { cn } from "@/lib/utils/cn";

type ClientSwitcherProps = {
  active: number;
  onSelect: (index: number) => void;
};

/** Navegación del cubo: un logo por cliente de IA; el activo se pinta con su color y muestra el nombre. */
export function ClientSwitcher({ active, onSelect }: ClientSwitcherProps) {
  return (
    <GlassPanel className="mx-auto flex w-fit items-center gap-1 rounded-full p-1.5">
      {heroUseCases.map(({ client, category }, index) => {
        const isActive = index === active;
        const Icon = client.icon;
        return (
          <button
            key={client.name}
            type="button"
            onClick={() => onSelect(index)}
            aria-label={`Ver ejemplo en ${client.name}: ${category}`}
            aria-current={isActive}
            className={cn(
              "flex h-9 cursor-pointer items-center gap-2 rounded-full px-2.5 text-sm font-medium transition-all duration-300",
              isActive
                ? cn("bg-white shadow-sm", client.color)
                : "text-slate-400 hover:bg-white/60 hover:text-slate-600",
            )}
          >
            <Icon size={18} />
            <span
              className={cn(
                "overflow-hidden whitespace-nowrap text-slate-800 transition-all duration-300",
                isActive ? "max-w-24 opacity-100" : "max-w-0 opacity-0",
              )}
            >
              {client.name}
            </span>
          </button>
        );
      })}
    </GlassPanel>
  );
}
