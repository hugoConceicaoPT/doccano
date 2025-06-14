export default {
  methods: {
    /**
     * Obtém o nome completo do dataset com extensão
     * Prioriza upload_name com extensão, depois filename com extensão
     */
    getDatasetName(example) {
      if (!example) return ''
      
      // Tentar usar upload_name primeiro (nome original com extensão)
      if (example.uploadName && example.uploadName.includes('.')) {
        return example.uploadName
      }
      
      // Se filename tem extensão, usar filename
      if (example.filename && example.filename.includes('.')) {
        return example.filename
      }
      
      // Fallback para upload_name sem extensão
      if (example.uploadName) {
        return example.uploadName
      }
      
      // Último recurso: filename
      if (example.filename) {
        return example.filename
      }
      
      return ''
    },
    
    /**
     * Obtém o nome do dataset sem extensão (para compatibilidade)
     */
    getDatasetNameWithoutExtension(example) {
      const fullName = this.getDatasetName(example)
      return fullName.replace(/\.[^/.]+$/, '')
    }
  }
} 