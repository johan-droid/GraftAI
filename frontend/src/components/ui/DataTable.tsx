"use client";

import React, { useState, useCallback } from "react";
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
  Chip,
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
} from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";

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

// Utility function to render status chip
export const StatusChip = ({ status, size = "small" }: { status: string; size?: "small" | "medium" }) => {
  const normalizedStatus = status.toLowerCase().replace(/\s+/g, "_");
  const colors = statusColors[normalizedStatus] || { bg: "#f3f4f6", color: "#374151" };
  
  return (
    <Chip
      label={status.replace(/_/g, " ").replace(/\b\w/g, (l) => l.toUpperCase())}
      size={size}
      sx={{
        backgroundColor: colors.bg,
        color: colors.color,
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
  const [page, setPage] = useState(0);
  const [rowsPerPage, setRowsPerPage] = useState(defaultRowsPerPage);
  const [searchQuery, setSearchQuery] = useState("");
  const [sortConfig, setSortConfig] = useState<{ key: string; direction: "asc" | "desc" } | null>(null);
  const [activeFilters, setActiveFilters] = useState<Record<string, string>>({});
  const [showFilters, setShowFilters] = useState(false);

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

  // Empty state
  if (!loading && data.length === 0 && emptyState) {
    return (
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="flex flex-col items-center justify-center py-16 px-4"
      >
        <Box
          sx={{
            width: 120,
            height: 120,
            borderRadius: "50%",
            backgroundColor: "hsl(var(--muted))",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            mb: 3,
          }}
        >
          <Search size={48} color="hsl(var(--muted-foreground))" />
        </Box>
        <Typography variant="h6" className="text-center mb-2 font-semibold">
          {emptyState.title}
        </Typography>
        <Typography variant="body2" color="text.secondary" className="text-center mb-4 max-w-md">
          {emptyState.description}
        </Typography>
        {emptyState.action}
      </motion.div>
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
                <motion.tr
                  key={keyExtractor(row)}
                  initial={{ opacity: 0, x: -20 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: index * 0.05 }}
                  component={TableRow}
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
                </motion.tr>
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
