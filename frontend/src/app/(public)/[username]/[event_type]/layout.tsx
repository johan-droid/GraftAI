// PHASE 3: Force dynamic rendering for booking pages
export const dynamic = 'force-dynamic';
export const revalidate = 0;

export default function BookingLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return <>{children}</>;
}
