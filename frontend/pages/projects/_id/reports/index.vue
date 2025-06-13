<template>
  <v-container fluid>
    <v-row>
      <v-col cols="12">
        <v-card>
          <v-card-title class="primary white--text">
            <v-icon left color="white">{{ mdiFileDocumentOutline }}</v-icon>
            Relatórios sobre Anotadores
            <v-spacer />
            <v-btn color="white" text :loading="isGenerating" @click="generateReport">
              <v-icon left>{{ mdiRefresh }}</v-icon>
              Gerar Relatório
            </v-btn>
            <v-btn
              v-if="reportData && reportData.length > 0"
              color="success"
              class="ml-2"
              @click="showExportDialog = true"
            >
              <v-icon left>{{ mdiDownload }}</v-icon>
              Exportar
            </v-btn>
          </v-card-title>

          <v-card-text class="pa-0">
            <!-- Filtros Melhorados -->
            <v-card flat class="ma-4 elevation-2">
              <v-card-title class="pb-2">
                <v-icon left color="primary">{{ mdiFilter }}</v-icon>
                <span class="text-h6">Filtros de Pesquisa</span>
                <v-spacer />
                <v-btn small text color="primary" @click="clearFilters">
                  <v-icon small left>{{ mdiFilterRemove }}</v-icon>
                  Limpar Filtros
                </v-btn>
              </v-card-title>

              <v-card-text>
                <v-row>
                  <!-- Filtro de Utilizadores -->
                  <v-col cols="12" md="6">
                    <v-autocomplete
                      v-model="filters.users"
                      :items="availableUsers"
                      item-text="username"
                      item-value="id"
                      label="Anotadores"
                      multiple
                      chips
                      deletable-chips
                      clearable
                      outlined
                      dense
                      :prepend-inner-icon="mdiAccount"
                      hint="Selecione os anotadores específicos ou deixe vazio para todos"
                      persistent-hint
                    >
                      <template #selection="{ item, index }">
                        <v-chip
                          v-if="index < 3"
                          small
                          close
                          color="primary"
                          text-color="white"
                          @click:close="removeUser(item.id)"
                        >
                          {{ item.username }}
                        </v-chip>
                        <span v-if="index === 3" class="grey--text text-caption">
                          (+{{ filters.users.length - 3 }} outros)
                        </span>
                      </template>
                    </v-autocomplete>
                  </v-col>

                  <!-- Filtro de Labels -->
                  <v-col cols="12" md="6">
                    <v-autocomplete
                      v-model="filters.labels"
                      :items="availableLabels"
                      item-text="text"
                      item-value="id"
                      label="Labels"
                      multiple
                      chips
                      deletable-chips
                      clearable
                      outlined
                      dense
                      :prepend-inner-icon="mdiTag"
                      hint="Selecione labels específicos ou deixe vazio para todos"
                      persistent-hint
                    >
                      <template #selection="{ item, index }">
                        <v-chip
                          v-if="index < 2"
                          small
                          close
                          :color="getLabelTypeColor(item.type)"
                          text-color="white"
                          @click:close="removeLabel(item.id)"
                        >
                          {{ item.text }}
                        </v-chip>
                        <span v-if="index === 2" class="grey--text text-caption">
                          (+{{ filters.labels.length - 2 }} outros)
                        </span>
                      </template>
                      <template #item="{ item }">
                        <v-list-item-avatar>
                          <v-chip small :color="getLabelTypeColor(item.type)" text-color="white">
                            {{ item.type }}
                          </v-chip>
                        </v-list-item-avatar>
                        <v-list-item-content>
                          <v-list-item-title>{{ item.text }}</v-list-item-title>
                        </v-list-item-content>
                      </template>
                    </v-autocomplete>
                  </v-col>

                  <!-- Filtro de Data Início -->
                  <v-col cols="12" md="6">
                    <v-menu
                      v-model="dateFromMenu"
                      :close-on-content-click="false"
                      :nudge-right="40"
                      transition="scale-transition"
                      offset-y
                      min-width="auto"
                    >
                      <template #activator="{ on, attrs }">
                        <v-text-field
                          v-model="filters.date_from"
                          label="Data de Início"
                          :prepend-inner-icon="mdiCalendarStart"
                          readonly
                          outlined
                          dense
                          clearable
                          hint="Data a partir da qual considerar as anotações"
                          persistent-hint
                          v-bind="attrs"
                          v-on="on"
                        />
                      </template>
                      <v-date-picker
                        v-model="filters.date_from"
                        :max="filters.date_to || new Date().toISOString().substr(0, 10)"
                        locale="pt"
                        @input="dateFromMenu = false"
                      />
                    </v-menu>
                  </v-col>

                  <!-- Filtro de Data Fim -->
                  <v-col cols="12" md="6">
                    <v-menu
                      v-model="dateToMenu"
                      :close-on-content-click="false"
                      :nudge-right="40"
                      transition="scale-transition"
                      offset-y
                      min-width="auto"
                    >
                      <template #activator="{ on, attrs }">
                        <v-text-field
                          v-model="filters.date_to"
                          label="Data de Fim"
                          :prepend-inner-icon="mdiCalendarEnd"
                          readonly
                          outlined
                          dense
                          clearable
                          hint="Data até à qual considerar as anotações"
                          persistent-hint
                          v-bind="attrs"
                          v-on="on"
                        />
                      </template>
                      <v-date-picker
                        v-model="filters.date_to"
                        :min="filters.date_from"
                        :max="new Date().toISOString().substr(0, 10)"
                        locale="pt"
                        @input="dateToMenu = false"
                      />
                    </v-menu>
                  </v-col>

                  <!-- Filtro de Tipos de Tarefa -->
                  <v-col cols="12">
                    <v-select
                      v-model="filters.task_types"
                      :items="taskTypes"
                      label="Tipos de Tarefa"
                      multiple
                      chips
                      deletable-chips
                      clearable
                      outlined
                      dense
                      :prepend-inner-icon="mdiCog"
                      hint="Selecione os tipos de tarefa ou deixe vazio para todos"
                      persistent-hint
                    >
                      <template #selection="{ item, index }">
                        <v-chip
                          v-if="index < 4"
                          small
                          close
                          color="secondary"
                          text-color="white"
                          @click:close="removeTaskType(item)"
                        >
                          {{ getTaskTypeLabel(item) }}
                        </v-chip>
                        <span v-if="index === 4" class="grey--text text-caption">
                          (+{{ filters.task_types.length - 4 }} outros)
                        </span>
                      </template>
                      <template #item="{ item }">
                        <v-list-item-content>
                          <v-list-item-title>{{ getTaskTypeLabel(item) }}</v-list-item-title>
                          <v-list-item-subtitle class="text-caption">{{
                            item
                          }}</v-list-item-subtitle>
                        </v-list-item-content>
                      </template>
                    </v-select>
                  </v-col>
                </v-row>

                <!-- Resumo dos Filtros Ativos -->
                <v-row v-if="hasActiveFilters" class="mt-2">
                  <v-col cols="12">
                    <v-divider class="mb-3" />
                    <div class="d-flex align-center">
                      <v-icon small color="primary" class="mr-2">{{ mdiInformation }}</v-icon>
                      <span class="text-caption font-weight-medium">Filtros ativos:</span>
                      <v-spacer />
                      <span class="text-caption grey--text"
                        >{{ getActiveFiltersCount }} filtro(s) aplicado(s)</span
                      >
                    </div>
                  </v-col>
                </v-row>
              </v-card-text>
            </v-card>

            <!-- Tabela de Resultados -->
            <div class="ma-4">
              <v-data-table
                v-if="reportData && reportData.length > 0"
                :headers="tableHeaders"
                :items="reportData"
                :loading="isGenerating"
                class="elevation-2"
                :items-per-page="15"
                :footer-props="{
                  'items-per-page-options': [10, 15, 25, 50, -1],
                  'items-per-page-text': 'Itens por página:'
                }"
                loading-text="Carregando dados..."
                no-data-text="Nenhum dado disponível"
              >
                <template #top>
                  <v-toolbar flat color="grey lighten-4">
                    <v-toolbar-title class="text-h6">
                      <v-icon left>{{ mdiTable }}</v-icon>
                      Resultados do Relatório
                    </v-toolbar-title>
                    <v-spacer />
                    <v-chip color="primary" outlined> {{ reportData.length }} anotador(es) </v-chip>
                  </v-toolbar>
                </template>

                <template #[`item.label_breakdown`]="{ item }">
                  <div class="d-flex flex-wrap">
                    <v-chip
                      v-for="(count, label) in item.label_breakdown"
                      :key="label"
                      x-small
                      class="ma-1"
                      color="secondary"
                    >
                      {{ label }}: {{ count }}
                    </v-chip>
                    <span
                      v-if="Object.keys(item.label_breakdown).length === 0"
                      class="grey--text text-caption"
                    >
                      Nenhum label
                    </span>
                  </div>
                </template>

                <template #[`item.first_annotation_date`]="{ item }">
                  <span class="text-caption">
                    {{ formatDate(item.first_annotation_date) }}
                  </span>
                </template>

                <template #[`item.last_annotation_date`]="{ item }">
                  <span class="text-caption">
                    {{ formatDate(item.last_annotation_date) }}
                  </span>
                </template>
              </v-data-table>

              <!-- Estado vazio -->
              <v-card v-else-if="!isGenerating" flat class="text-center pa-12 elevation-2">
                <v-icon size="80" color="grey lighten-2">{{ mdiFileDocumentOutline }}</v-icon>
                <h3 class="grey--text mt-6 mb-2">Nenhum relatório gerado</h3>
                <p class="grey--text mb-6">
                  Configure os filtros desejados e clique em "Gerar Relatório" para visualizar os
                  dados dos anotadores
                </p>
                <v-btn color="primary" large @click="generateReport">
                  <v-icon left>{{ mdiRefresh }}</v-icon>
                  Gerar Primeiro Relatório
                </v-btn>
              </v-card>

              <!-- Loading -->
              <v-card v-else flat class="text-center pa-12 elevation-2">
                <v-progress-circular indeterminate color="primary" size="80" width="6" />
                <h3 class="mt-6 mb-2">Gerando relatório...</h3>
                <p class="grey--text">
                  Por favor aguarde enquanto processamos os dados dos anotadores
                </p>
              </v-card>
            </div>
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>

    <!-- Diálogo de Exportação -->
    <v-dialog v-model="showExportDialog" max-width="500px">
      <v-card>
        <v-card-title class="text-h5">
          <v-icon left color="primary">{{ mdiDownload }}</v-icon>
          Exportar Relatório
        </v-card-title>

        <v-card-text>
          <p class="mb-4">Escolha o formato para exportar o relatório:</p>

          <v-radio-group v-model="selectedExportFormat" column>
            <v-radio label="CSV (Comma Separated Values)" value="csv" color="primary">
              <template #label>
                <div class="d-flex align-center">
                  <v-icon class="mr-2" color="green">{{ mdiFileDelimited }}</v-icon>
                  <div>
                    <div class="font-weight-medium">CSV (Comma Separated Values)</div>
                    <div class="text-caption grey--text">Ideal para Excel e análise de dados</div>
                  </div>
                </div>
              </template>
            </v-radio>

            <v-radio label="TSV (Tab Separated Values)" value="tsv" color="primary">
              <template #label>
                <div class="d-flex align-center">
                  <v-icon class="mr-2" color="blue">{{ mdiFileDelimited }}</v-icon>
                  <div>
                    <div class="font-weight-medium">TSV (Tab Separated Values)</div>
                    <div class="text-caption grey--text">
                      Separado por tabs, compatível com muitas ferramentas
                    </div>
                  </div>
                </div>
              </template>
            </v-radio>

            <v-radio label="PDF (Portable Document Format)" value="pdf" color="primary">
              <template #label>
                <div class="d-flex align-center">
                  <v-icon class="mr-2" color="red">{{ mdiFilePdfBox }}</v-icon>
                  <div>
                    <div class="font-weight-medium">PDF (Portable Document Format)</div>
                    <div class="text-caption grey--text">
                      Documento formatado para visualização e impressão
                    </div>
                  </div>
                </div>
              </template>
            </v-radio>
          </v-radio-group>
        </v-card-text>

        <v-card-actions>
          <v-spacer />
          <v-btn text @click="showExportDialog = false"> Cancelar </v-btn>
          <v-btn color="primary" :loading="isExporting" @click="exportReport">
            <v-icon left>{{ mdiDownload }}</v-icon>
            Exportar
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </v-container>
</template>

