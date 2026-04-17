/**
 * Material Design 3 Navigation Drawer
 * 
 * Standard/modal side navigation for desktop:
 * - Width: 360dp
 * - Two-section layout (Menu above, favorites below)
 * - Optional header with branding
 * - Active indicator: full-width container highlight
 * 
 * @see https://m3.material.io/components/navigation-drawer/overview
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
  Plus,
  ChevronLeft,
  X
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
  section?: 'primary' | 'secondary';
}

interface NavDrawerProps {
  isOpen?: boolean;
  onClose?: () => void;
  variant?: 'standard' | 'modal' | 'dismissible';
  showHeader?: boolean;
}

// Navigation destinations organized by section
const navItems: NavItem[] = [
  // Primary section
  { id: 'home', icon: Home, label: 'Dashboard', href: '/dashboard', section: 'primary' },
  { id: 'calendar', icon: Calendar, label: 'Calendar', href: '/dashboard/calendar', section: 'primary' },
  { id: 'bookings', icon: Plus, label: 'New Booking', href: '/dashboard/book', section: 'primary' },
  { id: 'ai', icon: Sparkles, label: 'AI Assistant', href: '/dashboard/ai', section: 'primary' },
  
  // Secondary section
  { id: 'teams', icon: Users, label: 'Team Management', href: '/dashboard/teams', section: 'secondary' },
  { id: 'analytics', icon: BarChart3, label: 'Analytics', href: '/dashboard/analytics', section: 'secondary' },
  { id: 'settings', icon: Settings, label: 'Settings', href: '/dashboard/settings', section: 'secondary' },
];

// Filter by section
const primaryItems = navItems.filter(item => item.section === 'primary');
const secondaryItems = navItems.filter(item => item.section === 'secondary');

export default function NavDrawer({
  isOpen = true,
  onClose,
  variant = 'standard',
  showHeader = true
}: NavDrawerProps) {
  const pathname = usePathname();
  const { mode } = useTheme();
  const isDark = mode === 'dark';
  const [pressedItem, setPressedItem] = useState<string | null>(null);

  // Get active item
  const activeItem = navItems.find(item => 
    pathname === item.href || pathname.startsWith(item.href + '/')
  ) || navItems[0];

  const isModal = variant === 'modal';
  const isDismissible = variant === 'dismissible';

  const drawerContent = (
    <div 
      className={`
        h-full flex flex-col
        ${isDark 
          ? 'bg-[#1C1B1F]' 
          : 'bg-[#F2F2F4]'
        }
      `}
      style={{
        // M3 Navigation Drawer: 360dp width
        width: variant === 'standard' ? '360px' : '320px',
      }}
    >
      {/* Header Section */}
      {showHeader && (
        <div 
          className={`
            flex items-center gap-3 px-4 py-6
            ${isDark 
              ? 'border-b border-[#49454F]' 
              : 'border-b border-[#E6E1E5]'
            }
          `}
        >
          {/* Close button for modal/dismissible */}
          {(isModal || isDismissible) && onClose && (
            <motion.button
              whileTap={{ scale: 0.95 }}
              onClick={onClose}
              className={`
                w-10 h-10 rounded-full
                flex items-center justify-center
                transition-colors duration-150
                ${isDark
                  ? 'hover:bg-[#49454F] text-[#E6E1E5]'
                  : 'hover:bg-[#E8E0EC] text-[#1C1B1F]'
                }
              `}
              aria-label="Close navigation"
            >
              <X className="w-5 h-5" strokeWidth={1.5} />
            </motion.button>
          )}
          
          {/* Brand/Logo area */}
          <div className="flex items-center gap-3">
            <div className={`
              w-10 h-10 rounded-xl flex items-center justify-center
              ${isDark 
                ? 'bg-[#1A73E8]' 
                : 'bg-[#1A73E8]'
              }
            `}>
              <Sparkles className="w-5 h-5 text-white" />
            </div>
            <div>
              <h1 className={`
                text-lg font-medium
                ${isDark ? 'text-[#E6E1E5]' : 'text-[#1C1B1F]'}
              `}>
                GraftAI
              </h1>
              <p className={`
                text-xs
                ${isDark ? 'text-[#938F99]' : 'text-[#49454F]'}
              `}>
                Smart Scheduling
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Scrollable content */}
      <div className="flex-1 overflow-y-auto py-2">
        {/* Primary Section */}
        <nav className="px-3" aria-label="Main navigation">
          <ul className="space-y-1">
            {primaryItems.map((item) => (
              <NavDrawerItem
                key={item.id}
                item={item}
                isActive={activeItem.id === item.id}
                isPressed={pressedItem === item.id}
                isDark={isDark}
                onPressStart={() => setPressedItem(item.id)}
                onPressEnd={() => setPressedItem(null)}
              />
            ))}
          </ul>
        </nav>

        {/* Divider */}
        <div className={`
          my-4 mx-4 h-px
          ${isDark ? 'bg-[#49454F]' : 'bg-[#E6E1E5]'}
        `} />

        {/* Secondary Section */}
        <nav className="px-3" aria-label="Secondary navigation">
          <ul className="space-y-1">
            {secondaryItems.map((item) => (
              <NavDrawerItem
                key={item.id}
                item={item}
                isActive={activeItem.id === item.id}
                isPressed={pressedItem === item.id}
                isDark={isDark}
                onPressStart={() => setPressedItem(item.id)}
                onPressEnd={() => setPressedItem(null)}
              />
            ))}
          </ul>
        </nav>
      </div>

      {/* Footer - optional */}
      <div className={`
        px-4 py-4
        ${isDark 
          ? 'border-t border-[#49454F]' 
          : 'border-t border-[#E6E1E5]'
        }
      `}>
        <p className={`
          text-xs
          ${isDark ? 'text-[#938F99]' : 'text-[#49454F]'}
        `}>
          Version 1.0.0
        </p>
      </div>
    </div>
  );

  // Modal variant with backdrop
  if (isModal) {
    return (
      <AnimatePresence>
        {isOpen && (
          <>
            {/* Backdrop */}
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              transition={{ duration: 0.15 }}
              onClick={onClose}
              className="fixed inset-0 z-40 bg-black/50"
              aria-hidden="true"
            />
            
            {/* Drawer */}
            <motion.aside
              initial={{ x: '-100%' }}
              animate={{ x: 0 }}
              exit={{ x: '-100%' }}
              transition={{ duration: 0.3, ease: "easeInOut" }}
              className="fixed left-0 top-0 bottom-0 z-50 shadow-2xl"
            >
              {drawerContent}
            </motion.aside>
          </>
        )}
      </AnimatePresence>
    );
  }

  // Standard or dismissible variant
  return (
    <aside 
      className={`
        fixed left-0 top-0 bottom-0 z-30
        hidden expanded:flex
        ${isDismissible && !isOpen ? '-translate-x-full' : ''}
        transition-transform duration-300 ease-in-out
      `}
    >
      {drawerContent}
    </aside>
  );
}

