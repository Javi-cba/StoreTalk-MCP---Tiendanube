import type { Metadata } from "next";
import { AuthArt, AuthScreen } from "@/components/auth";
import { authCopy } from "@/content/auth";
import { site } from "@/content/site";

export const metadata: Metadata = { title: `${authCopy.signUp.metaTitle} · ${site.name}` };

export default function SignUpPage() {
  return <AuthScreen flow="signUp" art={<AuthArt />} />;
}
