import { ClerkProvider } from "@clerk/nextjs";
import { PageBackground } from "@/components/layout/page-background";
import { clerkAppearance, clerkLocalization } from "@/lib/auth/clerk";

/** Login y registro: pantalla completa, sin navbar ni footer (la vuelta del OAuth los agrega en su página). */
export default function AuthLayout({ children }: LayoutProps<"/">) {
  return (
    <ClerkProvider localization={clerkLocalization} appearance={clerkAppearance}>
      <PageBackground />
      <main className="flex flex-1 flex-col">{children}</main>
    </ClerkProvider>
  );
}
