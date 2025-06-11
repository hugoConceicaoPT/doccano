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
        <v-btn 
          v-if="isAdmin"
          small 
          outlined 
          :color="getReviewButtonColor(row)" 
          :disabled="isReviewed(row)"
          class="ms-1" 
          @click="openReportDialog(row)"
        >
          <v-icon left small>{{ getReviewButtonIcon(row) }}</v-icon>
          {{ getReviewButtonText(row) }}
        </v-btn>
      </template>
    </v-data-table>
    <v-dialog v-model="showReportDialog" max-width="800">
      <v-card>
        <v-card-title class="headline d-flex align-center">
          <v-icon 
            class="mr-2" 
            :color="itemToReport && isManuallyFlagged(itemToReport) ? 'error' : 'primary'"
          >
            {{ itemToReport && isManuallyFlagged(itemToReport) ? require('@mdi/js').mdiAlert : require('@mdi/js').mdiClipboardCheck }}
          </v-icon>
          Revisão de Concordância entre Anotadores
          <v-chip 
            v-if="itemToReport && isManuallyFlagged(itemToReport)" 
            color="error" 
            text-color="white" 
            small 
            class="ml-2"
          >
            Discrepante
          </v-chip>
        </v-card-title>
        <v-card-text>
          <div class="mb-4">
            <strong>Dataset ID:</strong> {{ itemToReport?.id }}<br>
            <strong>Texto:</strong> {{ itemToReport?.text | truncate(100) }}
          </div>
          
          <v-divider class="mb-4"></v-divider>
          
          <h3 class="mb-3">Concordância de Labels entre Anotadores:</h3>
          
          <div v-if="loadingLabels" class="text-center py-4">
            <v-progress-circular indeterminate color="primary"></v-progress-circular>
            <p class="mt-2">Analisando concordância entre anotadores...</p>
          </div>
          
          <div v-else-if="datasetLabels.length === 0" class="text-center py-4">
            <v-icon large color="grey">{{ require('@mdi/js').mdiInformationOutline }}</v-icon>
            <p class="mt-2 grey--text">Nenhuma anotação encontrada para análise de concordância</p>
          </div>
          
          <div v-else>

            <div class="label-agreements">
              <div
                v-for="label in datasetLabels"
                :key="label.name"
                class="label-agreement-item mb-3"
              >
                <div class="d-flex align-center">
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
                    
                    <div class="caption grey--text">
                      {{ label.agreementDetails }}
                    </div>
                    <div v-if="label.annotators && label.annotators.length > 0" class="caption grey--text mt-1">
                      <strong>Anotadores:</strong> {{ label.annotators.join(', ') }}
                    </div>
                  </div>
                </div>
              </div>
            </div>

            <v-divider class="my-4"></v-divider>

            <h3 class="mb-3">Decisão sobre o Dataset:</h3>
            <v-card outlined class="pa-4">
              <v-radio-group 
                v-model="datasetDecision" 
                mandatory
                class="mt-0"
              >
                <v-radio 
                  :value="false" 
                  color="success"
                >
                  <template #label>
                    <div class="d-flex align-items-center">
                      <v-icon color="success" class="mr-2">{{ require('@mdi/js').mdiCheckCircle }}</v-icon>
                      <span>Dataset está correto (sem discrepâncias)</span>
                    </div>
                  </template>
                </v-radio>
                <v-radio 
                  :value="true" 
                  color="error"
                >
                  <template #label>
                    <div class="d-flex align-items-center">
                      <v-icon color="error" class="mr-2">{{ require('@mdi/js').mdiAlert }}</v-icon>
                      <span>Dataset tem discrepâncias</span>
                    </div>
                  </template>
                </v-radio>
              </v-radio-group>

              <v-textarea
                v-if="datasetDecision === true"
                v-model="datasetComment"
                label="Comentário sobre a discrepância (opcional)"
                placeholder="Descreva as discrepâncias identificadas no dataset..."
                outlined
                dense
                rows="3"
                class="mt-3"
              ></v-textarea>
            </v-card>
            
            <!-- Mensagem informativa quando não há anotadores suficientes -->
            <v-alert 
              v-if="totalAnnotators < 2"
              type="warning" 
              dense 
              text 
              class="mt-4"
            >
              <small>
                <v-icon small class="mr-1">{{ require('@mdi/js').mdiInformationOutline }}</v-icon>
                É necessário pelo menos 2 anotadores para submeter análise de concordância. 
                Atualmente: {{ totalAnnotators }} anotador{{ totalAnnotators === 1 ? '' : 'es' }}.
              </small>
            </v-alert>
          </div>
        </v-card-text>
        <v-card-actions>
          <v-spacer></v-spacer>
          <v-btn color="grey" text @click="closeReportDialog">Cancelar</v-btn>
          <v-btn 
            color="primary" 
            :disabled="!isReviewFormValid" 
            :loading="submittingReview"
            @click="submitReview"
          >
            <v-icon left small>{{ require('@mdi/js').mdiContentSave }}</v-icon>
            Submeter Análise
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- Snackbar para feedback -->
    <v-snackbar
      v-model="showSnackbar"
      :color="snackbarColor"
      timeout="4000"
      top
    >
      {{ snackbarMessage }}
      <template #action="{ attrs }">
        <v-btn text v-bind="attrs" @click="showSnackbar = false">
          Fechar
        </v-btn>
      </template>
    </v-snackbar>
  </div>
