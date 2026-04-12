"use client";

import { apiClient, API_BASE_URL } from "./api-client";

// ═══════════════════════════════════════════════════════════════════
// TYPES
// ═══════════════════════════════════════════════════════════════════

export interface RetryConfig {
  maxRetries: number;
  retryDelay: number;
  retryDelayMultiplier: number;
  maxRetryDelay: number;
  retryableStatuses: number[];
}

export interface RequestQueueItem {
  id: string;
  endpoint: string;
  method: string;
  body?: unknown;
  retryCount: number;
  timestamp: number;
  priority: "high" | "normal" | "low";
}

export interface NetworkState {
  isOnline: boolean;
  connectionType?: string;
  downlink?: number;
  rtt?: number;
}

// ═══════════════════════════════════════════════════════════════════
// CONFIGURATION
// ═══════════════════════════════════════════════════════════════════

const DEFAULT_RETRY_CONFIG: RetryConfig = {
  maxRetries: 3,
  retryDelay: 1000,
  retryDelayMultiplier: 2,
  maxRetryDelay: 30000,
  retryableStatuses: [408, 429, 500, 502, 503, 504],
};

// ═══════════════════════════════════════════════════════════════════
// RETRY LOGIC
// ═══════════════════════════════════════════════════════════════════

export class RetryableError extends Error {
  constructor(
    message: string,
    public statusCode: number,
    public retryAfter?: number
  ) {
    super(message);
    this.name = "RetryableError";
  }
}

export function isRetryableError(error: unknown, config: RetryConfig = DEFAULT_RETRY_CONFIG): boolean {
  if (error instanceof RetryableError) {
    return config.retryableStatuses.includes(error.statusCode);
  }
  
  // Network errors are retryable
  if (error instanceof TypeError && error.message.includes("fetch")) {
    return true;
  }
  
  // Check for network errors
  if (error instanceof Error) {
    const networkErrors = ["Failed to fetch", "NetworkError", "AbortError", "ECONNREFUSED", "ETIMEDOUT"];
    return networkErrors.some((e) => error.message.includes(e));
  }
  
  return false;
}

export function calculateRetryDelay(
  retryCount: number,
  config: RetryConfig = DEFAULT_RETRY_CONFIG,
  retryAfter?: number
): number {
  // Use server-provided retry-after if available
  if (retryAfter) {
    return retryAfter * 1000;
  }
  
  // Exponential backoff with jitter
  const baseDelay = config.retryDelay * Math.pow(config.retryDelayMultiplier, retryCount);
  const jitter = Math.random() * 0.3 * baseDelay; // 30% jitter
  const delay = Math.min(baseDelay + jitter, config.maxRetryDelay);
  
  return Math.round(delay);
}

export async function sleep(ms: number): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

// ═══════════════════════════════════════════════════════════════════
// OFFLINE QUEUE
// ═══════════════════════════════════════════════════════════════════

class OfflineQueue {
  private queue: RequestQueueItem[] = [];
  private listeners: Set<(queue: RequestQueueItem[]) => void> = new Set();
  private storageKey = "graftai_offline_queue";

  constructor() {
    this.loadFromStorage();
    
    // Listen for online events
    if (typeof window !== "undefined") {
      window.addEventListener("online", () => this.processQueue());
    }
  }

  private loadFromStorage(): void {
    if (typeof window === "undefined") return;
    
    try {
      const stored = localStorage.getItem(this.storageKey);
      if (stored) {
        this.queue = JSON.parse(stored);
        this.notifyListeners();
      }
    } catch (e) {
      console.error("Failed to load offline queue:", e);
    }
  }

  private saveToStorage(): void {
    if (typeof window === "undefined") return;
    
    try {
      localStorage.setItem(this.storageKey, JSON.stringify(this.queue));
    } catch (e) {
      console.error("Failed to save offline queue:", e);
    }
  }

  private notifyListeners(): void {
    this.listeners.forEach((listener) => listener([...this.queue]))
  }

