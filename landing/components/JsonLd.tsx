import { appLinks, site } from "@/lib/site";

export type FaqItem = { q: string; a: string };

type JsonLdProps = {
  /** Optional FAQ entries; when present a FAQPage node is added to the graph. */
  faq?: FaqItem[];
};

/** Serialise for an inline <script>: `<` is escaped so the payload can never close the tag. */
function serialize(data: unknown): string {
  return JSON.stringify(data).replace(/</g, "\\u003c");
}

export function JsonLd({ faq }: JsonLdProps) {
  const orgId = `${site.url}/#organization`;
  const websiteId = `${site.url}/#website`;
  const appId = `${site.url}/#app`;
  const logoUrl = `${site.url}/brand/linguini-logo.png`;

  const graph: Record<string, unknown>[] = [
    {
      "@type": "Organization",
      "@id": orgId,
      name: site.name,
      url: `${site.url}/`,
      logo: {
        "@type": "ImageObject",
        url: logoUrl,
        width: 360,
        height: 360,
      },
    },
    {
      "@type": "WebSite",
      "@id": websiteId,
      name: site.name,
      url: `${site.url}/`,
      description: site.description,
      inLanguage: "en",
      publisher: { "@id": orgId },
    },
    {
      "@type": "SoftwareApplication",
      "@id": appId,
      name: site.name,
      description: site.description,
      url: `${site.url}/`,
      installUrl: appLinks.signUp,
      applicationCategory: "EducationalApplication",
      operatingSystem: "Web",
      image: `${site.url}/opengraph-image`,
      publisher: { "@id": orgId },
      offers: [
        {
          "@type": "Offer",
          name: "Free",
          price: "0",
          priceCurrency: "USD",
          category: "free",
        },
        {
          "@type": "Offer",
          name: "Plus",
          price: "6.99",
          priceCurrency: "USD",
          category: "subscription",
          priceSpecification: {
            "@type": "UnitPriceSpecification",
            price: "6.99",
            priceCurrency: "USD",
            unitCode: "MON",
            billingDuration: "P1M",
            referenceQuantity: {
              "@type": "QuantitativeValue",
              value: 1,
              unitCode: "MON",
            },
          },
        },
        {
          "@type": "Offer",
          name: "Plus (yearly)",
          price: "59.88",
          priceCurrency: "USD",
          category: "subscription",
          priceSpecification: {
            "@type": "UnitPriceSpecification",
            price: "59.88",
            priceCurrency: "USD",
            unitCode: "ANN",
            billingDuration: "P1Y",
            referenceQuantity: {
              "@type": "QuantitativeValue",
              value: 1,
              unitCode: "ANN",
            },
          },
        },
      ],
    },
  ];

  if (faq && faq.length > 0) {
    graph.push({
      "@type": "FAQPage",
      "@id": `${site.url}/#faq`,
      isPartOf: { "@id": websiteId },
      mainEntity: faq.map(({ q, a }) => ({
        "@type": "Question",
        name: q,
        acceptedAnswer: { "@type": "Answer", text: a },
      })),
    });
  }

  return (
    <script
      type="application/ld+json"
      dangerouslySetInnerHTML={{ __html: serialize({ "@context": "https://schema.org", "@graph": graph }) }}
    />
  );
}
export default JsonLd;
