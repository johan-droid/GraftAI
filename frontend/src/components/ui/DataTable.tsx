/**
 * Mobile-Responsive DataTable Component
 * 
 * Following Material Design 3 principles:
 * - Card-based layout on mobile (< 640px)
 * - Horizontal scroll table on tablet/desktop
 * - Responsive touch targets (min 48dp)
 * - Dark mode support
 * 
 * @see https://m3.material.io/components/data-tables/overview
 */

"use client";

import React, { useState, useCallback, useEffect } from "react";
import {
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  TablePagination,
  TableSortLabel,
  Chip as MuiChip,
  IconButton,
  Tooltip,
  Box,
  Typography,
  TextField,
  InputAdornment,
  Skeleton,
  MenuItem,
  Select,
  FormControl,
  InputLabel,
} from "@mui/material";
import {
  Search,
  Filter,
  RefreshCw,
  ChevronLeft,
  ChevronRight,
  ArrowUpDown,
  MoreVertical,
  Eye,
  Edit,
  Trash2,
} from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";
import { useTheme } from "@/contexts/ThemeContext";
import { useBreakpoint, isCompact } from "@/theme/breakpoints";

const MotionTableRow = motion(TableRow);

// M3 Motion tokens
const m3Motion = {
  standard: { duration: 0.15, ease: "easeOut" as const },
  emphasized: { duration: 0.3, ease: "easeInOut" as const },
};

// Types
export interface Column<T> {
  key: string;
  header: string;
  width?: string | number;
  sortable?: boolean;
  filterable?: boolean;
  render?: (row: T) => React.ReactNode;
  align?: "left" | "center" | "right";
}

export interface DataTableProps<T> {
  columns: Column<T>[];
  data: T[];
  keyExtractor: (row: T) => string;
  title?: string;
  subtitle?: string;
  loading?: boolean;
  searchable?: boolean;
  searchPlaceholder?: string;
  onSearch?: (query: string) => void;
  onRefresh?: () => void;
  onRowClick?: (row: T) => void;
  pagination?: boolean;
  rowsPerPageOptions?: number[];
  defaultRowsPerPage?: number;
  sortable?: boolean;
  emptyState?: {
    title: string;
    description: string;
    action?: React.ReactNode;
  };
  filters?: {
    key: string;
    label: string;
    options: { value: string; label: string }[];
  }[];
  onFilter?: (filters: Record<string, string>) => void;
  actions?: (row: T) => React.ReactNode;
  stickyHeader?: boolean;
  maxHeight?: number | string;
  className?: string;
}

// Status color mapping
const statusColors: Record<string, { bg: string; color: string }> = {
  completed: { bg: "#dcfce7", color: "#166534" },
  success: { bg: "#dcfce7", color: "#166534" },
  pending: { bg: "#fef9c3", color: "#854d0e" },
  in_progress: { bg: "#dbeafe", color: "#1e40af" },
  failed: { bg: "#fee2e2", color: "#991b1b" },
  partial: { bg: "#ffedd5", color: "#9a3412" },
  error: { bg: "#fee2e2", color: "#991b1b" },
  cancelled: { bg: "#f3f4f6", color: "#374151" },
  high: { bg: "#fee2e2", color: "#991b1b" },
  medium: { bg: "#fef9c3", color: "#854d0e" },
  low: { bg: "#dcfce7", color: "#166534" },
  critical: { bg: "#fee2e2", color: "#7f1d1d" },
};

// Utility function to render status chip with dark mode support
export const StatusChip = ({ 
  status, 
  size = "small",
  isDark = false,
}: { 
  status: string; 
  size?: "small" | "medium";
  isDark?: boolean;
}) => {
  const normalizedStatus = status.toLowerCase().replace(/\s+/g, "_");
  const colors = statusColors[normalizedStatus] || { bg: isDark ? "#49454F" : "#f3f4f6", color: isDark ? "#E6E1E5" : "#374151" };
  
  // Dark mode color overrides
  const darkModeColors: Record<string, { bg: string; color: string }> = {
    completed: { bg: "#1E4C30", color: "#84D9A6" },
    success: { bg: "#1E4C30", color: "#84D9A6" },
    pending: { bg: "#5C3B00", color: "#FFDEA2" },
    in_progress: { bg: "#004878", color: "#AAC7FF" },
    failed: { bg: "#5C1009", color: "#FFB4AB" },
    error: { bg: "#5C1009", color: "#FFB4AB" },
    cancelled: { bg: "#49454F", color: "#938F99" },
    high: { bg: "#5C1009", color: "#FFB4AB" },
    medium: { bg: "#5C3B00", color: "#FFDEA2" },
    low: { bg: "#1E4C30", color: "#84D9A6" },
    critical: { bg: "#5C1009", color: "#FFB4AB" },
  };

  const finalColors = isDark && darkModeColors[normalizedStatus] 
    ? darkModeColors[normalizedStatus] 
    : colors;
  
  return (
    <MuiChip
      label={status.replace(/_/g, " ").replace(/\b\w/g, (l) => l.toUpperCase())}
      size={size}
      sx={{
        backgroundColor: finalColors.bg,
        color: finalColors.color,
        fontWeight: 600,
        fontSize: size === "small" ? "0.75rem" : "0.875rem",
        borderRadius: "6px",
        height: size === "small" ? "24px" : "32px",
      }}
    />
  );
};

