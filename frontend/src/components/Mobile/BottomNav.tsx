/**
 * Mobile Bottom Navigation
 * 
- Mobile-first navigation with smooth transitions
- Active state indicators
- Gesture-friendly touch targets
 */

'use client';

import { useState } from 'react';
import { motion } from 'framer-motion';
import { Home, Calendar, Users, Settings, Plus } from 'lucide-react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';

const navItems = [
  { icon: Home, label: 'Home', href: '/dashboard' },
  { icon: Calendar, label: 'Calendar', href: '/dashboard/calendar' },
  { icon: null, label: 'Create', href: '#', isAction: true },
  { icon: Users, label: 'Team', href: '/dashboard/team' },
  { icon: Settings, label: 'Settings', href: '/dashboard/settings' },
];

export default function BottomNav() {
  const pathname = usePathname();
  const [isPressed, setIsPressed] = useState(false);

  return (
    <motion.nav
      initial={{ y: 100 }}
      animate={{ y: 0 }}
      className="fixed bottom-0 left-0 right-0 z-40 lg:hidden"
    >
      {/* Glassmorphism Background */}
      <div className="bg-slate-900/90 backdrop-blur-xl border-t border-slate-700/50 px-2 pb-safe">
        <div className="flex items-center justify-around py-2">
          {navItems.map((item, index) => {
            const isActive = pathname === item.href;
            const Icon = item.icon;

            if (item.isAction) {
              return (
                <motion.button
                  key={index}
                  whileTap={{ scale: 0.9 }}
                  onTouchStart={() => setIsPressed(true)}
                  onTouchEnd={() => setIsPressed(false)}
                  className="relative -mt-8"
                >
                  <motion.div
                    animate={{
                      scale: isPressed ? 0.95 : 1,
                      boxShadow: isPressed
                        ? '0 4px 20px rgba(59, 130, 246, 0.4)'
                        : '0 8px 30px rgba(59, 130, 246, 0.5)',
                    }}
                    className="w-14 h-14 rounded-2xl bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center shadow-lg"
                  >
                    <Plus className="w-7 h-7 text-white" />
                  </motion.div>
                  <span className="absolute -bottom-5 left-1/2 -translate-x-1/2 text-[10px] text-slate-400 whitespace-nowrap">
                    Create
                  </span>
                </motion.button>
              );
            }

            return (
              <Link
                key={index}
                href={item.href}
                className="relative flex flex-col items-center gap-1 py-2 px-3"
              >
                <motion.div
                  animate={{
                    scale: isActive ? 1.1 : 1,
                    y: isActive ? -2 : 0,
                  }}
                  className={`relative p-2 rounded-xl transition-colors ${
                    isActive
                      ? 'bg-blue-500/20 text-blue-400'
                      : 'text-slate-400 hover:text-slate-300'
                  }`}
                >
                  {Icon && <Icon className="w-6 h-6" strokeWidth={isActive ? 2.5 : 2} />}
                  
                  {/* Active Indicator */}
                  {isActive && (
                    <motion.div
                      layoutId="bottomNavIndicator"
                      className="absolute -bottom-1 left-1/2 -translate-x-1/2 w-1 h-1 bg-blue-400 rounded-full"
                    />
                  )}
                </motion.div>
                
                <span
                  className={`text-[10px] font-medium transition-colors ${
                    isActive ? 'text-blue-400' : 'text-slate-500'
                  }`}
                >
                  {item.label}
                </span>
              </Link>
            );
          })}
        </div>
      </div>
    </motion.nav>
  );
}
