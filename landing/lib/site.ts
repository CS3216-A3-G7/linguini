function resolveSiteUrl(): string {
  if (process.env.NEXT_PUBLIC_SITE_URL) return process.env.NEXT_PUBLIC_SITE_URL;
  if (process.env.VERCEL_PROJECT_PRODUCTION_URL) return `https://${process.env.VERCEL_PROJECT_PRODUCTION_URL}`;
  if (process.env.VERCEL_URL) return `https://${process.env.VERCEL_URL}`;
  return "http://localhost:3000";
}

export const site = {
  name: "Linguini",
  url: resolveSiteUrl().replace(/\/$/, ""),
  appUrl: (process.env.NEXT_PUBLIC_APP_URL ?? "http://localhost:5173").replace(/\/$/, ""),
  title: "Linguini — Learn a language from the photos you take",
  shortTitle: "Linguini",
  description:
    "Snap a café, a street, a sunset. Linguini finds the words inside your photo, turns them into bite-size games in Spanish or French, and saves the day to your journal. Free to start.",
  tagline: "Learn the language of your day.",
  locale: "en_US",
  keywords: [
    "language learning app",
    "learn Spanish with photos",
    "learn French vocabulary",
    "learn a language with pictures",
    "photo vocabulary",
    "language journal",
    "gamified language learning",
    "I-Spy language game",
  ],
} as const;

export const appLinks = {
  signUp: `${site.appUrl}/login?mode=signup`,
  signIn: `${site.appUrl}/login`,
};
