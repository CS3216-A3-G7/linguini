import { Faq } from "@/components/Faq";
import { Features } from "@/components/Features";
import { FinalCta } from "@/components/FinalCta";
import { HowItWorks } from "@/components/HowItWorks";
import { JournalWall } from "@/components/JournalWall";
import { JsonLd } from "@/components/JsonLd";
import { Pricing } from "@/components/Pricing";
import { SiteFooter } from "@/components/SiteFooter";
import { SiteHeader } from "@/components/SiteHeader";
import { Hero } from "@/components/try/Hero";
import { Why } from "@/components/Why";
import { faq } from "@/data/faq";

export default function HomePage() {
  return (
    <>
      <a href="#main" className="skip-link">Skip to content</a>
      <SiteHeader />
      <main id="main">
        <Hero />
        <Why />
        <HowItWorks />
        <Features />
        <JournalWall />
        <Pricing />
        <Faq />
        <FinalCta />
      </main>
      <SiteFooter />
      <JsonLd faq={faq} />
    </>
  );
}
