'use client';
import { useState } from 'react';
import { Calendar, Video } from 'lucide-react';
import { Button } from '@/components/ui/Button';
import { apiClient } from '@/lib/api-client';

export default function IntegrationsPage() {
  const [loading, setLoading] = useState<null | 'google_calendar' | 'zoom'>(null);
  const [error, setError] = useState<string | null>(null);

  const handleConnectOAuth = async (provider: 'google_calendar' | 'zoom') => {
    setLoading(provider);
    setError(null);

    try {
      const data = await apiClient.get<any>(`/integrations/${provider}/auth-url`);
      
      if (!data.auth_url) {
        throw new Error("OAuth initiation failed; missing redirect URL.");
      }

      window.location.href = data.auth_url;
    } catch (err) {
      setError(err instanceof Error ? err.message : "Connection failed.");
    } finally {
      setLoading(null);
    }
  };

  return (
    <div className="max-w-4xl mx-auto py-8">
      <h2 className="text-2xl font-bold text-gray-900 mb-6">Connected Apps</h2>
      
      <div className="grid gap-6 md:grid-cols-2">
        {/* Google Calendar Card */}
        <div className="p-6 bg-white border border-gray-200 rounded-xl shadow-sm flex flex-col items-center text-center">
          <div className="w-12 h-12 bg-blue-50 rounded-full flex items-center justify-center mb-4">
            <Calendar className="w-6 h-6 text-blue-600" />
          </div>
          <h3 className="text-lg font-bold text-gray-900 mb-1">Google Calendar</h3>
          <p className="text-sm text-gray-500 mb-6">Sync your availability and automatically create meeting events.</p>
          
          <Button 
            onClick={() => handleConnectOAuth('google_calendar')}
            loadingText="Connecting..."
            className="w-full"
          >
            Connect Calendar
          </Button>
        </div>

        {/* Zoom Card */}
        <div className="p-6 bg-white border border-gray-200 rounded-xl shadow-sm flex flex-col items-center text-center">
          <div className="w-12 h-12 bg-blue-50 rounded-full flex items-center justify-center mb-4">
            <Video className="w-6 h-6 text-blue-600" />
          </div>
          <h3 className="text-lg font-bold text-gray-900 mb-1">Zoom</h3>
          <p className="text-sm text-gray-500 mb-6">Automatically generate unique meeting links for your attendees.</p>
          
          <Button 
            onClick={() => handleConnectOAuth('zoom')}
            loadingText="Connecting..."
            variant="outline"
            className="w-full"
          >
            Connect Zoom
          </Button>
        </div>
      </div>
    </div>
  );
}
