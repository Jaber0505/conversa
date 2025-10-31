import { Injectable } from '@angular/core';

export interface RateLimitConfig {
  maxAttempts: number;
  windowMs: number; // Time window in milliseconds
}

interface RateLimitEntry {
  attempts: number[];
}

@Injectable({ providedIn: 'root' })
export class RateLimiterService {
  private limits: Map<string, RateLimitEntry> = new Map();

  private readonly configs: Record<string, RateLimitConfig> = {
    // Sync with backend: auth_login = 10/min
    login: { maxAttempts: 10, windowMs: 60 * 1000 }, // 10 attempts per minute
    // Sync with backend: auth_register = 5/hour
    register: { maxAttempts: 5, windowMs: 60 * 60 * 1000 }, // 5 attempts per hour
    // Generic rate limits
    search: { maxAttempts: 30, windowMs: 60 * 1000 }, // 30 searches per minute
  };

  /**
   * Check if an action is allowed based on rate limiting
   * Returns true if allowed, false if rate limit exceeded
   */
  isAllowed(action: string): boolean {
    const config = this.configs[action];
    if (!config) {
      console.warn(`Rate limit config not found for action: ${action}`);
      return true; // Allow if no config (fail open)
    }

    const now = Date.now();
    const entry = this.limits.get(action) || { attempts: [] };

    // Remove attempts outside the time window
    entry.attempts = entry.attempts.filter(
      (timestamp) => now - timestamp < config.windowMs
    );

    // Check if limit exceeded
    if (entry.attempts.length >= config.maxAttempts) {
      return false;
    }

    // Record this attempt
    entry.attempts.push(now);
    this.limits.set(action, entry);

    return true;
  }

  /**
   * Get remaining attempts for an action
   */
  getRemainingAttempts(action: string): number {
    const config = this.configs[action];
    if (!config) return Infinity;

    const now = Date.now();
    const entry = this.limits.get(action) || { attempts: [] };

    // Filter recent attempts
    const recentAttempts = entry.attempts.filter(
      (timestamp) => now - timestamp < config.windowMs
    );

    return Math.max(0, config.maxAttempts - recentAttempts.length);
  }

  /**
   * Get time until next attempt is allowed (in milliseconds)
   * Returns 0 if attempts are currently allowed
   */
  getTimeUntilReset(action: string): number {
    const config = this.configs[action];
    if (!config) return 0;

    const now = Date.now();
    const entry = this.limits.get(action);
    if (!entry || entry.attempts.length < config.maxAttempts) {
      return 0; // Attempts available now
    }

    // Find oldest attempt in window
    const recentAttempts = entry.attempts.filter(
      (timestamp) => now - timestamp < config.windowMs
    );

    if (recentAttempts.length < config.maxAttempts) {
      return 0;
    }

    // Time until oldest attempt expires
    const oldestAttempt = Math.min(...recentAttempts);
    return config.windowMs - (now - oldestAttempt);
  }

  /**
   * Reset rate limit for a specific action
   */
  reset(action: string): void {
    this.limits.delete(action);
  }

  /**
   * Clear all rate limits
   */
  clearAll(): void {
    this.limits.clear();
  }
}
