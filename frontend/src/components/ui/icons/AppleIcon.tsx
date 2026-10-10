import type { SVGProps } from "react";

type AppleIconProps = SVGProps<SVGSVGElement> & {
  size?: number | string;
};

export function AppleIcon({ size = 20, ...props }: AppleIconProps) {
  return (
    <svg
      xmlns="http://www.w3.org/2000/svg"
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="currentColor"
      aria-hidden="true"
      {...props}
    >
      <path d="M16.37 12.73c-.02-2.27 1.86-3.37 1.94-3.42-1.06-1.55-2.7-1.76-3.28-1.78-1.4-.14-2.73.82-3.44.82-.71 0-1.8-.8-2.96-.78a4.38 4.38 0 0 0-3.7 2.25c-1.58 2.74-.4 6.79 1.13 9.01.75 1.09 1.64 2.3 2.81 2.26 1.13-.05 1.56-.73 2.92-.73 1.36 0 1.75.73 2.94.71 1.22-.02 1.99-1.1 2.73-2.2.86-1.26 1.21-2.48 1.23-2.55-.03-.01-2.36-.9-2.38-3.59zM14.12 6.07c.62-.76 1.04-1.8.93-2.85-.9.04-1.99.6-2.63 1.35-.58.67-1.08 1.74-.95 2.77 1 .08 2.03-.51 2.65-1.27z" />
    </svg>
  );
}
