<template>
  <div>
    <v-data-table
      :value="value"
      :headers="headers"
      :items="items"
      :options.sync="options"
      :server-items-length="total"
      :search="search"
      :loading="isLoading"
      :loading-text="$t('generic.loading')"
      :no-data-text="$t('vuetify.noDataAvailable')"
      :footer-props="{
        showFirstLastPage: true,
        'items-per-page-options': [10, 50, 100],
        'items-per-page-text': $t('vuetify.itemsPerPageText'),
        'page-text': $t('dataset.pageText')
      }"
      item-key="id"
      show-select
      @input="$emit('input', $event)"
    >
      <template #top>
        <v-text-field
          v-model="search"
          :prepend-inner-icon="mdiMagnify"
          :label="$t('generic.search') + ' (e.g. label:positive)'"
          single-line
          hide-details
          filled
        />
      </template>
      <template #[`item.isConfirmed`]="{ item: row }">
        <v-chip :color="row.isConfirmed ? 'success' : 'warning'" text small>
          {{ row.isConfirmed ? 'Finished' : 'In progress' }}
        </v-chip>
      </template>
      <template #[`item.text`]="{ item: row }">
        <span class="d-flex d-sm-none">{{ row.text | truncate(50) }}</span>
        <span class="d-none d-sm-flex">{{ row.text | truncate(200) }}</span>
      </template>
      <template #[`item.meta`]="{ item: row }">
        {{ JSON.stringify(row.meta, null, 4) }}
      </template>
      <template #[`item.assignee`]="{ item: row }">
        <v-combobox
          :value="toSelected(row)"
          :items="members"
          item-text="username"
          no-data-text="No one"
          multiple
          chips
          dense
          flat
          hide-selected
          hide-details
          small-chips
          solo
          style="width: 200px"
          @change="onAssignOrUnassign(row, $event)"
        >
          <template #selection="{ attrs, item: member, parent, selected }">
            <v-chip v-bind="attrs" :input-value="selected" small class="mt-1 mb-1">
              <span class="pr-1">{{ member.username }}</span>
              <v-icon small @click="parent.selectItem(member)"> $delete </v-icon>
            </v-chip>
          </template>
        </v-combobox>
      </template>
      <template #[`item.action`]="{ item: row }">
        <v-btn class="me-1" small color="primary text-capitalize" @click="$emit('edit', row)">
          Edit
        </v-btn>
        <v-btn small color="primary text-capitalize" @click="toLabeling(row)">
          {{ $t('dataset.annotate') }}
        </v-btn>
        <v-tooltip bottom :disabled="!isReported(row)">
          <template #activator="{ on, attrs }">
            <v-btn
              v-if="isAdmin"
              small
              outlined
              :color="getReviewButtonColor(row)"
              class="ms-1"
              v-bind="attrs"
              v-on="on"
              @click="openReportDialog(row)"
            >
              <v-icon left small>{{ getReviewButtonIcon(row) }}</v-icon>
              {{ getReviewButtonText(row) }}
            </v-btn>
          </template>
          <span>{{ getReviewTooltip(row) }}</span>
        </v-tooltip>
      </template>
    </v-data-table>
    <v-dialog v-model="showReportDialog" max-width="800">
      <v-card>
        <v-card-title class="headline d-flex align-center">
          <v-icon class="mr-2" color="primary">{{ require('@mdi/js').mdiClipboardCheck }}</v-icon>
          Inter-Annotator Agreement Review
        </v-card-title>
        <v-card-text>
          <div class="mb-4">
            <strong>Texto:</strong> {{ itemToReport?.text | truncate(100) }}
          </div>

          <v-divider class="mb-4"></v-divider>

                      <h3 class="mb-3">Agreement by Label:</h3>

          <div v-if="loadingLabels" class="text-center py-4">
            <v-progress-circular indeterminate color="primary"></v-progress-circular>
                          <p class="mt-2">Analyzing agreement between annotators...</p>
          </div>

          <div v-else-if="hasConnectionError" class="text-center py-4">
            <v-alert type="error" outlined class="mb-4">
              <div class="d-flex align-center">
                <v-icon class="mr-3" large>{{ require('@mdi/js').mdiDatabaseAlert }}</v-icon>
                <div class="text-left">
                  <h4 class="mb-2">Erro de Conectividade</h4>
                  <p class="mb-2">{{ connectionErrorMessage }}</p>
                  <v-btn
                    color="error"
                    outlined
                    small
                    :loading="loadingLabels"
                    @click="retryConnection"
                  >
                    <v-icon left small>{{ require('@mdi/js').mdiRefresh }}</v-icon>
                    Tentar Novamente
                  </v-btn>
                </div>
              </div>
            </v-alert>
          </div>

          <div v-else-if="datasetLabels.length === 0" class="text-center py-4">
            <v-icon large color="grey">{{ require('@mdi/js').mdiInformationOutline }}</v-icon>
                          <p class="mt-2 grey--text">No annotation found for agreement analysis</p>
          </div>

          <div v-else>
            <!-- Mostrar concordância de cada label -->
            <v-card v-for="label in datasetLabels" :key="label.name" class="mb-3" outlined>
              <v-card-text class="py-3">
                <div class="d-flex align-center justify-space-between">
                  <div class="flex-grow-1">
                    <div class="d-flex align-center mb-2">
                      <v-chip
                        :color="label.color || 'primary'"
                        text-color="white"
                        small
                        class="mr-3"
                      >
                        {{ label.name }}
                      </v-chip>
                      <span class="font-weight-bold">{{ label.percentage }}%</span>
                    </div>

                    <v-progress-linear
                      :value="label.percentage"
                      :color="label.color || 'primary'"
                      height="8"
                      rounded
                      class="mb-2"
                    ></v-progress-linear>

                    <div class="caption grey--text">
                      {{ label.agreementDetails }}
                    </div>
                    <div
                      v-if="label.annotators && label.annotators.length > 0"
                      class="caption grey--text mt-1"
                    >
                      <strong>Annotators:</strong> {{ label.annotators.join(', ') }}
                    </div>
                  </div>
                </div>
              </v-card-text>
            </v-card>

            <!-- Avaliação geral do dataset -->
            <v-divider class="my-4"></v-divider>

            <!-- Aviso se não há anotadores suficientes -->
            <v-alert v-if="!hasAllAnnotatorsCompleted()" type="warning" outlined class="mb-4">
              <div>
                <strong>Agreement analysis not available</strong>
                <br />
                {{ minimumAnnotatorsMessage }}
              </div>
            </v-alert>

            <v-card class="mt-4" outlined>
              <v-card-text class="py-4">
                <div class="d-flex align-center justify-space-between mb-4">
                  <div>
                    <h4 class="mb-2">Overall Dataset Evaluation</h4>
                    <p class="body-2 grey--text mb-0">
                      Based on the label agreements above, how do you evaluate this dataset?
                    </p>
                  </div>
                  <v-btn-toggle v-model="datasetApproval" :disabled="!hasAllAnnotatorsCompleted()" dense>
                    <v-btn :value="true" color="success" outlined :disabled="!hasAllAnnotatorsCompleted()">
                      <v-icon small class="mr-1">{{ require('@mdi/js').mdiCheck }}</v-icon>
                      Concordant Dataset
                    </v-btn>
                    <v-btn :value="false" color="error" outlined :disabled="!hasAllAnnotatorsCompleted()">
                      <v-icon small class="mr-1">{{ require('@mdi/js').mdiAlert }}</v-icon>
                      Discrepant Dataset
                    </v-btn>
                  </v-btn-toggle>
                </div>

                <v-textarea
                  v-if="datasetApproval === false"
                  v-model="datasetComment"
                  label="Comment on discrepancy (optional)"
                  placeholder="Describe the agreement issues identified in the dataset..."
                  outlined
                  dense
                  rows="3"
                  class="mt-3"
                  :disabled="!hasAllAnnotatorsCompleted()"
                ></v-textarea>
              </v-card-text>
            </v-card>
          </div>
        </v-card-text>
        <v-card-actions>
          <v-spacer></v-spacer>
          <v-btn color="grey" text @click="closeReportDialog">Cancel</v-btn>
          <v-tooltip bottom :disabled="hasAllAnnotatorsCompleted()">
            <template #activator="{ on, attrs }">
              <v-btn
                color="primary"
                :disabled="!isReviewFormValid"
                :loading="submittingReview"
                v-bind="attrs"
                v-on="on"
                @click="submitReview"
              >
                <v-icon left small>{{ require('@mdi/js').mdiContentSave }}</v-icon>
                {{ hasAllAnnotatorsCompleted() ? 'Submit Analysis' : 'Analysis Unavailable' }}
              </v-btn>
            </template>
            <span>{{ minimumAnnotatorsMessage }}</span>
          </v-tooltip>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- Diálogo para visualizar resultados (somente leitura) -->
    <v-dialog v-model="showResultsDialog" max-width="800">
      <v-card>
        <v-card-title class="headline d-flex align-center">
          <v-icon class="mr-2" color="success">{{ require('@mdi/js').mdiEye }}</v-icon>
          Agreement Review Results
          <v-spacer></v-spacer>
          <v-chip :color="datasetApproval ? 'success' : 'error'" text-color="white" small>
            <v-icon left small>{{
              datasetApproval ? require('@mdi/js').mdiCheck : require('@mdi/js').mdiAlert
            }}</v-icon>
            {{ datasetApproval ? 'Concordant' : 'Discrepant' }}
          </v-chip>
        </v-card-title>
        <v-card-text>
          <div class="mb-4">
            <strong>Text:</strong> {{ itemToReport?.text | truncate(100) }}
          </div>

          <v-divider class="mb-4"></v-divider>

          <v-alert :type="datasetApproval ? 'success' : 'error'" outlined class="mb-4">
            <div class="d-flex align-center">
              <v-icon class="mr-2">{{
                datasetApproval
                  ? require('@mdi/js').mdiCheckCircle
                  : require('@mdi/js').mdiAlertCircle
              }}</v-icon>
              <div>
                <strong>{{
                  datasetApproval ? 'Dataset Approved' : 'Dataset with Discrepancies'
                }}</strong>
                <br />
                <span class="body-2">
                  {{
                    datasetApproval
                      ? 'This dataset was evaluated as having good agreement between annotators.'
                      : 'This dataset was identified as having agreement issues between annotators.'
                  }}
                </span>
              </div>
            </div>
          </v-alert>

          <div v-if="datasetComment" class="mb-4">
            <h4 class="mb-2">Review Comment:</h4>
            <v-card outlined class="pa-3">
              <p class="mb-0">{{ datasetComment }}</p>
            </v-card>
          </div>

          <div class="text-center py-4">
            <v-icon large color="grey">{{ require('@mdi/js').mdiLock }}</v-icon>
            <p class="mt-2 grey--text">
              <strong>Review Completed</strong><br />
              This evaluation has been submitted and cannot be changed.
            </p>
          </div>
        </v-card-text>
        <v-card-actions>
          <v-spacer></v-spacer>
          <v-btn color="primary" @click="closeResultsDialog">Close</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- Snackbar para feedback -->
    <v-snackbar v-model="showSnackbar" :color="snackbarColor" :timeout="snackbarTimeout" top>
      {{ snackbarMessage }}
      <template #action="{ attrs }">
        <v-btn text v-bind="attrs" @click="showSnackbar = false"> Close </v-btn>
      </template>
    </v-snackbar>

    <!-- Botão de debug (apenas em desenvolvimento) -->
    <div v-if="$nuxt.isDev" class="mt-4 text-center">
      <v-btn small outlined color="warning" @click="clearReviewState">
        <v-icon left small>{{ require('@mdi/js').mdiDeleteSweep }}</v-icon>
        Clear Review State (Debug)
      </v-btn>
      <div class="caption mt-2 grey--text">
        Reviews saved: {{ reportedIds.length }} | Project: {{ projectId }}
      </div>
    </div>
  </div>
