import { Navbar } from "@/components/layout/navbar";

export default function MarketingLayout({ children }: LayoutProps<"/">) {
  return (
    <>
      <Navbar />
      <div className="flex flex-1 flex-col pt-16 animate-intro-content motion-reduce:animate-none">
        {children}
      </div>
    </>
  );
}
