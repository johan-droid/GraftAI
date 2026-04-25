'use client';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { Home, Calendar, Link as LinkIcon, Settings } from 'lucide-react';

export function BottomNav() {
  const pathname = usePathname();

  // Do not render the bottom nav on public booking pages or auth pages
  if (!pathname.startsWith('/dashboard')) {
    return null;
  }

  const navItems = [
    { name: 'Home', href: '/dashboard', icon: Home },
    { name: 'Calendar', href: '/dashboard/calendar', icon: Calendar },
    { name: 'Event Types', href: '/dashboard/event-types', icon: LinkIcon },
    { name: 'Settings', href: '/dashboard/settings', icon: Settings },
  ];

  return (
    <div className="md:hidden fixed bottom-0 w-full bg-white border-t border-gray-200 pb-safe z-50">
      <div className="flex justify-around items-center h-16 px-2">
        {navItems.map((item) => {
          const isActive = pathname === item.href;
          const Icon = item.icon;
          
          return (
            <Link 
              key={item.name} 
              href={item.href}
              className={`flex flex-col items-center justify-center w-full h-full space-y-1 transition-colors
                ${isActive ? 'text-blue-600' : 'text-gray-500 hover:text-gray-900'}
              `}
            >
              <div className={`p-1 rounded-full ${isActive ? 'bg-blue-50' : ''}`}>
                <Icon className="w-6 h-6" />
              </div>
              <span className="text-[10px] font-medium">{item.name}</span>
            </Link>
          );
        })}
      </div>
    </div>
  );
}

// Export as default for backward compatibility
export default BottomNav;
