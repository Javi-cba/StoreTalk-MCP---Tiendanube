import type { Metadata } from "next";
import { SsoCallback } from "@/components/auth";
import { Footer } from "@/components/layout/footer";
import { Navbar } from "@/components/layout/navbar";
import { authCopy } from "@/content/auth";
import { site } from "@/content/site";

export const metadata: Metadata = { title: `${authCopy.callback.metaTitle} · ${site.name}` };

/** Vuelta del OAuth: a diferencia del login, muestra la navbar (sin el intro) y el footer mientras carga. */
export default function SsoCallbackPage() {
  return (
    <>
      <Navbar intro={false} />
      <div className="pt-(--navbar-height)">
        <div className="flex screen-fill flex-col justify-center">
          <SsoCallback />
        </div>
      </div>
      <Footer />
    </>
  );
}
