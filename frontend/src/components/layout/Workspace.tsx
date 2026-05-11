import React from 'react';

export default function Workspace({ children }: { children: React.ReactNode }) {
  return (
    <div className="flex flex-col min-h-screen bg-gray-50">
      <main className="flex-1 w-full max-w-7xl mx-auto p-4 sm:p-6 lg:p-8">
        {children}
      </main>
      <footer className="w-full py-4 text-center text-sm text-gray-500 border-t bg-white">
        Designed by <span className="font-semibold text-gray-900">Nova Devs</span>
      </footer>
    </div>
  );
}
