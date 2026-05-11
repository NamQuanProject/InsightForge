import axios, { AxiosInstance, AxiosError, InternalAxiosRequestConfig } from 'axios'

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000'

export const apiClient: AxiosInstance = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 60000,
})

apiClient.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    console.log(`[API Request] ${config.method?.toUpperCase()} ${config.url}`)
    return config
  },
  (error: AxiosError) => {
    console.error('[API Request Error]', error)
    return Promise.reject(error)
  }
)

apiClient.interceptors.response.use(
  (response) => {
    console.log(`[API Response] ${response.status} ${response.config.url}`)
    return response
  },
  (error: AxiosError) => {
    const { response, config } = error
    const status = response?.status
    const url = config?.url

    console.error(`[API Response Error] ${status} ${url}`, response?.data)

    if (typeof window !== 'undefined') {
      switch (status) {
        case 400:
          console.error('Bad Request:', response?.data)
          break
        case 401:
          console.error('Unauthorized - Redirecting to login')
          break
        case 403:
          console.error('Forbidden - You do not have permission')
          break
        case 404:
          console.error('Not Found - The requested resource does not exist')
          break
        case 422:
          console.error('Validation Error:', response?.data)
          break
        case 500:
          console.error('Internal Server Error - Please try again later')
          break
        default:
          if (status && status >= 500) {
            console.error(`Server Error (${status}) - Please try again later`)
          } else if (!status) {
            console.error('Network Error - Please check your connection')
          }
      }
    }

    return Promise.reject(error)
  }
)

export default apiClient