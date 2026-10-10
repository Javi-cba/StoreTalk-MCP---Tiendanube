import type { Metadata } from "next";
import { ConnectStorePanel } from "@/components/dashboard/connect";
import { connectCopy } from "@/content/connect";
import { site } from "@/content/site";

export const metadata: Metadata = { title: `${connectCopy.start.metaTitle} · ${site.name}` };

export default function ConnectPage() {
  return (
    <div className="flex screen-fill items-center justify-center px-4 py-10 sm:px-6">
      <ConnectStorePanel />
    </div>
  );
}
