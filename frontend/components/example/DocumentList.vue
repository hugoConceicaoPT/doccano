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
        <v-btn small outlined :color="isReported(row) ? 'success' : 'primary text-capitalize'" class="ms-1" @click="openReportDialog(row)">
          <v-icon left small>{{ isReported(row) ? require('@mdi/js').mdiCheckCircle : require('@mdi/js').mdiClipboardCheck }}</v-icon>
          {{ isReported(row) ? 'Reviewed' : 'Review' }}
        </v-btn>
      </template>
    </v-data-table>
    <v-dialog v-model="showReportDialog" max-width="800">
      <v-card>
        <v-card-title class="headline d-flex align-center">
          <v-icon class="mr-2" color="primary">{{ require('@mdi/js').mdiClipboardCheck }}</v-icon>
          Revisão de Concordância entre Anotadores
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
            <v-card
              v-for="label in datasetLabels"
              :key="label.name"
              class="mb-3"
              outlined
            >
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
                    <div v-if="label.annotators && label.annotators.length > 0" class="caption grey--text mt-1">
                      <strong>Anotadores:</strong> {{ label.annotators.join(', ') }}
                    </div>
                  </div>
                  
                  <div class="ml-4">
                    <v-btn-toggle
                      v-model="labelApprovals[label.name]"
                      mandatory
                      dense
                    >
                      <v-btn
                        small
                        :value="true"
                        color="success"
                        outlined
                      >
                        <v-icon small>{{ require('@mdi/js').mdiCheck }}</v-icon>
                        Concordância OK
                      </v-btn>
                      <v-btn
                        small
                        :value="false"
                        color="error"
                        outlined
                      >
                        <v-icon small>{{ require('@mdi/js').mdiAlert }}</v-icon>
                        Discrepância
                      </v-btn>
                    </v-btn-toggle>
                  </div>
                </div>
                
                <v-textarea
                  v-if="labelApprovals[label.name] === false"
                  v-model="labelComments[label.name]"
                  label="Comentário sobre discrepância (opcional)"
                  placeholder="Descreva a discrepância identificada..."
                  outlined
                  dense
                  rows="2"
                  class="mt-3"
                ></v-textarea>
              </v-card-text>
            </v-card>
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
      labelApprovals: {} as Record<string, boolean>,
      labelComments: {} as Record<string, string>,
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
      return this.reportForm.discrepancyType && this.reportForm.description && this.reportForm.severity
    },

    isReviewFormValid() {
      // Verifica se todas as labels foram aprovadas ou rejeitadas
      const allLabelsReviewed = this.datasetLabels.every(label => 
        this.labelApprovals[label.name] !== undefined
      )
      
      // Verifica se todas as labels rejeitadas têm comentários (opcional)
      const rejectedLabelsHaveComments = this.datasetLabels
        .filter(_label => this.labelApprovals[_label.name] === false)
        .every(_label => true) // Comentários são opcionais
      
      return allLabelsReviewed && rejectedLabelsHaveComments
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
      this.labelApprovals = {}
      this.labelComments = {}
      this.datasetLabels = []
    },

    isReported(item: ExampleDTO) {
      return this.reportedIds.includes(item.id)
    },

    async fetchDatasetLabels(_datasetId: number) {
      try {
        this.loadingLabels = true
        
        // Buscar o projeto para saber que tipo de labels usar
        const project = await this.$services.project.findById(this.projectId)
        
        let labelTypes = []
        let allAnnotations = []
        
        // Determinar que tipo de labels buscar baseado no tipo de projeto
        if (project.canDefineCategory) {
          labelTypes = await this.$services.categoryType.list(this.projectId)
          allAnnotations = await this.$repositories.category.list(this.projectId, _datasetId)
        } else if (project.canDefineSpan) {
          labelTypes = await this.$services.spanType.list(this.projectId)
          allAnnotations = await this.$repositories.span.list(this.projectId, _datasetId)
        } else {
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
        const totalAnnotators = userIds.length
        
        if (totalAnnotators === 0) {
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
          
          const agreementPercentage = totalAnnotators > 0 
            ? (usersWhoAnnotatedThisLabel / totalAnnotators) * 100 
            : 0
          
          labelAgreements[label.text] = {
            percentage: Math.round(agreementPercentage * 10) / 10,
            count: usersWhoAnnotatedThisLabel,
            total: totalAnnotators,
            annotators: annotatorsWithLabel,
            agreementDetails: `${usersWhoAnnotatedThisLabel} de ${totalAnnotators} anotadores concordam`
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
        
        // Inicializar os formulários com valores padrão
        this.labelApprovals = {}
        this.labelComments = {}
        this.datasetLabels.forEach(label => {
          this.labelApprovals[label.name] = undefined
          this.labelComments[label.name] = ''
        })
        
      } catch (error) {
        console.error('Erro ao carregar concordância de labels:', error)
        this.datasetLabels = []
        this.showSnackbar = true
        this.snackbarColor = 'error'
        this.snackbarMessage = 'Erro ao carregar concordância entre anotadores.'
      } finally {
        this.loadingLabels = false
      }
    },

    submitReview() {
      if (!this.itemToReport || !this.isReviewFormValid) return
      
      this.submittingReview = true
      try {
        const reviewData = {
          dataset_id: this.itemToReport.id,
          reviewed_by: this.$auth?.user?.id || 'anonymous',
          reviewed_at: new Date().toISOString(),
          label_approvals: this.datasetLabels.map(label => ({
            label_name: label.name,
            approved: this.labelApprovals[label.name],
            percentage: label.percentage,
            count: label.count,
            total: label.total,
            comment: this.labelComments[label.name] || null
          }))
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
        this.snackbarMessage = 'Revisão submetida com sucesso!'
        
        this.closeReportDialog()
        
      } catch (error) {
        console.error('Erro ao submeter revisão:', error)
        this.showSnackbar = true
        this.snackbarColor = 'error'
        this.snackbarMessage = 'Erro ao submeter revisão. Tente novamente.'
      } finally {
        this.submittingReview = false
      }
    }
  }
})
</script>
