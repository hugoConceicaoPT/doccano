import axios from 'axios'
axios.defaults.xsrfCookieName = 'csrftoken'
axios.defaults.xsrfHeaderName = 'X-CSRFToken'

class ApiService {
  constructor() {
    this.instance = axios.create({
      baseURL: process.env.baseUrl,
      timeout: 6000 // Aumentar timeout para 10 segundos
    })
    
    // Interceptor de resposta para tratar erros de conexão
    this.instance.interceptors.response.use(
      (response) => {
        // Resposta bem-sucedida, retornar normalmente
        return response
      },
      (error) => {
        // Tratar erros de conexão
        if (!error.response) {
          // Erro de rede/conexão (sem resposta do servidor)
          error.isNetworkError = true
          error.userMessage = 'Erro de conexão: Não foi possível conectar ao servidor. Verifique sua conexão com a internet.'
        } else if (error.response.status === 503) {
          // Service Unavailable - base de dados indisponível
          error.isDatabaseError = true
          error.userMessage = 'Base de dados indisponível: A base de dados está temporariamente desligada ou sem conexão. Tente novamente em alguns instantes.'
        } else if (error.response.status >= 500) {
          // Erro interno do servidor
          error.isServerError = true
          error.userMessage = 'Database is slow or unavailable. Please try again later.'
        } else if (error.code === 'ECONNABORTED') {
          // Timeout
          error.isTimeoutError = true
          error.userMessage = 'Timeout: A operação demorou muito tempo. A base de dados pode estar sobrecarregada.'
        }
        
        return Promise.reject(error)
      }
    )
  }

  request(method, url, data = {}, config = {}) {
    return this.instance({
      method,
      url,
      data,
      ...config
    })
  }

  get(url, config = {}) {
    return this.request('GET', url, {}, config)
  }

  post(url, data, config = {}) {
    return this.request('POST', url, data, config)
  }

  put(url, data, config = {}) {
    return this.request('PUT', url, data, config)
  }

  patch(url, data, config = {}) {
    return this.request('PATCH', url, data, config)
  }

  delete(url, data = {}, config = {}) {
    return this.request('DELETE', url, data, config)
  }
}

export default new ApiService()