</template>

<script lang="ts">
import { mdiMagnify } from '@mdi/js'
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
      showReportDialog: false,
      itemToReport: null as ExampleDTO | null,
      reportedIds: [] as number[],
      manuallyFlaggedIds: [] as number[],
      reportForm: {
        discrepancyType: null,
        description: '',
        severity: null
      },
      showSnackbar: false,
      snackbarColor: '',
      snackbarMessage: '',
      loadingLabels: true,
      datasetLabels: [] as { name: string; percentage: number; count: number; total: number; color?: string }[],
      submittingReview: false,
      datasetDecision: false,
      datasetComment: '',
      totalAnnotators: 0
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
      return this.reportForm.discrepancyType && this.reportForm.description && this.reportForm.severity
    },

    isReviewFormValid() {
      // Verifica apenas se há pelo menos 2 anotadores
      return this.totalAnnotators >= 2
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
    }
  },

  async created() {
    // Load manual discrepancies if user is admin
    if (this.isAdmin) {
      await this.loadManualDiscrepancies()
    }
  },

  methods: {
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
      // Não permitir abrir dialog para itens já analisados
      if (this.isReviewed(item)) {
        this.showSnackbar = true
        this.snackbarColor = 'warning'
        this.snackbarMessage = 'Este dataset já foi analisado e não pode ser alterado.'
        return
      }
      
      this.itemToReport = item
      this.resetReviewForm()
      this.showReportDialog = true
      await this.fetchDatasetLabels(item.id)
    },

    closeReportDialog() {
      this.itemToReport = null
      this.showReportDialog = false
      this.resetReviewForm()
    },

    resetReviewForm() {
      this.reportForm = {
        discrepancyType: null,
        description: '',
        severity: null
      }
      this.datasetDecision = false
      this.datasetComment = ''
      this.datasetLabels = []
      this.totalAnnotators = 0
    },

    isReported(item: ExampleDTO) {
      return this.reportedIds.includes(item.id)
    },

    isManuallyFlagged(item: ExampleDTO) {
      return this.manuallyFlaggedIds.includes(item.id)
    },

    isReviewed(item: ExampleDTO) {
      // Um item está "reviewed" se foi reportado (tem análise submetida)
      return this.isReported(item)
    },

    async loadManualDiscrepancies() {
      try {
        const response = await this.$axios.get(`/api/projects/${this.projectId}/labels/manual-discrepancies`)
        this.manuallyFlaggedIds = response.data.map((discrepancy: any) => 
          parseInt(discrepancy.example)
        )
      } catch (error) {
        console.error('Error loading manual discrepancies:', error)
      }
    },

    async fetchDatasetLabels(_datasetId: number) {
      try {
        this.loadingLabels = true
        
        // Buscar o projeto para saber que tipo de labels usar
        const project = await this.$services.project.findById(this.projectId)
        
        let labelTypes = []
        let allAnnotations = []
        
        // Temporary solution: Get annotations from current user and simulate multiple users
        // This is a pragmatic approach until we can solve the API issues
        if (project.canDefineCategory) {
          labelTypes = await this.$services.categoryType.list(this.projectId)
          console.log('Getting categories for example:', _datasetId)
          
          // Get annotations from ALL users (admin only)
          allAnnotations = await this.$repositories.category.list(this.projectId, _datasetId, true)
          console.log('Got annotations from all users:', allAnnotations.length)
          
          // Multi-user annotations now working!
          if (allAnnotations.length > 0) {
            console.log('Successfully loaded annotations from all users for review.')
          }
        } else if (project.canDefineSpan) {
          labelTypes = await this.$services.spanType.list(this.projectId)
          console.log('Getting spans for example:', _datasetId)
          
          // Get annotations from ALL users (admin only)
          allAnnotations = await this.$repositories.span.list(this.projectId, _datasetId, true)
          console.log('Got annotations from all users:', allAnnotations.length)
          
          // Multi-user annotations now working!
          if (allAnnotations.length > 0) {
            console.log('Successfully loaded annotations from all users for review.')
          }
        } else {
          this.datasetLabels = []
          return
        }
        
        // Verificar se temos um array válido
        console.log('All annotations type:', typeof allAnnotations, 'Is array:', Array.isArray(allAnnotations), 'Length:', allAnnotations?.length)
        if (!Array.isArray(allAnnotations)) {
          console.error('allAnnotations is not an array:', allAnnotations)
          this.datasetLabels = []
          return
        }
        
        // Buscar todos os membros do projeto para obter informações dos anotadores
        const members = await this.$repositories.member.list(this.projectId)
        const memberMap = Object.fromEntries(members.map(m => [m.user, m.username]))
        
        // Agrupar anotações por anotador
        const annotationsByUser = {}
        allAnnotations.forEach(annotation => {
          const userId = annotation.user
          if (!annotationsByUser[userId]) {
            annotationsByUser[userId] = []
          }
          annotationsByUser[userId].push(annotation)
        })
        
        const userIds = Object.keys(annotationsByUser)
        this.totalAnnotators = userIds.length
        
        if (this.totalAnnotators === 0) {
          this.datasetLabels = labelTypes.map(label => ({
            name: label.text,
            percentage: 0,
            count: 0,
            total: 0,
            color: label.backgroundColor || 'primary',
            annotators: [],
            agreementDetails: 'Nenhuma anotação encontrada'
          }))
          return
        }
        
        // Calcular concordância para cada label
        const labelAgreements = {}
        
        labelTypes.forEach(label => {
          let usersWhoAnnotatedThisLabel = 0
          const annotatorsWithLabel = []
          
          userIds.forEach(userId => {
            const userAnnotations = annotationsByUser[userId] || []
            const hasLabelAnnotation = userAnnotations.some(ann => ann.label === label.id)
            
            if (hasLabelAnnotation) {
              usersWhoAnnotatedThisLabel++
              annotatorsWithLabel.push(memberMap[userId] || `User ${userId}`)
            }
          })
          
          const agreementPercentage = this.totalAnnotators > 0 
            ? (usersWhoAnnotatedThisLabel / this.totalAnnotators) * 100 
            : 0
          
          labelAgreements[label.text] = {
            percentage: Math.round(agreementPercentage * 10) / 10,
            count: usersWhoAnnotatedThisLabel,
            total: this.totalAnnotators,
            annotators: annotatorsWithLabel,
            agreementDetails: `${usersWhoAnnotatedThisLabel} de ${this.totalAnnotators} anotadores concordam`
          }
        })
        
        // Converter em dados formatados para o UI, ordenados por percentagem decrescente
        this.datasetLabels = labelTypes
          .map(label => ({
            name: label.text,
            percentage: labelAgreements[label.text].percentage,
            count: labelAgreements[label.text].count,
            total: labelAgreements[label.text].total,
            color: label.backgroundColor || 'primary',
            annotators: labelAgreements[label.text].annotators,
            agreementDetails: labelAgreements[label.text].agreementDetails
          }))
          .sort((a, b) => b.percentage - a.percentage) // Ordenar por percentagem decrescente
        
        // Initialize dataset decision (check if already flagged)
        this.datasetDecision = this.isManuallyFlagged(this.itemToReport)
        this.datasetComment = ''
        
      } catch (error) {
        console.error('Erro ao carregar concordância de labels:', error)
        console.error('Full error details:', error.response || error)
        this.datasetLabels = []
        this.showSnackbar = true
        this.snackbarColor = 'error'
        this.snackbarMessage = `Erro ao carregar concordância entre anotadores: ${error.message || error}`
      } finally {
        this.loadingLabels = false
      }
    },

    async submitReview() {
      if (!this.itemToReport || !this.isReviewFormValid) return
      
      // Verificar se uma decisão foi tomada
      if (this.datasetDecision === undefined || this.datasetDecision === null) {
        this.showSnackbar = true
        this.snackbarColor = 'warning'
        this.snackbarMessage = 'Por favor, tome uma decisão sobre o dataset antes de submeter.'
        return
      }
      
      this.submittingReview = true
      try {
        const reviewData = {
          dataset_id: this.itemToReport.id,
          reviewed_by: this.$auth?.user?.id || 'anonymous',
          reviewed_at: new Date().toISOString(),
          is_discrepant: this.datasetDecision,
          comment: this.datasetComment || null,
          label_percentages: this.datasetLabels.map(label => ({
            label_name: label.name,
            percentage: label.percentage,
            count: label.count,
            total: label.total
          }))
        }

        // Se foi marcado como discrepante, usar nossa API para marcar
        if (this.datasetDecision) {
          try {
            const response = await this.$axios.post(
              `/v1/projects/${this.projectId}/examples/${this.itemToReport.id}/manual-discrepancy-toggle`,
              { reason: `Review: ${this.datasetComment || 'Dataset marcado como discrepante'}` }
            )
            
            // Update local state based on API response
            if (response.data.is_flagged) {
              if (!this.manuallyFlaggedIds.includes(this.itemToReport.id)) {
                this.manuallyFlaggedIds.push(this.itemToReport.id)
              }
            }
          } catch (error) {
            console.error('Erro ao marcar discrepância manual:', error)
            // Continuar mesmo se esta parte falhar
          }
        } else {
          // Se foi marcado como correto, remover flag se existir
          try {
            const response = await this.$axios.post(
              `/v1/projects/${this.projectId}/examples/${this.itemToReport.id}/manual-discrepancy-toggle`,
              { reason: 'Review: Dataset marcado como correto' }
            )
            
            // Update local state - remove from flagged if it was unflagged
            if (!response.data.is_flagged) {
              this.manuallyFlaggedIds = this.manuallyFlaggedIds.filter(id => id !== this.itemToReport.id)
            }
          } catch (error) {
            // Se não conseguiu remover o flag, continuar
            console.error('Erro ao remover flag de discrepância:', error)
          }
        }

        // Chamada ao backend - descomentar quando implementado
        // await this.$axios.post('/api/dataset-reviews/', reviewData)
        
        // Mock: adicionar à lista local
        this.reportedIds.push(this.itemToReport.id)
        
        // Emitir evento para o componente pai
        this.$emit('dataset-reviewed', {
          item: this.itemToReport,
          review: reviewData
        })
        
        this.showSnackbar = true
        this.snackbarColor = 'success'
        this.snackbarMessage = this.datasetDecision 
          ? 'Dataset marcado como discrepante!' 
          : 'Dataset marcado como correto!'
        
        this.closeReportDialog()
        
      } catch (error) {
        console.error('Erro ao submeter revisão:', error)
        this.showSnackbar = true
        this.snackbarColor = 'error'
        this.snackbarMessage = 'Erro ao submeter revisão. Tente novamente.'
      } finally {
        this.submittingReview = false
      }
    },

    getReviewButtonColor(item: ExampleDTO) {
      if (this.isManuallyFlagged(item)) return 'error' // Red for discrepant
      if (this.isReported(item)) return 'grey' // Grey for reviewed (disabled)
      return 'primary' // Blue for not reviewed
    },

    getReviewButtonIcon(item: ExampleDTO) {
      if (this.isManuallyFlagged(item)) return require('@mdi/js').mdiAlert
      if (this.isReported(item)) return require('@mdi/js').mdiCheckCircle
      return require('@mdi/js').mdiClipboardCheck
    },

    getReviewButtonText(item: ExampleDTO) {
      if (this.isManuallyFlagged(item)) return 'Discrepante'
      if (this.isReported(item)) return 'Analisado'
      return 'Review'
    },

    async getAdminAnnotations(type: string, datasetId: number) {
      // Try to get all annotations from all users using authenticated requests
      try {
        // Use the same pattern as other authenticated API calls in the app
        const url = `/v1/projects/${this.projectId}/labels/admin/examples/${datasetId}/${type}`
        console.log('Making authenticated request to:', url)
        
        // The $axios instance should already have authentication configured
        const response = await this.$axios.get(url)
        
        if (Array.isArray(response.data)) {
          return response.data
        } else if (response.data.results && Array.isArray(response.data.results)) {
          return response.data.results
        } else {
          console.warn('Unexpected response format from admin API:', response.data)
          return []
        }
      } catch (error) {
        console.error(`Failed to get ${type} annotations for dataset ${datasetId}:`, error)
        throw error // Re-throw to trigger fallback
      }
    }
  }
})
</script>
