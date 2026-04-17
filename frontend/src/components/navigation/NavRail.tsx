/**
 * Material Design 3 Navigation Rail
 * 
 * Side navigation for tablet and desktop compact layouts:
 * - Width: 80dp
 * - 3-7 navigation destinations
 * - Optional FAB in center
 * - Optional header (logo/menu button)
 * - Active indicator: 56dp wide pill
 * 
 * @see https://m3.material.io/components/navigation-rail/overview
 */

'use client';

import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  Home, 
  Calendar, 
  Settings, 
  Sparkles, 
  Users, 
  BarChart3,
  Menu,
  Plus
} from 'lucide-react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { useTheme } from '@/contexts/ThemeContext';

interface NavItem {
  id: string;
  icon: React.ElementType;
  label: string;
  href: string;
  badge?: number | null;
}

// Navigation destinations (3-7 items per M3 spec)
const navItems: NavItem[] = [
  { id: 'home', icon: Home, label: 'Home', href: '/dashboard' },
  { id: 'calendar', icon: Calendar, label: 'Calendar', href: '/dashboard/calendar' },
  { id: 'ai', icon: Sparkles, label: 'AI', href: '/dashboard/ai' },
  { id: 'teams', icon: Users, label: 'Teams', href: '/dashboard/teams' },
  { id: 'analytics', icon: BarChart3, label: 'Analytics', href: '/dashboard/analytics' },
  { id: 'settings', icon: Settings, label: 'Settings', href: '/dashboard/settings' },
];

// M3 Motion tokens
const m3Motion = {
  standard: { duration: 0.15, ease: "easeOut" as const },
  emphasized: { duration: 0.3, ease: "easeInOut" as const },
};

interface NavRailProps {
  showHeader?: boolean;
  showFab?: boolean;
  onMenuClick?: () => void;
}

export default function NavRail({ 
  showHeader = true, 
  showFab = true,
  onMenuClick 
}: NavRailProps) {
  const pathname = usePathname();
  const { mode } = useTheme();
  const isDark = mode === 'dark';
  const [pressedItem, setPressedItem] = useState<string | null>(null);

  // Get active item
  const activeItem = navItems.find(item => 
    pathname === item.href || pathname.startsWith(item.href + '/')
  ) || navItems[0];

  // Split items for FAB positioning (optional)
  const fabIndex = Math.floor(navItems.length / 2);
  const topItems = navItems.slice(0, fabIndex);
  const bottomItems = navItems.slice(fabIndex);

  return (
    <aside
      className={`
        fixed left-0 top-0 bottom-0 z-30
        hidden medium:flex
        flex-col
        w-20
        py-3
        ${isDark 
          ? 'bg-[#1C1B1F] border-r border-[#49454F]' 
          : 'bg-[#F2F2F4] border-r border-[#E6E1E5]'
        }
      `}
      style={{
        // M3 Navigation Rail: 80dp width
        width: '80px',
      }}
    >
      {/* Header with menu button */}
      {showHeader && (
        <div className="flex items-center justify-center mb-4 px-2">
          <motion.button
            whileTap={{ scale: 0.95 }}
            onClick={onMenuClick}
            className={`
              w-12 h-12 rounded-full
              flex items-center justify-center
              transition-colors duration-150
              ${isDark
                ? 'hover:bg-[#49454F] text-[#E6E1E5]'
                : 'hover:bg-[#E8E0EC] text-[#1C1B1F]'
              }
            `}
            aria-label="Open menu"
          >
            <Menu className="w-6 h-6" strokeWidth={1.5} />
          </motion.button>
        </div>
      )}

      {/* Top navigation items */}
      <div className="flex-1 flex flex-col items-center gap-1">
        {topItems.map((item) => (
          <NavRailItem
            key={item.id}
            item={item}
            isActive={activeItem.id === item.id}
            isPressed={pressedItem === item.id}
            isDark={isDark}
            onPressStart={() => setPressedItem(item.id)}
            onPressEnd={() => setPressedItem(null)}
          />
        ))}

        {/* Center FAB (optional) */}
        {showFab && (
          <div className="py-4">
            <motion.button
              whileTap={{ scale: 0.95 }}
              onClick={() => window.location.href = '/dashboard/book'}
              className={`
                w-14 h-14 rounded-[16px]
                flex items-center justify-center
                shadow-lg
                transition-shadow duration-150
                ${isDark
                  ? 'bg-[#1A73E8] shadow-black/30'
                  : 'bg-[#1A73E8] shadow-blue-900/20'
                }
              `}
              style={{
                // M3 FAB elevation 3
                boxShadow: '0 4px 8px 3px rgba(0,0,0,0.15)',
              }}
              aria-label="Create new"
            >
              <Plus className="w-6 h-6 text-white" strokeWidth={2} />
            </motion.button>
          </div>
        )}

        {/* Bottom navigation items */}
        {bottomItems.map((item) => (
          <NavRailItem
            key={item.id}
            item={item}
            isActive={activeItem.id === item.id}
            isPressed={pressedItem === item.id}
            isDark={isDark}
            onPressStart={() => setPressedItem(item.id)}
            onPressEnd={() => setPressedItem(null)}
          />
        ))}
      </div>
    </aside>
  );
}