// Individual drawer item component
interface NavDrawerItemProps {
  item: NavItem;
  isActive: boolean;
  isPressed: boolean;
  isDark: boolean;
  onPressStart: () => void;
  onPressEnd: () => void;
}

function NavDrawerItem({ 
  item, 
  isActive, 
  isPressed, 
  isDark,
  onPressStart,
  onPressEnd 
}: NavDrawerItemProps) {
  const Icon = item.icon;

  return (
    <li>
      <Link
        href={item.href}
        className={`
          relative flex items-center gap-4
          px-4 py-3 rounded-full
          transition-all duration-150
          ${isActive
            ? isDark 
              ? 'bg-[#004878] text-[#AAC7FF]' // secondaryContainer dark
              : 'bg-[#E8F0FE] text-[#1967D2]' // secondaryContainer light
            : isDark
              ? 'text-[#C9C5CA] hover:bg-[#49454F]/50' // onSurfaceVariant dark
              : 'text-[#49454F] hover:bg-[#E8E0EC]/50' // onSurfaceVariant light
          }
          ${isPressed && !isActive 
            ? isDark 
              ? 'bg-[#49454F]/70' 
              : 'bg-[#E8E0EC]/70'
            : ''
          }
        `}
        onTouchStart={onPressStart}
        onTouchEnd={onPressEnd}
        onMouseDown={onPressStart}
        onMouseUp={onPressEnd}
        onMouseLeave={onPressEnd}
        aria-current={isActive ? 'page' : undefined}
      >
        {/* Icon */}
        <div className={`
          flex items-center justify-center
          w-6 h-6
        `}>
          <Icon 
            className="w-6 h-6" 
            strokeWidth={isActive ? 2 : 1.5}
          />
        </div>

        {/* Label */}
        <span className={`
          flex-1 text-sm font-medium
          ${isActive
            ? isDark 
              ? 'text-[#E6E1E5]' // onSurface dark
              : 'text-[#1C1B1F]' // onSurface light
            : isDark
              ? 'text-[#C9C5CA]' // onSurfaceVariant dark
              : 'text-[#49454F]' // onSurfaceVariant light
          }
        `}>
          {item.label}
        </span>

        {/* Badge */}
        {item.badge && (
          <span className="flex h-5 min-w-[20px] items-center justify-center rounded-full bg-[#EA4335] text-[11px] font-medium text-white px-1.5">
            {item.badge > 99 ? '99+' : item.badge}
          </span>
        )}

        {/* Active indicator bar (left side) */}
        {isActive && (
          <motion.div
            layoutId="drawerActiveIndicator"
            className={`
              absolute left-0 top-1/2 -translate-y-1/2
              w-1 h-6 rounded-full
              ${isDark ? 'bg-[#AAC7FF]' : 'bg-[#1967D2]'}
            `}
            transition={{ duration: 0.2 }}
          />
        )}
      </Link>
    </li>
  );
}
