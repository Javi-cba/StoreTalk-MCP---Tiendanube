import type { Metadata } from "next";
import { Sparkles } from "lucide-react";
import { ConnectStoreButton } from "@/components/dashboard/connect";
import { StoreList } from "@/components/dashboard/stores";
import { ButtonLink } from "@/components/ui/button";
import { dashboardCopy } from "@/content/dashboard";
import { navigation, site } from "@/content/site";

export const metadata: Metadata = { title: `${dashboardCopy.metaTitle} · ${site.name}` };

export default function DashboardPage() {
  return (
    <StoreList
      headerAction={
        <>
          <ButtonLink href={navigation.connectAi.href} variant="glass">
            <Sparkles className="size-4" aria-hidden />
            {navigation.connectAi.label}
          </ButtonLink>
          <ConnectStoreButton label={dashboardCopy.connectAnother} className="sm:w-64" />
        </>
      }
      emptyAction={<ConnectStoreButton label={dashboardCopy.connectFirst} />}
    />
  );
}
