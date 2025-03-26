// API service for communicating with the Flask backend

interface ApiResponse {
  success: boolean;
  data?: any;
  error?: string;
}

/**
 * Main API service for the health assistant application
 */
export const API = {
  async sendMessage(message: string): Promise<ApiResponse> {
    try {
      const formData = new FormData();
      formData.append('msg', message);

      const apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:5000';
      console.log('Sending request to:', apiUrl); // Debug log

      const response = await fetch(`${apiUrl}/get`, {
        method: 'POST',
        body: formData,
        headers: {
          'Accept': 'text/plain',
        },
      });

      console.log('Response status:', response.status); // Debug log

      if (!response.ok) {
        const errorText = await response.text();
        console.error('API error response:', errorText);
        return { 
          success: false, 
          error: `Server error: ${response.status} - ${errorText}` 
        };
      }
      
      const textResponse = await response.text();
      console.log('API success response:', textResponse); // Debug log
      
      return { 
        success: true, 
        data: { response: textResponse }
      };
    } catch (error) {
      console.error('Request failed:', error);
      return { 
        success: false, 
        error: error instanceof Error ? error.message : 'Unknown error' 
      };
    }
  }
};
