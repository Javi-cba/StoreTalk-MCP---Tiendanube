import type { Metadata } from "next";
import { AuthArt, AuthScreen } from "@/components/auth";
import { authCopy } from "@/content/auth";
import { site } from "@/content/site";

export const metadata: Metadata = { title: `${authCopy.signIn.metaTitle} · ${site.name}` };

export default function SignInPage() {
  return <AuthScreen flow="signIn" art={<AuthArt />} />;
}