  add(item: Omit<RequestQueueItem, "id" | "timestamp" | "retryCount">): string {
    const queueItem: RequestQueueItem = {
      ...item,
      id: `${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
      timestamp: Date.now(),
      retryCount: 0,
    };
    
    this.queue.push(queueItem);
    this.saveToStorage();
    this.notifyListeners();
    
    return queueItem.id;
  }

  remove(id: string): void {
    this.queue = this.queue.filter((item) => item.id !== id);
    this.saveToStorage();
    this.notifyListeners();
  }

  update(id: string, updates: Partial<RequestQueueItem>): void {
    const index = this.queue.findIndex((item) => item.id === id);
    if (index !== -1) {
      this.queue[index] = { ...this.queue[index], ...updates };
      this.saveToStorage();
      this.notifyListeners();
    }
  }

  getAll(): RequestQueueItem[] {
    return [...this.queue];
  }

  get length(): number {
    return this.queue.length;
  }

  clear(): void {
    this.queue = [];
    this.saveToStorage();
    this.notifyListeners();
  }

  subscribe(listener: (queue: RequestQueueItem[]) => void): () => void {
    this.listeners.add(listener);
    return () => this.listeners.delete(listener);
  }

  private async processQueue(): Promise<void> {
    if (!navigator.onLine || this.queue.length === 0) return;
    
    // Sort by priority and timestamp
    const sorted = [...this.queue].sort((a, b) => {
      const priorityOrder = { high: 0, normal: 1, low: 2 };
      if (priorityOrder[a.priority] !== priorityOrder[b.priority]) {
        return priorityOrder[a.priority] - priorityOrder[b.priority];
      }
      return a.timestamp - b.timestamp;
    });
    
    for (const item of sorted) {
      try {
        await apiClient.fetch(item.endpoint, {
          method: item.method,
          json: item.body,
        });
        this.remove(item.id);
      } catch (e) {
        console.error(`Failed to process queued request ${item.id}:`, e);
        
        // Increment retry count
        this.update(item.id, {
          retryCount: item.retryCount + 1,
        });
        
        // Remove if max retries exceeded
        if (item.retryCount >= 3) {
          this.remove(item.id);
        }
      }
    }
  }
}

export const offlineQueue = new OfflineQueue();

// ═══════════════════════════════════════════════════════════════════
// NETWORK MONITOR
// ═══════════════════════════════════════════════════════════════════

class NetworkMonitor {
  private state: NetworkState = { isOnline: true };
  private listeners: Set<(state: NetworkState) => void> = new Set();

  constructor() {
    if (typeof window !== "undefined") {
      this.state.isOnline = navigator.onLine;
      
      window.addEventListener("online", () => this.updateState({ isOnline: true }));
      window.addEventListener("offline", () => this.updateState({ isOnline: false }));
      
      // Monitor connection quality if available
      if ("connection" in navigator) {
        const connection = (navigator as any).connection;
        if (connection) {
          connection.addEventListener("change", () => this.updateConnectionInfo());
          this.updateConnectionInfo();
        }
      }
    }
  }

  private updateConnectionInfo(): void {
    if ("connection" in navigator) {
      const connection = (navigator as any).connection;
      this.updateState({
        connectionType: connection?.effectiveType,
        downlink: connection?.downlink,
        rtt: connection?.rtt,
      });
    }
  }

  private updateState(updates: Partial<NetworkState>): void {
    this.state = { ...this.state, ...updates };
    this.listeners.forEach((listener) => listener(this.state));
  }

  getState(): NetworkState {
    return { ...this.state };
  }

  isOnline(): boolean {
    return this.state.isOnline;
  }

  subscribe(listener: (state: NetworkState) => void): () => void {
    this.listeners.add(listener);
    listener(this.state); // Initial state
    return () => this.listeners.delete(listener);
  }
}

export const networkMonitor = new NetworkMonitor();

// ═══════════════════════════════════════════════════════════════════
// ENHANCED API CLIENT
// ═══════════════════════════════════════════════════════════════════

export interface EnhancedApiOptions {
  retry?: Partial<RetryConfig>;
  offlineQueue?: boolean;
  priority?: "high" | "normal" | "low";
  signal?: AbortSignal;
}

export const enhancedApiClient = {
  async fetchWithRetry<T>(
    endpoint: string,
    options: EnhancedApiOptions & { method?: string; json?: unknown } = {}
  ): Promise<T> {
    const retryConfig = { ...DEFAULT_RETRY_CONFIG, ...options.retry };
    let lastError: Error | unknown;
    
    for (let attempt = 0; attempt <= retryConfig.maxRetries; attempt++) {
      try {
        return await apiClient.fetch(endpoint, {
          method: options.method,
          json: options.json,
          signal: options.signal,
        });
      } catch (error) {
        lastError = error;
        
        // Don't retry on last attempt
        if (attempt === retryConfig.maxRetries) {
          break;
        }
        
        // Check if error is retryable
        if (!isRetryableError(error, retryConfig)) {
          throw error;
        }
        
        // Calculate and apply delay
        const retryAfter = error instanceof RetryableError ? error.retryAfter : undefined;
        const delay = calculateRetryDelay(attempt, retryConfig, retryAfter);
        
        console.log(`Retrying ${endpoint} after ${delay}ms (attempt ${attempt + 1}/${retryConfig.maxRetries})`);
        await sleep(delay);
      }
    }
    
    throw lastError;
  },

  async fetchWithOfflineSupport<T>(
    endpoint: string,
    options: EnhancedApiOptions & { method?: string; json?: unknown } = {}
  ): Promise<T> {
    // If offline and queue enabled, add to queue for mutations
    if (!networkMonitor.isOnline() && options.offlineQueue && options.method && options.method !== "GET") {
      const id = offlineQueue.add({
        endpoint,
        method: options.method,
        body: options.json,
        priority: options.priority || "normal",
      });
      
      // Return a promise that resolves when online
      return new Promise((resolve, reject) => {
        const checkOnline = () => {
          if (networkMonitor.isOnline()) {
            // Try to execute immediately
            this.fetchWithRetry<T>(endpoint, { ...options, offlineQueue: false })
              .then((result) => {
                offlineQueue.remove(id);
                resolve(result);
              })
              .catch(reject);
          }
        };
        
        const unsubscribe = networkMonitor.subscribe((state) => {
          if (state.isOnline) {
            unsubscribe();
            checkOnline();
          }
        });
        
        // Return queue info for UI
        resolve({
          queued: true,
          id,
          message: "Request queued for when you're back online",
        } as unknown as T);
      });
    }
    
    // Normal execution with retry
    return this.fetchWithRetry<T>(endpoint, options);
  },

  // Convenience methods
  async get<T>(endpoint: string, options: EnhancedApiOptions = {}): Promise<T> {
    return this.fetchWithOfflineSupport<T>(endpoint, { ...options, method: "GET" });
  },

  async post<T>(
    endpoint: string,
    body?: unknown,
    options: EnhancedApiOptions = {}
  ): Promise<T> {
    return this.fetchWithOfflineSupport<T>(endpoint, { ...options, method: "POST", json: body });
  },

  async patch<T>(
    endpoint: string,
    body?: unknown,
    options: EnhancedApiOptions = {}
  ): Promise<T> {
    return this.fetchWithOfflineSupport<T>(endpoint, { ...options, method: "PATCH", json: body });
  },

  async delete<T>(endpoint: string, options: EnhancedApiOptions = {}): Promise<T> {
    return this.fetchWithOfflineSupport<T>(endpoint, { ...options, method: "DELETE" });
  },

  // Upload with progress
  async upload<T>(
    endpoint: string,
    formData: FormData,
    onProgress?: (progress: number) => void,
    options: EnhancedApiOptions = {}
  ): Promise<T> {
    return new Promise((resolve, reject) => {
      const xhr = new XMLHttpRequest();
      
      xhr.upload.addEventListener("progress", (e) => {
        if (e.lengthComputable && onProgress) {
          onProgress((e.loaded / e.total) * 100);
        }
      });
      
      xhr.addEventListener("load", () => {
        if (xhr.status >= 200 && xhr.status < 300) {
          try {
            resolve(JSON.parse(xhr.responseText));
          } catch {
            resolve(xhr.responseText as unknown as T);
          }
        } else {
          reject(new Error(`Upload failed: ${xhr.statusText}`));
        }
      });
      
      xhr.addEventListener("error", () => {
        reject(new Error("Upload failed"));
      });
      
      xhr.addEventListener("abort", () => {
        reject(new Error("Upload aborted"));
      });
      
      xhr.open("POST", `${API_BASE_URL}${endpoint}`);
      
      // Add auth token
      const token = typeof window !== "undefined"
        ? localStorage.getItem("token") || localStorage.getItem("graftai_access_token")
        : null;
      if (token) {
        xhr.setRequestHeader("Authorization", `Bearer ${token}`);
      }
      
      xhr.send(formData);
    });
  },
};

// ═══════════════════════════════════════════════════════════════════
// REACT HOOKS
// ═══════════════════════════════════════════════════════════════════

import { useState, useEffect, useCallback, useRef } from "react";

export function useNetworkState() {
  const [state, setState] = useState<NetworkState>(networkMonitor.getState());
  
  useEffect(() => {
    return networkMonitor.subscribe(setState);
  }, []);
  
  return state;
}

export function useOfflineQueue() {
  const [queue, setQueue] = useState<RequestQueueItem[]>([]);
  
  useEffect(() => {
    setQueue(offlineQueue.getAll());
    return offlineQueue.subscribe(setQueue);
  }, []);
  
  return {
    queue,
    length: queue.length,
    clear: useCallback(() => offlineQueue.clear(), []),
  };
}

export function useRetryableRequest<T>(
  requestFn: () => Promise<T>,
  options: {
    retry?: Partial<RetryConfig>;
    onSuccess?: (data: T) => void;
    onError?: (error: Error) => void;
  } = {}
) {
  const [data, setData] = useState<T | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<Error | null>(null);
  const [retryCount, setRetryCount] = useState(0);
  const abortControllerRef = useRef<AbortController | null>(null);

  const execute = useCallback(async () => {
    setLoading(true);
    setError(null);
    setRetryCount(0);
    
    abortControllerRef.current = new AbortController();
    const retryConfig = { ...DEFAULT_RETRY_CONFIG, ...options.retry };
    
    for (let attempt = 0; attempt <= retryConfig.maxRetries; attempt++) {
      try {
        const result = await requestFn();
        setData(result);
        options.onSuccess?.(result);
        setLoading(false);
        return result;
      } catch (err) {
        if (abortControllerRef.current.signal.aborted) {
          setLoading(false);
          throw err;
        }
        
        const isRetryable = isRetryableError(err, retryConfig);
        const isLastAttempt = attempt === retryConfig.maxRetries;
        
        if (!isRetryable || isLastAttempt) {
          const error = err instanceof Error ? err : new Error(String(err));
          setError(error);
          options.onError?.(error);
          setLoading(false);
          throw error;
        }
        
        setRetryCount(attempt + 1);
        const delay = calculateRetryDelay(attempt, retryConfig);
        await sleep(delay);
      }
    }
  }, [requestFn, options.retry, options.onSuccess, options.onError]);

  const cancel = useCallback(() => {
    abortControllerRef.current?.abort();
  }, []);

  useEffect(() => {
    return () => {
      cancel();
    };
  }, [cancel]);

  return { data, loading, error, retryCount, execute, cancel };
}

export default enhancedApiClient;
