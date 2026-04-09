import Link from "next/link";

type EmbedPageProps = {
  params: {
    username: string;
    event_type: string;
  };
};

export default function EmbedBookingPage({ params }: EmbedPageProps) {
  const username = encodeURIComponent(params.username);
  const eventType = encodeURIComponent(params.event_type);
  const publicBookingPath = `/public/${username}/${eventType}`;

  return (
    <main className="min-h-screen bg-white">
      <div className="mx-auto w-full max-w-5xl px-3 py-4 sm:px-4 sm:py-6">
        <div className="mb-3 flex items-center justify-between rounded-xl border border-slate-200 bg-slate-50 px-3 py-2 text-xs text-slate-600 sm:text-sm">
          <span>
            Embedded booking for {params.username}/{params.event_type}
          </span>
          <Link href={publicBookingPath} target="_blank" className="font-semibold text-indigo-600 hover:text-indigo-700">
            Open full page
          </Link>
        </div>

        <iframe
          src={publicBookingPath}
          title="GraftAI Booking Widget"
          className="h-[78vh] w-full rounded-2xl border border-slate-200"
          loading="lazy"
          referrerPolicy="strict-origin-when-cross-origin"
        />
      </div>
    </main>
  );
}