</template>

<script lang="ts">
// @ts-nocheck
import { mdiMagnify, mdiDeleteSweep } from '@mdi/js'
import type { PropType } from 'vue'
import Vue from 'vue'
import { DataOptions } from 'vuetify/types'
import { ExampleDTO } from '~/services/application/example/exampleData'
import { MemberItem } from '~/domain/models/member/member'

export default Vue.extend({
  props: {
    isLoading: {
      type: Boolean,
      default: false,
      required: true
    },
    items: {
      type: Array as PropType<ExampleDTO[]>,
      default: () => [],
      required: true
    },
    value: {
      type: Array as PropType<ExampleDTO[]>,
      default: () => [],
      required: true
    },
    total: {
      type: Number,
      default: 0,
      required: true
    },
    members: {
      type: Array as PropType<MemberItem[]>,
      default: () => [],
      required: true
    },
    isAdmin: {
      type: Boolean,
      default: false
    }
  },

  data() {
    return {
      search: this.$route.query.q,
      options: {} as DataOptions,
      mdiMagnify,
      mdiDeleteSweep,
      showReportDialog: false,
      showResultsDialog: false,
      itemToReport: null as ExampleDTO | null,
      reportedIds: [] as number[],
      reviewResults: {} as { [key: number]: { approved: boolean; comment?: string } },
      reportForm: {
        discrepancyType: null,
        description: '',
        severity: null
      },
      showSnackbar: false,
      snackbarColor: '',
      snackbarMessage: '',
      snackbarTimeout: 6000,
      loadingLabels: true,
      hasConnectionError: false,
      connectionErrorMessage: '',
      datasetLabels: [] as {
        name: string
        percentage: number
        count: number
        total: number
        color?: string
        annotators: string[]
        agreementDetails: string
      }[],
      datasetApproval: undefined as boolean | undefined,
      datasetComment: '',
      submittingReview: false
    }
  },

  computed: {
    headers() {
      const headers = [
        {
          text: 'Status',
          value: 'isConfirmed',
          sortable: false
        },
        {
          text: this.$t('dataset.text'),
          value: 'text',
          sortable: false
        },
        {
          text: this.$t('dataset.metadata'),
          value: 'meta',
          sortable: false
        },
        {
          text: this.$t('dataset.action'),
          value: 'action',
          sortable: false
        }
      ]
      if (this.isAdmin) {
        headers.splice(3, 0, {
          text: 'Assignee',
          value: 'assignee',
          sortable: false
        })
      }
      return headers
    },

    isFormValid() {
      return (
        this.reportForm.discrepancyType && this.reportForm.description && this.reportForm.severity
      )
    },

    isReviewFormValid() {
      // Verifica se a concordância do dataset foi avaliada
      const hasEvaluation = this.datasetApproval !== undefined

      // Verifica se todos os anotadores associados ao dataset já anotaram
      const allAnnotatorsCompleted = this.hasAllAnnotatorsCompleted()

      return hasEvaluation && allAnnotatorsCompleted
    },

    hasMinimumAnnotators() {
      // Verifica se há pelo menos 1 anotador no dataset
      return this.datasetLabels.length > 0 && this.datasetLabels.some((label) => label.total >= 1)
    },



    minimumAnnotatorsMessage() {
      if (this.datasetLabels.length === 0) {
        return 'No annotation found in the dataset'
      }

      const projectAnnotators = this.members.filter(member => member.isAnnotator)
      
      if (projectAnnotators.length === 0) {
        return 'No annotator associated with the project.'
      }

      // Obter todos os anotadores únicos que anotaram este dataset
      const annotatorsWhoAnnotated = new Set()
      this.datasetLabels.forEach(label => {
        if (label.annotators && Array.isArray(label.annotators)) {
          label.annotators.forEach(annotatorName => {
            annotatorsWhoAnnotated.add(annotatorName)
          })
        }
      })
      
      // Verificar quais anotadores do projeto ainda não anotaram
      const allProjectAnnotatorNames = projectAnnotators.map(member => member.username)
      const missingAnnotators = allProjectAnnotatorNames.filter(annotatorName => 
        !annotatorsWhoAnnotated.has(annotatorName)
      )
      
      if (missingAnnotators.length > 0) {
        return `Not all annotators have completed the annotations for this dataset. All annotators must annotate before approval.`
      }

      return ''
    },

    projectId() {
      return this.$route.params.id
    }
  },

  watch: {
    options: {
      handler() {
        this.$emit('update:query', {
          query: {
            limit: this.options.itemsPerPage.toString(),
            offset: ((this.options.page - 1) * this.options.itemsPerPage).toString(),
            q: this.search
          }
        })
      },
      deep: true
    },
    search() {
      this.$emit('update:query', {
        query: {
          limit: this.options.itemsPerPage.toString(),
          offset: '0',
          q: this.search
        }
      })
      this.options.page = 1
    },
    projectId: {
      handler() {
        // Carregar estado dos reviews quando o projeto mudar
        this.loadReviewState()
      },
      immediate: false
    }
  },

  mounted() {
    // Carregar estado dos reviews do localStorage quando o componente é montado
    this.loadReviewState()
  },

  methods: {
    hasAllAnnotatorsCompleted() {
      // Verifica se todos os anotadores associados ao projeto já anotaram este dataset específico
      if (this.datasetLabels.length === 0) {
        return false
      }

      // Obter todos os anotadores do projeto
      const projectAnnotators = this.members.filter(member => member.isAnnotator)
      
      // Se não há anotadores, não pode aprovar
      if (projectAnnotators.length === 0) {
        return false
      }
      
      // Obter todos os anotadores únicos que anotaram este dataset
      const annotatorsWhoAnnotated = new Set()
      this.datasetLabels.forEach(label => {
        if (label.annotators && Array.isArray(label.annotators)) {
          label.annotators.forEach(annotatorName => {
            annotatorsWhoAnnotated.add(annotatorName)
          })
        }
      })
      
      // Verificar se todos os anotadores do projeto estão na lista dos que anotaram
      const allProjectAnnotatorNames = projectAnnotators.map(member => member.username)
      const allAnnotated = allProjectAnnotatorNames.every(annotatorName => 
        annotatorsWhoAnnotated.has(annotatorName)
      )
      
      return allAnnotated
    },

    loadReviewState() {
      // Carregar estado dos reviews do localStorage para este projeto
      try {
        const storageKey = `dataset_reviews_project_${this.projectId}`
        const savedState = localStorage.getItem(storageKey)

        if (savedState) {
          const parsedState = JSON.parse(savedState)
          this.reportedIds = parsedState.reportedIds || []
          this.reviewResults = parsedState.reviewResults || {}

          console.log(`Loaded review state for project ${this.projectId}:`, {
            reportedIds: this.reportedIds,
            reviewResults: this.reviewResults
          })
        }
      } catch (error) {
                  console.error('Error loading review state:', error)
        // Em caso de erro, inicializar com estado vazio
        this.reportedIds = []
        this.reviewResults = {}
      }
    },

    saveReviewState() {
      // Guardar estado dos reviews no localStorage para este projeto
      try {
        const storageKey = `dataset_reviews_project_${this.projectId}`
        const stateToSave = {
          reportedIds: this.reportedIds,
          reviewResults: this.reviewResults,
          lastUpdated: new Date().toISOString()
        }

        localStorage.setItem(storageKey, JSON.stringify(stateToSave))
        console.log(`Saved review state for project ${this.projectId}:`, stateToSave)
      } catch (error) {
                  console.error('Error saving review state:', error)
      }
    },

    clearReviewState() {
      // Limpar estado dos reviews (útil para debugging ou reset)
      try {
        const storageKey = `dataset_reviews_project_${this.projectId}`
        localStorage.removeItem(storageKey)
        this.reportedIds = []
        this.reviewResults = {}
        console.log(`Review state cleared for project ${this.projectId}`)
      } catch (error) {
                  console.error('Error clearing review state:', error)
      }
    },

    toLabeling(item: ExampleDTO) {
      const index = this.items.indexOf(item)
      const offset = (this.options.page - 1) * this.options.itemsPerPage
      const page = (offset + index + 1).toString()
      this.$emit('click:labeling', { page, q: this.search })
    },

    toSelected(item: ExampleDTO) {
      const assigneeIds = item.assignments.map((assignment) => assignment.assignee_id)
      return this.members.filter((member) => assigneeIds.includes(member.user))
    },

    onAssignOrUnassign(item: ExampleDTO, newAssignees: MemberItem[]) {
      const newAssigneeIds = newAssignees.map((assignee) => assignee.user)
      const oldAssigneeIds = item.assignments.map((assignment) => assignment.assignee_id)
      if (oldAssigneeIds.length > newAssigneeIds.length) {
        // unassign
        for (const assignment of item.assignments) {
          if (!newAssigneeIds.includes(assignment.assignee_id)) {
            this.$emit('unassign', assignment.id)
          }
        }
      } else {
        // assign
        for (const newAssigneeId of newAssigneeIds) {
          if (!oldAssigneeIds.includes(newAssigneeId)) {
            this.$emit('assign', item.id, newAssigneeId)
          }
        }
      }
    },

    async openReportDialog(item: ExampleDTO) {
      // Se já foi submetido, apenas mostrar os resultados sem permitir edição
      if (this.isReported(item)) {
        this.showReviewResultsDialog(item)
        return
      }

      this.itemToReport = item
      this.resetReviewForm()
      this.showReportDialog = true
      await this.fetchDatasetLabels(item.id)
    },

    showReviewResultsDialog(item: ExampleDTO) {
      this.itemToReport = item
      this.showResultsDialog = true
      // Carregar dados do review para visualização
      const result = this.reviewResults[item.id]
      if (result) {
        this.datasetApproval = result.approved
        this.datasetComment = result.comment || ''
      }
    },

    closeReportDialog() {
      this.itemToReport = null
      this.showReportDialog = false
      this.resetReviewForm()
    },

    closeResultsDialog() {
      this.itemToReport = null
      this.showResultsDialog = false
      this.resetReviewForm()
    },

    resetReviewForm() {
      this.reportForm = {
        discrepancyType: null,
        description: '',
        severity: null
      }
      this.datasetLabels = []
      this.datasetApproval = undefined
      this.datasetComment = ''
      this.hasConnectionError = false
      this.connectionErrorMessage = ''
    },

    isReported(item: ExampleDTO) {
      return this.reportedIds.includes(item.id)
    },

    getReviewButtonColor(item: ExampleDTO) {
      if (!this.isReported(item)) {
        return 'primary text-capitalize'
      }

      const result = this.reviewResults[item.id]
      if (result) {
        return result.approved ? 'success' : 'error'
      }

      return 'success' // fallback para compatibilidade
    },

    getReviewButtonIcon(item: ExampleDTO) {
      if (!this.isReported(item)) {
        return require('@mdi/js').mdiClipboardCheck
      }

      const result = this.reviewResults[item.id]
      if (result) {
        return result.approved
          ? require('@mdi/js').mdiCheckCircle
          : require('@mdi/js').mdiAlertCircle
      }

      return require('@mdi/js').mdiCheckCircle // fallback para compatibilidade
    },

    getReviewButtonText(item: ExampleDTO) {
      if (!this.isReported(item)) {
        return 'Review'
      }

      const result = this.reviewResults[item.id]
      if (result) {
        return result.approved ? 'Concordant' : 'Discrepant'
      }

      return 'Reviewed' // fallback para compatibilidade
    },

    getReviewTooltip(item: ExampleDTO) {
      const result = this.reviewResults[item.id]
      if (result) {
        const status = result.approved
          ? 'Dataset evaluated as CONCORDANT'
          : 'Dataset evaluated as DISCREPANT'
        const comment = result.comment ? `\nComment: ${result.comment}` : ''
        return `${status}${comment}\n\nClick to view details (read-only)`
      }
      return 'Dataset has been reviewed'
    },

    isDatabaseConnectionError(error: any) {
      // Detectar erros de conexão com a base de dados
      if (!error) return false

      const errorMessage = error.message || error.toString().toLowerCase()
      const errorStatus = error.response?.status
      const errorCode = error.code

      // Códigos de status que indicam problemas de BD
      const dbErrorStatuses = [500, 502, 503, 504]

      // Códigos de erro que indicam problemas de conexão/BD
      const connectionErrorCodes = ['ECONNREFUSED', 'ENOTFOUND', 'ETIMEDOUT', 'ECONNRESET']

      // Mensagens que indicam problemas de BD ou conexão
      const dbErrorMessages = [
        'database',
        'connection refused',
        'connection timeout',
        'server error',
        'internal server error',
        'bad gateway',
        'service unavailable',
        'gateway timeout',
        'postgresql',
        'mysql',
        'sqlite',
        'database connection',
        'db connection',
        'failed to connect',
        "couldn't connect to server",
        'connection failed',
        'network error'
      ]

      // Verificar se é um erro de conexão (quando o servidor está completamente inacessível)
      const isConnectionError =
        connectionErrorCodes.includes(errorCode) ||
        errorMessage.includes('failed to connect') ||
        errorMessage.includes("couldn't connect") ||
        errorMessage.includes('connection refused') ||
        (!error.response && errorCode) // Axios sem resposta geralmente indica problema de conexão

      return (
        dbErrorStatuses.includes(errorStatus) ||
        dbErrorMessages.some((msg) => errorMessage.includes(msg)) ||
        isConnectionError
      )
    },

    isNetworkError(error: any) {
      // Detectar erros de rede (diferentes de erros de BD/servidor)
      if (!error) return false

      const errorMessage = error.message || error.toString().toLowerCase()
      const errorCode = error.code

      // Códigos específicos de rede (não relacionados com BD)
      const networkErrorCodes = ['NETWORK_ERROR', 'ERR_NETWORK']
      const networkErrorMessages = [
        'fetch error',
        'no internet',
        'offline',
        'dns',
        'name resolution'
      ]

      // Só considerar erro de rede se não for erro de BD/conexão ao servidor
      const isNetworkSpecific =
        networkErrorCodes.includes(errorCode) ||
        networkErrorMessages.some((msg) => errorMessage.includes(msg))

      return isNetworkSpecific && !this.isDatabaseConnectionError(error)
    },

    isAuthenticationError(error: any) {
      // Detectar erros de autenticação
      if (!error) return false

      const errorStatus = error.response?.status
      return errorStatus === 401 || errorStatus === 403
    },

    async retryConnection() {
      if (this.itemToReport) {
        await this.fetchDatasetLabels(this.itemToReport.id)
      }
    },

    async realBackendCall(reviewData: any) {
      // Fazer chamada real ao backend para submeter a revisão
      const response = await this.$axios.post(`/v1/projects/${this.projectId}/dataset-reviews`, reviewData)
      return response
    },

    async fetchDatasetLabels(_datasetId: number) {
      try {
        this.loadingLabels = true
        this.hasConnectionError = false
        this.connectionErrorMessage = ''

        // Buscar o projeto para saber que tipo de labels usar
        const project = await this.$services.project.findById(this.projectId)

        let labelTypes = []
        let allAnnotations = []

        // Determinar que tipo de labels buscar baseado no tipo de projeto
        if (project.canDefineCategory) {
          labelTypes = await this.$services.categoryType.list(this.projectId)
          allAnnotations = await this.$repositories.category.list(this.projectId, _datasetId, true) // true = buscar de todos os utilizadores
        } else if (project.canDefineSpan) {
          labelTypes = await this.$services.spanType.list(this.projectId)
          allAnnotations = await this.$repositories.span.list(this.projectId, _datasetId, true) // true = buscar de todos os utilizadores
        } else {
          this.datasetLabels = []
          return
        }

        // Buscar todos os membros do projeto para obter informações dos anotadores
        const members = await this.$repositories.member.list(this.projectId)
        const memberMap = Object.fromEntries(members.map((m) => [m.user, m.username]))

        // Agrupar anotações por anotador
        const annotationsByUser = {}
        allAnnotations.forEach((annotation) => {
          const userId = annotation.user
          if (!annotationsByUser[userId]) {
            annotationsByUser[userId] = []
          }
          annotationsByUser[userId].push(annotation)
        })

        const userIds = Object.keys(annotationsByUser)
        const totalAnnotators = userIds.length

        if (totalAnnotators === 0) {
          this.datasetLabels = labelTypes.map((label) => ({
            name: label.text,
            percentage: 0,
            count: 0,
            total: 0,
            color: label.backgroundColor || 'primary',
            annotators: [],
            agreementDetails: 'No annotation found'
          }))
          return
        }

        // Calcular concordância para cada label
        const labelAgreements = {}

        labelTypes.forEach((label) => {
          let usersWhoAnnotatedThisLabel = 0
          const annotatorsWithLabel = []

          userIds.forEach((userId) => {
            const userAnnotations = annotationsByUser[userId] || []
            const hasLabelAnnotation = userAnnotations.some((ann) => ann.label === label.id)

            if (hasLabelAnnotation) {
              usersWhoAnnotatedThisLabel++
              annotatorsWithLabel.push(memberMap[userId] || `User ${userId}`)
            }
          })

          const agreementPercentage =
            totalAnnotators > 0 ? (usersWhoAnnotatedThisLabel / totalAnnotators) * 100 : 0

          labelAgreements[label.text] = {
            percentage: Math.round(agreementPercentage * 10) / 10,
            count: usersWhoAnnotatedThisLabel,
            total: totalAnnotators,
            annotators: annotatorsWithLabel,
            agreementDetails: `${usersWhoAnnotatedThisLabel} of ${totalAnnotators} annotators agree`
          }
        })

        // Converter em dados formatados para o UI, ordenados por percentagem decrescente
        this.datasetLabels = labelTypes
          .map((label) => ({
            name: label.text,
            percentage: labelAgreements[label.text].percentage,
            count: labelAgreements[label.text].count,
            total: labelAgreements[label.text].total,
            color: label.backgroundColor || 'primary',
            annotators: labelAgreements[label.text].annotators,
            agreementDetails: labelAgreements[label.text].agreementDetails
          }))
          .sort((a, b) => b.percentage - a.percentage) // Ordenar por percentagem decrescente

        // Inicializar formulário
        this.datasetApproval = undefined
        this.datasetComment = ''
      } catch (error) {
        console.error('Error loading label agreement:', error)
        this.datasetLabels = []
        this.hasConnectionError = true
        this.showSnackbar = true
        this.snackbarColor = 'error'

        // Detectar tipo de erro para mostrar mensagem apropriada
        if (this.isDatabaseConnectionError(error)) {
          this.connectionErrorMessage =
            'Database is slow or unavailable. Please try again later.'
          this.snackbarMessage = '❌ ' + this.connectionErrorMessage
        } else if (this.isNetworkError(error)) {
          this.connectionErrorMessage = 'Network error. Check your internet connection.'
          this.snackbarMessage = '🌐 ' + this.connectionErrorMessage
        } else if (this.isAuthenticationError(error)) {
          this.connectionErrorMessage = 'Authentication error. Please login again.'
          this.snackbarMessage = '🔐 ' + this.connectionErrorMessage
        } else {
          this.connectionErrorMessage =
            'Error loading agreement between annotators. Please try again.'
          this.snackbarMessage = '⚠️ ' + this.connectionErrorMessage
        }
      } finally {
        this.loadingLabels = false
      }
    },

    async submitReview() {
      if (!this.itemToReport || !this.isReviewFormValid) return

      this.submittingReview = true
      try {
        const reviewData = {
          dataset_id: this.itemToReport.id,
          reviewed_by: this.$auth?.user?.id || 'anonymous',
          reviewed_at: new Date().toISOString(),
          label_agreements: this.datasetLabels.map((label) => ({
            label_name: label.name,
            percentage: label.percentage,
            count: label.count,
            total: label.total,
            annotators: label.annotators
          })),
          dataset_evaluation: {
            approved: this.datasetApproval,
            comment: this.datasetComment || null
          }
        }

        // Fazer chamada real ao backend
        await this.realBackendCall(reviewData)

        // Adicionar à lista local de datasets revisados
        this.reportedIds.push(this.itemToReport.id)

        // Armazenar resultado do review para mostrar no botão
        this.reviewResults[this.itemToReport.id] = {
          approved: this.datasetApproval,
          comment: this.datasetComment
        }

        // Guardar estado no localStorage
        this.saveReviewState()

        // Emitir evento para o componente pai
        this.$emit('dataset-reviewed', {
          item: this.itemToReport,
          review: reviewData
        })

        this.showSnackbar = true
        this.snackbarColor = 'success'
        this.snackbarMessage = 'Dataset review submitted successfully!'
        this.snackbarTimeout = 4000 // Timeout normal para sucesso

        this.closeReportDialog()
      } catch (error) {
        console.error('Error submitting review:', error)
        this.showSnackbar = true
        this.snackbarColor = 'error'

        // Detectar tipo de erro para mostrar mensagem apropriada
        if (this.isDatabaseConnectionError(error)) {
          this.snackbarMessage =
            '❌ Database is slow or unavailable. Please try again later.'
          this.snackbarTimeout = 10000 // Mais tempo para erros críticos
        } else if (this.isNetworkError(error)) {
          this.snackbarMessage =
            '🌐 Network error. Check your internet connection and try again.'
          this.snackbarTimeout = 8000
        } else if (this.isAuthenticationError(error)) {
          this.snackbarMessage = '🔐 Session expired. Please login again to submit the review.'
          this.snackbarTimeout = 8000
        } else {
          this.snackbarMessage =
            '⚠️ Unexpected error when submitting review. Please try again in a few moments.'
          this.snackbarTimeout = 6000
        }

        // Manter o diálogo aberto para permitir nova tentativa
        // this.closeReportDialog() - removido para permitir retry
      } finally {
        this.submittingReview = false
      }
    }
  }
})
</script>
