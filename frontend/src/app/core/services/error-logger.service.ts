import { Injectable } from '@angular/core';
import { HttpErrorResponse } from '@angular/common/http';

export type ErrorLevel = 'error' | 'warn' | 'info';

export interface LoggedError {
  timestamp: Date;
  level: ErrorLevel;
  message: string;
  url?: string;
  status?: number;
  stack?: string;
  user?: string;
  context?: Record<string, any>;
}

@Injectable({ providedIn: 'root' })
export class ErrorLoggerService {
  private readonly MAX_STORED_ERRORS = 50;
  private errors: LoggedError[] = [];

  /**
   * Log an HTTP error
   */
  logHttpError(error: HttpErrorResponse, context?: Record<string, any>): void {
    const loggedError: LoggedError = {
      timestamp: new Date(),
      level: 'error',
      message: this.extractHttpErrorMessage(error),
      url: error.url || undefined,
      status: error.status,
      context: {
        ...context,
        statusText: error.statusText,
        errorBody: error.error,
      },
    };

    this.storeError(loggedError);
    this.consoleLog(loggedError);

    // TODO: Send to remote logging service (Sentry, LogRocket, etc.)
    // this.sendToRemote(loggedError);
  }

  /**
   * Log a general error
   */
  logError(error: Error | string, context?: Record<string, any>): void {
    const loggedError: LoggedError = {
      timestamp: new Date(),
      level: 'error',
      message: typeof error === 'string' ? error : error.message,
      stack: typeof error === 'string' ? undefined : error.stack,
      context,
    };

    this.storeError(loggedError);
    this.consoleLog(loggedError);

    // TODO: Send to remote logging service
    // this.sendToRemote(loggedError);
  }

  /**
   * Log a warning
   */
  logWarn(message: string, context?: Record<string, any>): void {
    const loggedError: LoggedError = {
      timestamp: new Date(),
      level: 'warn',
      message,
      context,
    };

    this.storeError(loggedError);
    console.warn(`[${loggedError.timestamp.toISOString()}] ${message}`, context);
  }

  /**
   * Log informational message
   */
  logInfo(message: string, context?: Record<string, any>): void {
    const loggedError: LoggedError = {
      timestamp: new Date(),
      level: 'info',
      message,
      context,
    };

    this.storeError(loggedError);
    console.info(`[${loggedError.timestamp.toISOString()}] ${message}`, context);
  }

  /**
   * Get all stored errors (useful for debugging or user support)
   */
  getErrors(): ReadonlyArray<LoggedError> {
    return [...this.errors];
  }

  /**
   * Clear all stored errors
   */
  clearErrors(): void {
    this.errors = [];
  }

  /**
   * Export errors as JSON for user bug reports
   */
  exportErrors(): string {
    return JSON.stringify(this.errors, null, 2);
  }

  private extractHttpErrorMessage(error: HttpErrorResponse): string {
    if (error.status === 0) {
      return 'Network error: Unable to reach server';
    }
    if (error.status === 401) {
      return 'Authentication error: Unauthorized';
    }
    if (error.status === 403) {
      return 'Authorization error: Forbidden';
    }
    if (error.status === 404) {
      return 'Resource not found';
    }
    if (error.status >= 500) {
      return `Server error: ${error.status} ${error.statusText}`;
    }
    if (error.status >= 400) {
      return `Client error: ${error.status} ${error.statusText}`;
    }
    return `HTTP error: ${error.status} ${error.statusText}`;
  }

  private storeError(error: LoggedError): void {
    this.errors.unshift(error);
    if (this.errors.length > this.MAX_STORED_ERRORS) {
      this.errors = this.errors.slice(0, this.MAX_STORED_ERRORS);
    }
  }

  private consoleLog(error: LoggedError): void {
    const prefix = `[${error.timestamp.toISOString()}]`;
    const details = {
      url: error.url,
      status: error.status,
      context: error.context,
      stack: error.stack,
    };

    switch (error.level) {
      case 'error':
        console.error(`${prefix} ${error.message}`, details);
        break;
      case 'warn':
        console.warn(`${prefix} ${error.message}`, details);
        break;
      case 'info':
        console.info(`${prefix} ${error.message}`, details);
        break;
    }
  }

  /**
   * TODO: Implement remote logging integration
   * Example with Sentry:
   *
   * private sendToRemote(error: LoggedError): void {
   *   Sentry.captureException(new Error(error.message), {
   *     level: error.level,
   *     tags: {
   *       url: error.url,
   *       status: error.status?.toString(),
   *     },
   *     extra: error.context,
   *   });
   * }
   */
}
