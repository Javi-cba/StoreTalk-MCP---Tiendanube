import type { Metadata } from "next";
import { ConnectStoreButton } from "@/components/dashboard/connect";
import { StoreList } from "@/components/dashboard/stores";
import { dashboardCopy } from "@/content/dashboard";
import { site } from "@/content/site";

export const metadata: Metadata = { title: `${dashboardCopy.metaTitle} · ${site.name}` };

export default function DashboardPage() {
  return (
    <StoreList
      headerAction={<ConnectStoreButton label={dashboardCopy.connectAnother} />}
      emptyAction={<ConnectStoreButton label={dashboardCopy.connectFirst} />}
    />
  );
}
