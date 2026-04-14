import { OnboardingProvider } from "@/context/onboarding-context";

export const metadata = {
  title: "Profile Setup | GraftAI",
  description: "Complete your profile setup and get your booking page live.",
};

export default function ProfileSetupLayout({ children }: { children: React.ReactNode }) {
  return <OnboardingProvider>{children}</OnboardingProvider>;
}
