import { ClerkProvider } from "@clerk/nextjs";
import { Suspense } from "react";
import { Footer } from "@/components/layout/footer";
import { Navbar } from "@/components/layout/navbar";
import { PageBackground } from "@/components/layout/page-background";
import { AccountActions } from "@/components/layout/account-actions";
import { clerkAppearance, clerkLocalization } from "@/lib/auth/clerk";

/** Área privada: Clerk vive solo acá, la landing no lo carga. */
export default function AppLayout({ children }: LayoutProps<"/">) {
  return (
    <ClerkProvider localization={clerkLocalization} appearance={clerkAppearance}>
      <PageBackground />
      <Navbar intro={false} actions={
          <Suspense>
            <AccountActions />
          </Suspense>
        } />
      <main className="flex flex-1 flex-col pt-(--navbar-height)">{children}</main>
      <Footer />
    </ClerkProvider>
  );
}
