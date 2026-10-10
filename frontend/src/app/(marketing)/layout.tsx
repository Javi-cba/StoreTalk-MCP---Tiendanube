import { Footer } from "@/components/layout/footer";
import { Navbar } from "@/components/layout/navbar";
import { PageBackground } from "@/components/layout/page-background";

export default function MarketingLayout({ children }: LayoutProps<"/">) {
  return (
    <>
      <PageBackground />
      <Navbar />
      <div className="flex flex-1 flex-col pt-(--navbar-height) animate-intro-content motion-reduce:animate-none">
        {children}
        <Footer />
      </div>
    </>
  );
}
