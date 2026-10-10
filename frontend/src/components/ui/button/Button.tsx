import type { ComponentProps } from "react";
import { LoaderCircle } from "lucide-react";
import { buttonStyles, type ButtonVariant } from "./buttonStyles";

type ButtonProps = ComponentProps<"button"> & {
  variant?: ButtonVariant;
  /** Muestra un spinner y deshabilita el botón. */
  loading?: boolean;
};

export function Button({
  variant = "primary",
  loading = false,
  disabled,
  className,
  children,
  type = "button",
  ...props
}: ButtonProps) {
  return (
    <button
      type={type}
      disabled={disabled || loading}
      aria-busy={loading || undefined}
      className={buttonStyles(variant, className)}
      {...props}
    >
      {loading && <LoaderCircle className="size-4 animate-spin" aria-hidden />}
      {children}
    </button>
  );
}
