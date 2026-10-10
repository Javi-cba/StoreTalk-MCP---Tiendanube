import Link from "next/link";
import type { ComponentProps } from "react";
import { buttonStyles, type ButtonVariant } from "./buttonStyles";

type ButtonLinkProps = ComponentProps<typeof Link> & {
  variant?: ButtonVariant;
};

export function ButtonLink({ variant = "primary", className, ...props }: ButtonLinkProps) {
  return <Link className={buttonStyles(variant, className)} {...props} />;
}