<script>
import {
  mdiFileDocumentOutline,
  mdiRefresh,
  mdiDownload,
  mdiFilter,
  mdiFilterRemove,
  mdiAccount,
  mdiTag,
  mdiCalendarStart,
  mdiCalendarEnd,
  mdiCog,
  mdiInformation,
  mdiTable,
  mdiFileDelimited,
  mdiFilePdfBox
} from '@mdi/js'

export default {
  layout: 'project',
  middleware: ['check-auth', 'auth', 'setCurrentProject', 'isProjectAdmin'],

  validate({ params }) {
    return /^\d+$/.test(params.id)
  },

  data() {
    return {
      mdiFileDocumentOutline,
      mdiRefresh,
      mdiDownload,
      mdiFilter,
      mdiFilterRemove,
      mdiAccount,
      mdiTag,
      mdiCalendarStart,
      mdiCalendarEnd,
      mdiCog,
      mdiInformation,
      mdiTable,
      mdiFileDelimited,
      mdiFilePdfBox,

      isGenerating: false,
      dateFromMenu: false,
      dateToMenu: false,

      filters: {
        users: [],
        date_from: null,
        date_to: null,
        labels: [],
        task_types: []
      },

      availableUsers: [],
      availableLabels: [],
      taskTypes: [
        { text: 'Classificação de Documentos', value: 'DOCUMENT_CLASSIFICATION' },
        { text: 'Rotulagem de Sequências', value: 'SEQUENCE_LABELING' },
        { text: 'Sequência para Sequência', value: 'SEQUENCE_TO_SEQUENCE' },
        { text: 'Classificação de Imagens', value: 'IMAGE_CLASSIFICATION' },
        { text: 'Fala para Texto', value: 'SPEECH_TO_TEXT' },
        { text: 'Deteção de Intenção e Slot Filling', value: 'INTENT_DETECTION_AND_SLOT_FILLING' },
        { text: 'Caixa Delimitadora', value: 'BOUNDING_BOX' },
        { text: 'Segmentação', value: 'SEGMENTATION' }
      ],

      reportData: [],

      tableHeaders: [
        { text: 'Utilizador', value: 'annotator_username', sortable: true, width: '150px' },
        { text: 'Nome', value: 'annotator_name', sortable: true, width: '250px' },
        { text: 'Por Label', value: 'label_breakdown', sortable: false, width: '300px' },
        { text: 'Primeira', value: 'first_annotation_date', sortable: true, width: '150px' },
        { text: 'Última', value: 'last_annotation_date', sortable: true, width: '150px' }
      ],

      showExportDialog: false,
      selectedExportFormat: 'csv',
      isExporting: false
    }
  },

  computed: {
    projectId() {
      return this.$route.params.id
    },

    hasActiveFilters() {
      return (
        this.filters.users.length > 0 ||
        this.filters.labels.length > 0 ||
        this.filters.task_types.length > 0 ||
        this.filters.date_from ||
        this.filters.date_to
      )
    },

    getActiveFiltersCount() {
      let count = 0
      if (this.filters.users.length > 0) count++
      if (this.filters.labels.length > 0) count++
      if (this.filters.task_types.length > 0) count++
      if (this.filters.date_from) count++
      if (this.filters.date_to) count++
      return count
    }
  },

  async created() {
    await this.loadFilterOptions()
  },

  methods: {
    async loadFilterOptions() {
      try {
        // Carregar utilizadores do projeto
        const members = await this.$repositories.member.list(this.projectId)
        this.availableUsers = members.map((member) => ({
          id: member.user,
          username: member.username
        }))

        // Carregar projeto atual para verificar tipos disponíveis
        const currentProject = await this.$repositories.project.findById(this.projectId)

        // Carregar labels disponíveis baseado no tipo de projeto
        if (currentProject.canDefineCategory) {
          const categoryTypes = await this.$services.categoryType.list(this.projectId)
          this.availableLabels.push(
            ...categoryTypes.map((label) => ({
              id: label.id,
              text: label.text,
              type: 'category'
            }))
          )
        }

        if (currentProject.canDefineSpan) {
          const spanTypes = await this.$services.spanType.list(this.projectId)
          this.availableLabels.push(
            ...spanTypes.map((label) => ({
              id: label.id,
              text: label.text,
              type: 'span'
            }))
          )
        }

        if (currentProject.canDefineRelation) {
          const relationTypes = await this.$services.relationType.list(this.projectId)
          this.availableLabels.push(
            ...relationTypes.map((label) => ({
              id: label.id,
              text: label.text,
              type: 'relation'
            }))
          )
        }
      } catch (error) {
        console.error('Erro ao carregar opções de filtro:', error)
        this.showError('Erro ao carregar opções de filtro')
      }
    },

    async generateReport() {
      this.isGenerating = true
      try {
        // Preparar parâmetros de filtro com nomes corretos para a API
        const params = new URLSearchParams()

        // project_ids é obrigatório - usar sempre o projeto atual
        params.append('project_ids', this.projectId)

        if (this.filters.users.length > 0) {
          params.append('user_ids', this.filters.users.join(','))
        }

        if (this.filters.date_from) {
          params.append('date_from', this.filters.date_from)
        }

        if (this.filters.date_to) {
          params.append('date_to', this.filters.date_to)
        }

        if (this.filters.labels.length > 0) {
          params.append('label_ids', this.filters.labels.join(','))
        }

        if (this.filters.task_types.length > 0) {
          params.append(
            'task_types',
            this.filters.task_types.map((item) => item.value || item).join(',')
          )
        }

        console.log('[FRONTEND DEBUG] Parâmetros enviados:', params.toString())
        console.log(
          '[FRONTEND DEBUG] URL completa:',
          `/v1/reports/annotators/?${params.toString()}`
        )

        // Fazer chamada para a API
        const response = await this.$axios.get(`/v1/reports/annotators/?${params.toString()}`)
        console.log('[FRONTEND DEBUG] Resposta da API:', response)
        console.log('[FRONTEND DEBUG] Status:', response.status)
        console.log('[FRONTEND DEBUG] Data:', response.data)

        if (response.data && response.data.data) {
          this.reportData = response.data.data
          console.log(
            '[FRONTEND DEBUG] Dados do relatório definidos:',
            this.reportData.length,
            'anotadores'
          )
        } else {
          console.warn('[FRONTEND DEBUG] Estrutura de resposta inesperada:', response.data)
          this.reportData = []
        }

        this.showSuccess(
          `Relatório gerado com sucesso! ${this.reportData.length} anotador(es) encontrado(s).`
        )
      } catch (error) {
        console.error('[FRONTEND DEBUG] Erro completo:', error)
        console.error('[FRONTEND DEBUG] Erro response:', error.response)
        console.error('[FRONTEND DEBUG] Erro message:', error.message)

        let errorMessage = 'Erro ao gerar relatório'
        if (error.response) {
          console.error('[FRONTEND DEBUG] Status do erro:', error.response.status)
          console.error('[FRONTEND DEBUG] Data do erro:', error.response.data)

          if (error.response.data) {
            if (error.response.data.detail) {
              errorMessage = error.response.data.detail
            } else if (error.response.data.errors) {
              errorMessage = 'Parâmetros inválidos: ' + JSON.stringify(error.response.data.errors)
            }
          }
        } else if (error.request) {
          errorMessage = 'Erro de rede - servidor não respondeu'
          console.error('[FRONTEND DEBUG] Erro de request:', error.request)
        }

        this.showError(errorMessage)
      } finally {
        this.isGenerating = false
        console.log('[FRONTEND DEBUG] Loading finalizado')
      }
    },

    async exportReport() {
      this.isExporting = true
      try {
        // Preparar parâmetros de filtro com nomes corretos para a API
        const params = new URLSearchParams()

        // project_ids é obrigatório - usar sempre o projeto atual
        params.append('project_ids', this.projectId)

        if (this.filters.users.length > 0) {
          params.append('user_ids', this.filters.users.join(','))
        }

        if (this.filters.date_from) {
          params.append('date_from', this.filters.date_from)
        }

        if (this.filters.date_to) {
          params.append('date_to', this.filters.date_to)
        }

        if (this.filters.labels.length > 0) {
          params.append('label_ids', this.filters.labels.join(','))
        }

        if (this.filters.task_types.length > 0) {
          params.append(
            'task_types',
            this.filters.task_types.map((item) => item.value || item).join(',')
          )
        }

        // Adicionar formato de exportação
        params.append('export_format', this.selectedExportFormat)

        console.log('[EXPORT DEBUG] Formato selecionado:', this.selectedExportFormat)
        console.log('[EXPORT DEBUG] Parâmetros de exportação:', params.toString())

        // Fazer download do arquivo
        const response = await this.$axios.get(
          `/v1/reports/annotators/export/?${params.toString()}`,
          {
            responseType: 'blob'
          }
        )

        // Determinar nome do arquivo e tipo MIME baseado no formato
        let filename, mimeType
        switch (this.selectedExportFormat) {
          case 'csv':
            filename = `relatorio_anotadores_${new Date().toISOString().split('T')[0]}.csv`
            mimeType = 'text/csv'
            break
          case 'tsv':
            filename = `relatorio_anotadores_${new Date().toISOString().split('T')[0]}.tsv`
            mimeType = 'text/tab-separated-values'
            break
          case 'pdf':
            filename = `relatorio_anotadores_${new Date().toISOString().split('T')[0]}.pdf`
            mimeType = 'application/pdf'
            break
          default:
            filename = `relatorio_anotadores_${new Date().toISOString().split('T')[0]}.${
              this.selectedExportFormat
            }`
            mimeType = 'application/octet-stream'
        }

        // Criar link de download
        const blob = new Blob([response.data], { type: mimeType })
        const url = window.URL.createObjectURL(blob)
        const link = document.createElement('a')
        link.href = url
        link.download = filename
        document.body.appendChild(link)
        link.click()
        document.body.removeChild(link)
        window.URL.revokeObjectURL(url)

        // Fechar diálogo e mostrar sucesso
        this.showExportDialog = false
        this.showSuccess(
          `Relatório exportado em ${this.selectedExportFormat.toUpperCase()} com sucesso!`
        )
      } catch (error) {
        console.error('[EXPORT DEBUG] Erro ao exportar:', error)
        this.showError(`Erro ao exportar relatório em ${this.selectedExportFormat.toUpperCase()}`)
      } finally {
        this.isExporting = false
      }
    },

    async exportToCSV() {
      // Método mantido para compatibilidade, mas agora usa o método unificado
      this.selectedExportFormat = 'csv'
      await this.exportReport()
    },

    clearFilters() {
      this.filters = {
        users: [],
        date_from: null,
        date_to: null,
        labels: [],
        task_types: []
      }
      this.showSuccess('Filtros limpos')
    },

    removeUser(userId) {
      this.filters.users = this.filters.users.filter((id) => id !== userId)
    },

    removeLabel(labelId) {
      this.filters.labels = this.filters.labels.filter((id) => id !== labelId)
    },

    removeTaskType(taskType) {
      this.filters.task_types = this.filters.task_types.filter((type) => type !== taskType)
    },

    getLabelTypeColor(type) {
      const colors = {
        category: 'blue',
        span: 'green',
        relation: 'orange'
      }
      return colors[type] || 'grey'
    },

    getTaskTypeLabel(taskType) {
      if (typeof taskType === 'object') {
        return taskType.text
      }
      const found = this.taskTypes.find((t) => t.value === taskType)
      return found ? found.text : taskType
    },

    formatDate(dateString) {
      if (!dateString) return '-'
      return new Date(dateString).toLocaleDateString('pt-PT', {
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit'
      })
    },

    showSuccess(message) {
      // Usar $nuxt.$toast se disponível, senão console.log
      if (this.$nuxt && this.$nuxt.$toast) {
        this.$nuxt.$toast.success(message)
      } else if (this.$toast) {
        this.$toast.success(message)
      } else {
        console.log('SUCCESS:', message)
        // Fallback para alert se necessário
        alert(message)
      }
    },

    showError(message) {
      // Usar $nuxt.$toast se disponível, senão console.error
      if (this.$nuxt && this.$nuxt.$toast) {
        this.$nuxt.$toast.error(message)
      } else if (this.$toast) {
        this.$toast.error(message)
      } else {
        console.error('ERROR:', message)
        // Fallback para alert se necessário
        alert('Erro: ' + message)
      }
    }
  }
}
</script>

<style scoped>
.v-chip {
  margin: 2px;
}

.v-card-title.primary {
  background: linear-gradient(45deg, #1976d2, #42a5f5);
}

.v-data-table >>> .v-data-table__wrapper {
  border-radius: 8px;
}

.v-card {
  border-radius: 12px;
}

.text-caption {
  font-size: 0.75rem !important;
}
</style>
