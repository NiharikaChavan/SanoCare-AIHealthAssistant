
/**
 * Format error messages from API responses
 */
export const formatApiError = (error: unknown): string => {
  if (error instanceof Error) {
    return error.message;
  }
  if (typeof error === 'string') {
    return error;
  }
  return 'An unknown error occurred';
};

/**
 * Log API responses for debugging
 */
export const logApiResponse = (endpoint: string, data: any, error?: any) => {
  if (import.meta.env.MODE === 'development') {
    if (error) {
      console.error(`API ERROR (${endpoint}):`, error);
    } else {
      console.log(`API RESPONSE (${endpoint}):`, data);
    }
  }
};