// Main DataTable Component
export function DataTable<T>({
  columns,
  data,
  keyExtractor,
  title,
  subtitle,
  loading = false,
  searchable = true,
  searchPlaceholder = "Search...",
  onSearch,
  onRefresh,
  onRowClick,
  pagination = true,
  rowsPerPageOptions = [10, 25, 50, 100],
  defaultRowsPerPage = 10,
  sortable = true,
  emptyState,
  filters,
  onFilter,
  actions,
  stickyHeader = true,
  maxHeight = 600,
  className,
}: DataTableProps<T>) {
  const { mode } = useTheme();
  const isDark = mode === "dark";
  const breakpoint = useBreakpoint();
  const isMobile = isCompact(breakpoint);
  
  const [page, setPage] = useState(0);
  const [rowsPerPage, setRowsPerPage] = useState(defaultRowsPerPage);
  const [searchQuery, setSearchQuery] = useState("");
  const [sortConfig, setSortConfig] = useState<{ key: string; direction: "asc" | "desc" } | null>(null);
  const [activeFilters, setActiveFilters] = useState<Record<string, string>>({});
  const [showFilters, setShowFilters] = useState(false);
  const [expandedCard, setExpandedCard] = useState<string | null>(null);
  
  // Use card view on mobile
  const useCardView = isMobile;

  // Handle search
  const handleSearch = useCallback(
    (value: string) => {
      setSearchQuery(value);
      setPage(0);
      onSearch?.(value);
    },
    [onSearch]
  );

  // Handle sort
  const handleSort = useCallback(
    (key: string) => {
      if (!sortable) return;
      
      setSortConfig((current) => {
        if (current?.key === key) {
          return { key, direction: current.direction === "asc" ? "desc" : "asc" };
        }
        return { key, direction: "asc" };
      });
    },
    [sortable]
  );

  // Handle filter
  const handleFilter = useCallback(
    (key: string, value: string) => {
      const newFilters = { ...activeFilters, [key]: value };
      if (!value) delete newFilters[key];
      
      setActiveFilters(newFilters);
      setPage(0);
      onFilter?.(newFilters);
    },
    [activeFilters, onFilter]
  );

  // Filter and sort data
  const processedData = React.useMemo(() => {
    let result = [...data];

    // Apply filters
    if (Object.keys(activeFilters).length > 0) {
      result = result.filter((row) => {
        return Object.entries(activeFilters).every(([key, value]) => {
          const rowValue = (row as any)[key];
          return String(rowValue).toLowerCase() === value.toLowerCase();
        });
      });
    }

    // Apply search
    if (searchQuery && !onSearch) {
      result = result.filter((row) =>
        columns.some((col) => {
          const value = (row as any)[col.key];
          return String(value).toLowerCase().includes(searchQuery.toLowerCase());
        })
      );
    }

    // Apply sort
    if (sortConfig) {
      result.sort((a, b) => {
        const aValue = (a as any)[sortConfig.key];
        const bValue = (b as any)[sortConfig.key];
        
        if (aValue < bValue) return sortConfig.direction === "asc" ? -1 : 1;
        if (aValue > bValue) return sortConfig.direction === "asc" ? 1 : -1;
        return 0;
      });
    }

    return result;
  }, [data, activeFilters, searchQuery, sortConfig, columns, onSearch]);

  // Paginate data
  const paginatedData = React.useMemo(() => {
    if (!pagination) return processedData;
    return processedData.slice(page * rowsPerPage, page * rowsPerPage + rowsPerPage);
  }, [processedData, page, rowsPerPage, pagination]);

  // Empty state - M3 styled
  if (!loading && data.length === 0 && emptyState) {
    return (
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={m3Motion.emphasized}
        className={`
          flex flex-col items-center justify-center py-12 sm:py-16 px-4
          rounded-2xl border
          ${isDark ? "bg-[#1C1B1F] border-[#49454F]" : "bg-white border-[#DADCE0]"}
        `}
      >
        <div className={`
          w-20 h-20 sm:w-24 sm:h-24 rounded-full 
          flex items-center justify-center mb-4
          ${isDark ? "bg-[#49454F] text-[#938F99]" : "bg-[#F8F9FA] text-[#DADCE0]"}
        `}>
          <Search size={32} className="sm:w-10 sm:h-10" />
        </div>
        <h3 className={`text-lg font-semibold mb-2 ${isDark ? "text-[#E6E1E5]" : "text-[#202124]"}`}>
          {emptyState.title}
        </h3>
        <p className={`text-sm sm:text-base text-center mb-4 max-w-md ${isDark ? "text-[#938F99]" : "text-[#5F6368]"}`}>
          {emptyState.description}
        </p>
        {emptyState.action}
      </motion.div>
    );
  }
  
  // Mobile Card View
  if (useCardView && !loading) {
    return (
      <div className={`space-y-3 ${className || ""}`}>
        {/* Mobile Header */}
        <div className="flex items-center justify-between gap-2 mb-4">
          {title && (
            <div>
              <h2 className={`text-lg font-semibold ${isDark ? "text-[#E6E1E5]" : "text-[#202124]"}`}>
                {title}
              </h2>
              {subtitle && (
                <p className={`text-sm ${isDark ? "text-[#938F99]" : "text-[#5F6368]"}`}>
                  {subtitle}
                </p>
              )}
            </div>
          )}
          
          <div className="flex items-center gap-1">
            {onRefresh && (
              <motion.button
                whileTap={{ scale: 0.9 }}
                onClick={onRefresh}
                className={`
                  p-2 rounded-full transition-colors
                  ${isDark ? "hover:bg-[#49454F] text-[#938F99]" : "hover:bg-[#F1F3F4] text-[#5F6368]"}
                `}
              >
                <RefreshCw size={18} />
              </motion.button>
            )}
          </div>
        </div>
        
        {/* Mobile Search */}
        {searchable && (
          <div className={`
            relative mb-4
            ${isDark ? "bg-[#1C1B1F]" : "bg-white"}
            rounded-xl border ${isDark ? "border-[#49454F]" : "border-[#DADCE0]"}
          `}>
            <Search size={18} className={`absolute left-3 top-1/2 -translate-y-1/2 ${isDark ? "text-[#938F99]" : "text-[#5F6368]"}`} />
            <input
              type="text"
              placeholder={searchPlaceholder}
              value={searchQuery}
              onChange={(e) => handleSearch(e.target.value)}
              className={`
                w-full py-3 pl-10 pr-4 rounded-xl
                bg-transparent text-sm
                focus:outline-none focus:ring-2 focus:ring-[#1A73E8]/30
                ${isDark ? "text-[#E6E1E5] placeholder-[#938F99]" : "text-[#202124] placeholder-[#5F6368]"}
              `}
            />
          </div>
        )}
        
        {/* Mobile Cards */}
        <div className="space-y-3">
          {paginatedData.map((row, index) => (
            <motion.div
              key={keyExtractor(row)}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ ...m3Motion.standard, delay: index * 0.05 }}
              whileTap={{ scale: 0.98 }}
              onClick={() => {
                onRowClick?.(row);
                setExpandedCard(expandedCard === keyExtractor(row) ? null : keyExtractor(row));
              }}
              className={`
                rounded-xl p-4
                border transition-all
                ${isDark 
                  ? "bg-[#1C1B1F] border-[#49454F] active:bg-[#2D2D30]" 
                  : "bg-white border-[#DADCE0] active:bg-[#F8F9FA]"
                }
                ${onRowClick ? "cursor-pointer" : ""}
              `}
            >
              {/* Card Header - First column as title */}
              <div className="flex items-start justify-between gap-3 mb-3">
                <div className="flex-1 min-w-0">
                  <h3 className={`font-semibold truncate ${isDark ? "text-[#E6E1E5]" : "text-[#202124]"}`}>
                    {columns[0]?.render 
                      ? columns[0].render(row) 
                      : (row as any)[columns[0]?.key]}
                  </h3>
                </div>
                {actions && (
                  <div className="flex items-center gap-1 shrink-0">
                    {actions(row)}
                  </div>
                )}
              </div>
              
              {/* Card Body - Remaining columns */}
              <div className="grid grid-cols-2 gap-2">
                {columns.slice(1).map((column) => (
                  <div key={column.key} className="min-w-0">
                    <p className={`text-xs mb-0.5 ${isDark ? "text-[#938F99]" : "text-[#5F6368]"}`}>
                      {column.header}
                    </p>
                    <p className={`text-sm font-medium truncate ${isDark ? "text-[#C9C5CA]" : "text-[#1D1B20]"}`}>
                      {column.render 
                        ? column.render(row) 
                        : (row as any)[column.key]}
                    </p>
                  </div>
                ))}
              </div>
            </motion.div>
          ))}
        </div>
        
        {/* Mobile Pagination */}
        {pagination && processedData.length > 0 && (
          <div className={`
            flex items-center justify-between mt-4 pt-4 border-t
            ${isDark ? "border-[#49454F]" : "border-[#F1F3F4]"}
          `}>
            <button
              onClick={() => setPage(Math.max(0, page - 1))}
              disabled={page === 0}
              className={`
                p-2 rounded-full transition-colors
                ${page === 0 
                  ? "opacity-50 cursor-not-allowed" 
                  : isDark ? "hover:bg-[#49454F] text-[#E6E1E5]" : "hover:bg-[#F1F3F4] text-[#202124]"
                }
              `}
            >
              <ChevronLeft size={20} />
            </button>
            
            <span className={`text-sm ${isDark ? "text-[#938F99]" : "text-[#5F6368]"}`}>
              {page * rowsPerPage + 1} - {Math.min((page + 1) * rowsPerPage, processedData.length)} of {processedData.length}
            </span>
            
            <button
              onClick={() => setPage(Math.min(Math.ceil(processedData.length / rowsPerPage) - 1, page + 1))}
              disabled={page >= Math.ceil(processedData.length / rowsPerPage) - 1}
              className={`
                p-2 rounded-full transition-colors
                ${page >= Math.ceil(processedData.length / rowsPerPage) - 1
                  ? "opacity-50 cursor-not-allowed" 
                  : isDark ? "hover:bg-[#49454F] text-[#E6E1E5]" : "hover:bg-[#F1F3F4] text-[#202124]"
                }
              `}
            >
              <ChevronRight size={20} />
            </button>
          </div>
        )}
      </div>
    );
  }

  return (
    <Paper
      elevation={0}
      className={`overflow-hidden border border-[hsl(var(--border))] rounded-xl ${className || ""}`}
      sx={{ backgroundColor: "hsl(var(--card))" }}
    >
      {/* Header */}
      {(title || searchable || onRefresh || filters) && (
        <Box className="p-4 border-b border-[hsl(var(--border))]">
          <Box className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
            {/* Title */}
            {title && (
              <Box>
                <Typography variant="h6" className="font-semibold">
                  {title}
                </Typography>
                {subtitle && (
                  <Typography variant="body2" color="text.secondary">
                    {subtitle}
                  </Typography>
                )}
              </Box>
            )}

            {/* Controls */}
            <Box className="flex items-center gap-2 flex-wrap">
              {/* Search */}
              {searchable && (
                <TextField
                  size="small"
                  placeholder={searchPlaceholder}
                  value={searchQuery}
                  onChange={(e) => handleSearch(e.target.value)}
                  InputProps={{
                    startAdornment: (
                      <InputAdornment position="start">
                        <Search size={18} />
                      </InputAdornment>
                    ),
                  }}
                  sx={{ minWidth: 200 }}
                />
              )}

              {/* Filter Toggle */}
              {filters && filters.length > 0 && (
                <Tooltip title="Toggle Filters">
                  <IconButton
                    onClick={() => setShowFilters(!showFilters)}
                    color={showFilters ? "primary" : "default"}
                    size="small"
                  >
                    <Filter size={20} />
                  </IconButton>
                </Tooltip>
              )}

              {/* Refresh */}
              {onRefresh && (
                <Tooltip title="Refresh">
                  <IconButton onClick={onRefresh} size="small">
                    <RefreshCw size={20} />
                  </IconButton>
                </Tooltip>
              )}
            </Box>
          </Box>

          {/* Filters */}
          <AnimatePresence>
            {showFilters && filters && (
              <motion.div
                initial={{ height: 0, opacity: 0 }}
                animate={{ height: "auto", opacity: 1 }}
                exit={{ height: 0, opacity: 0 }}
                className="overflow-hidden"
              >
                <Box className="flex gap-3 mt-4 pt-4 border-t border-[hsl(var(--border))] flex-wrap">
                  {filters.map((filter) => (
                    <FormControl key={filter.key} size="small" sx={{ minWidth: 150 }}>
                      <InputLabel>{filter.label}</InputLabel>
                      <Select
                        value={activeFilters[filter.key] || ""}
                        onChange={(e) => handleFilter(filter.key, e.target.value)}
                        label={filter.label}
                      >
                        <MenuItem value="">
                          <em>All</em>
                        </MenuItem>
                        {filter.options.map((option) => (
                          <MenuItem key={option.value} value={option.value}>
                            {option.label}
                          </MenuItem>
                        ))}
                      </Select>
                    </FormControl>
                  ))}
                </Box>
              </motion.div>
            )}
          </AnimatePresence>
        </Box>
      )}

      {/* Table */}
      <TableContainer sx={{ maxHeight }}>
        <Table stickyHeader={stickyHeader} size="small">
          <TableHead>
            <TableRow>
              {columns.map((column) => (
                <TableCell
                  key={column.key}
                  align={column.align || "left"}
                  sx={{
                    width: column.width,
                    fontWeight: 600,
                    backgroundColor: "hsl(var(--muted))",
                    color: "hsl(var(--muted-foreground))",
                    whiteSpace: "nowrap",
                  }}
                >
                  {column.sortable && sortable ? (
                    <TableSortLabel
                      active={sortConfig?.key === column.key}
                      direction={sortConfig?.key === column.key ? sortConfig.direction : "asc"}
                      onClick={() => handleSort(column.key)}
                      IconComponent={ArrowUpDown}
                    >
                      {column.header}
                    </TableSortLabel>
                  ) : (
                    column.header
                  )}
                </TableCell>
              ))}
              {actions && (
                <TableCell
                  align="right"
                  sx={{
                    fontWeight: 600,
                    backgroundColor: "hsl(var(--muted))",
                    color: "hsl(var(--muted-foreground))",
                  }}
                >
                  Actions
                </TableCell>
              )}
            </TableRow>
          </TableHead>
          <TableBody>
            {loading ? (
              // Loading skeleton
              Array.from({ length: 5 }).map((_, index) => (
                <TableRow key={`skeleton-${index}`}>
                  {columns.map((_, colIndex) => (
                    <TableCell key={colIndex}>
                      <Skeleton variant="text" width="80%" />
                    </TableCell>
                  ))}
                  {actions && <TableCell><Skeleton variant="text" width={40} /></TableCell>}
                </TableRow>
              ))
            ) : (
              // Data rows
              paginatedData.map((row, index) => (
                <MotionTableRow
                  key={keyExtractor(row)}
                  initial={{ opacity: 0, x: -20 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: index * 0.05 }}
                  hover={!!onRowClick}
                  onClick={() => onRowClick?.(row)}
                  sx={{
                    cursor: onRowClick ? "pointer" : "default",
                    transition: "background-color 0.15s ease",
                  }}
                >
                  {columns.map((column) => (
                    <TableCell
                      key={`${keyExtractor(row)}-${column.key}`}
                      align={column.align || "left"}
                    >
                      {column.render
                        ? column.render(row)
                        : (row as any)[column.key]}
                    </TableCell>
                  ))}
                  {actions && (
                    <TableCell align="right">
                      <Box className="flex justify-end gap-1">
                        {actions(row)}
                      </Box>
                    </TableCell>
                  )}
                </MotionTableRow>
              ))
            )}
          </TableBody>
        </Table>
      </TableContainer>

      {/* Pagination */}
      {pagination && processedData.length > 0 && (
        <TablePagination
          component="div"
          count={processedData.length}
          page={page}
          onPageChange={(_, newPage) => setPage(newPage)}
          rowsPerPage={rowsPerPage}
          onRowsPerPageChange={(e) => {
            setRowsPerPage(parseInt(e.target.value, 10));
            setPage(0);
          }}
          rowsPerPageOptions={rowsPerPageOptions}
          backIconButtonProps={{ children: <ChevronLeft size={20} /> }}
          nextIconButtonProps={{ children: <ChevronRight size={20} /> }}
          sx={{
            borderTop: "1px solid hsl(var(--border))",
            backgroundColor: "hsl(var(--card))",
          }}
        />
      )}
    </Paper>
  );
}

export default DataTable;
