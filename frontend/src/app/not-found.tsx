import type { Metadata } from "next";
import { Footer } from "@/components/layout/footer";
import { Navbar } from "@/components/layout/navbar";
import { PageBackground } from "@/components/layout/page-background";
import { NotFoundHero } from "@/components/marketing/not-found";
import { notFound } from "@/content/notFound";
import { site } from "@/content/site";

export const metadata: Metadata = {
  title: `${notFound.metaTitle} · ${site.name}`,
};

/** 404 global: misma navbar (sin el intro), footer y fondo de la landing. */
export default function NotFound() {
  return (
    <>
      <PageBackground />
      <Navbar intro={false} />
      <main className="flex flex-col pt-(--navbar-height)">
        <div className="flex screen-fill flex-col justify-center">
          <NotFoundHero />
        </div>
      </main>
      <Footer />
    </>
  );
}
