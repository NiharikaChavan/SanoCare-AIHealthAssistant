
/**
 * Environment configuration for the application
 */
export const config = {
  /**
   * API URL for the Flask backend
   * Defaults to localhost:5000 in development
   */
  apiUrl: import.meta.env.VITE_API_URL || 'http://localhost:5000',
  
  /**
   * Debug mode for development
   */
  debug: import.meta.env.MODE === 'development',
};
