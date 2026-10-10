import type { Metadata } from "next";
import { Navbar } from "@/components/layout/navbar";
import { PageBackground } from "@/components/layout/page-background";
import { NotFoundHero } from "@/components/marketing/not-found";
import { notFound } from "@/content/notFound";
import { site } from "@/content/site";

export const metadata: Metadata = {
  title: `${notFound.metaTitle} · ${site.name}`,
};

/** 404 global: misma navbar (sin el intro) y fondo de la landing. */
export default function NotFound() {
  return (
    <>
      <PageBackground />
      <Navbar intro={false} />
      <main className="flex flex-1 flex-col justify-center pt-(--navbar-height)">
        <NotFoundHero />
      </main>
    </>
  );
}
