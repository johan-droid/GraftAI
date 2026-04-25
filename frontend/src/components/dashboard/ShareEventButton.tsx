'use client';
import { useEffect, useRef, useState } from 'react';
import { Copy, ExternalLink } from 'lucide-react';
import { Button } from '@/components/ui/Button';
import { toast } from '@/components/ui/Toast';

export function ShareEventButton({ username, eventSlug }: { username: string, eventSlug: string }) {
  const [copied, setCopied] = useState(false);
  const copyTimeoutRef = useRef<NodeJS.Timeout | null>(null);

  useEffect(() => {
    return () => {
      if (copyTimeoutRef.current) {
        clearTimeout(copyTimeoutRef.current);
      }
    };
  }, []);

  const handleCopy = async () => {
    if (typeof window === 'undefined') {
      toast.error("Cannot copy link before the page is fully loaded.");
      return;
    }

    const origin = window.location.origin;
    const eventUrl = `${origin}/public/${username}/${eventSlug}`;

    try {
      await navigator.clipboard.writeText(eventUrl);
      setCopied(true);
      toast.success("Link Copied!");

      if (copyTimeoutRef.current) {
        clearTimeout(copyTimeoutRef.current);
      }
      copyTimeoutRef.current = setTimeout(() => setCopied(false), 2000);
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Copy Failed");
    }
  };

  return (
    <div className="flex items-center gap-2">
      <Button 
        variant="outline" 
        size="sm" 
        onClick={handleCopy}
        className={`w-32 transition-colors ${copied ? 'bg-green-50 border-green-200 text-green-700' : ''}`}
      >
        <Copy className="w-4 h-4 mr-2" />
        {copied ? "Copied!" : "Copy Link"}
      </Button>
      
      <a 
        href={`/public/${username}/${eventSlug}`} 
        target="_blank" 
        rel="noopener noreferrer"
        className="p-2 text-gray-400 hover:text-blue-600 hover:bg-blue-50 rounded-md transition-colors"
        title="Preview booking page"
      >
        <ExternalLink className="w-4 h-4" />
      </a>
    </div>
  );
}
