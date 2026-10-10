import { TiendanubeIcon } from "@/components/ui/icons";
import { site } from "@/content/site";

type BrandLogoProps = {
  /** Reproduce la animación de entrada: el ícono gira y el nombre se revela. */
  intro?: boolean;
};

export function BrandLogo({ intro = false }: BrandLogoProps) {
  return (
    <span className="flex items-center gap-1.5 text-base font-medium tracking-tight">
      <TiendanubeIcon
        size={20}
        className={`text-brand ${intro ? "animate-intro-icon motion-reduce:animate-none" : ""}`}
      />
      <span className={intro ? "animate-intro-name motion-reduce:animate-none" : ""}>
        {site.name}
      </span>
    </span>
  );
}