// Individual nav rail item component
interface NavRailItemProps {
  item: NavItem;
  isActive: boolean;
  isPressed: boolean;
  isDark: boolean;
  onPressStart: () => void;
  onPressEnd: () => void;
}

function NavRailItem({ 
  item, 
  isActive, 
  isPressed, 
  isDark,
  onPressStart,
  onPressEnd 
}: NavRailItemProps) {
  const Icon = item.icon;

  return (
    <Link
      href={item.href}
      className="relative flex flex-col items-center justify-center w-full py-1"
      onTouchStart={onPressStart}
      onTouchEnd={onPressEnd}
      onMouseDown={onPressStart}
      onMouseUp={onPressEnd}
      onMouseLeave={onPressEnd}
      aria-current={isActive ? 'page' : undefined}
    >
      <div className="relative flex flex-col items-center justify-center w-full py-1">
        {/* 
          M3 Active Indicator
          - Width: 56dp
          - Height: 32dp
          - Shape: Pill (16dp radius)
          - Container: secondaryContainer
        */}
        <AnimatePresence>
          {isActive && (
            <motion.div
              layoutId="navRailIndicator"
              initial={{ opacity: 0, scale: 0.8 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.8 }}
              transition={{ duration: 0.3, ease: "easeInOut" }}
              className={`
                absolute
                w-14 h-8 rounded-2xl
                ${isDark 
                  ? 'bg-[#003735]' // secondaryContainer dark
                  : 'bg-[#B2DFDB]' // secondaryContainer light
                }
              `}
            />
          )}
        </AnimatePresence>

        {/* Icon Container - 56dp touch target */}
        <div 
          className={`
            relative z-10
            flex items-center justify-center
            w-14 h-14 rounded-full
            transition-colors duration-150
            ${isActive
              ? isDark 
                ? 'text-[#00E5CD]' // onSecondaryContainer dark
                : 'text-[#003735]' // onSecondaryContainer light
              : isDark
                ? 'text-[#C9C5CA]' // onSurfaceVariant dark
                : 'text-[#49454F]' // onSurfaceVariant light
            }
            ${isPressed && !isActive 
              ? isDark 
                ? 'bg-[#49454F]/50' 
                : 'bg-[#E8E0EC]/50'
              : ''
            }
          `}
        >
          <Icon 
            className="w-6 h-6" 
            strokeWidth={isActive ? 2 : 1.5}
          />

          {/* Badge indicator */}
          {item.badge && (
            <span className="absolute top-2 right-2 flex h-4 w-4 items-center justify-center rounded-full bg-[#EA4335] text-[10px] font-medium text-white">
              {item.badge > 9 ? '9+' : item.badge}
            </span>
          )}
        </div>

        {/* 
          M3 Label
          - Font size: 12sp
          - Weight: Medium
        */}
        <span 
          className={`
            mt-1 text-[12px] font-medium
            transition-colors duration-150
            ${isActive
              ? isDark 
                ? 'text-[#E6E1E5]' // onSurface dark
                : 'text-[#1C1B1F]' // onSurface light
              : isDark
                ? 'text-[#938F99]' // onSurfaceVariant dark
                : 'text-[#49454F]' // onSurfaceVariant light
            }
          `}
        >
          {item.label}
        </span>
      </div>
    </Link>
  );
}
