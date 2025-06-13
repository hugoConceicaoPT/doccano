<template>
  <div>
    <v-dialog v-model="showWarningDialog" persistent max-width="500">
      <v-card>
        <v-card-title class="headline">
          <v-icon left color="warning" class="mr-2">{{ mdiAlert }}</v-icon>
          Attention
        </v-card-title>
        <v-card-text>
          If you proceed, the project will be closed and you will no longer be able to annotate,
          import datasets, etc. Do you wish to continue?
        </v-card-text>
        <v-card-actions>
          <v-spacer></v-spacer>
          <v-btn color="primary" text @click="onProceed">Proceed</v-btn>
          <v-btn color="secondary" text @click="onCancel">Cancel</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <v-card class="filter-card mb-4">
      <v-card-text>
        <v-row>
          <v-col cols="12" md="4">
            <v-select
              v-model="selectedExample"
              :items="exampleOptions"
              label="Selecione a anotação"
              dense
              outlined
              clearable
              hide-details
              placeholder="Select"
              :prepend-inner-icon="mdiFileDocumentOutline"
            />
          </v-col>
          <v-col cols="12" md="4">
            <v-select
              v-model="selectedPerspectiveQuestion"
              :items="perspectiveQuestions"
              label="Perspective Question"
              dense
              outlined
              hide-details
              placeholder="Select a question"
              :prepend-inner-icon="mdiHelpCircleOutline"
            />
          </v-col>
          <v-col v-if="selectedPerspectiveQuestion" cols="12" md="4">
            <v-select
              v-model="selectedPerspectiveAnswer"
              :items="possibleAnswers"
              label="Perspective Answer"
              dense
              outlined
              multiple
              hide-details
              placeholder="Select answer(s)"
              :prepend-inner-icon="mdiCheckboxMultipleMarkedOutline"
            />
          </v-col>
        </v-row>
        <v-row>
          <v-col cols="12" class="d-flex justify-end">
            <v-btn
              color="primary"
              outlined
              small
              @click="clearFilters"
              :disabled="!hasActiveFilters"
            >
              <v-icon left small>{{ mdiFilterRemove }}</v-icon>
              Clear Filters
            </v-btn>
          </v-col>
        </v-row>
      </v-card-text>
    </v-card>

    <v-card class="table-card">
      <v-data-table
        :items="flatItems"
        :headers="headers"
        :loading="isLoading"
        :loading-text="$t('generic.loading')"
        :no-data-text="$t('vuetify.noDataAvailable')"
        :footer-props="{
          showFirstLastPage: true,
          'items-per-page-text': $t('vuetify.itemsPerPageText'),
          'page-text': $t('dataset.pageText')
        }"
        :item-key="items.exampleName + '-' + items.labelName"
        show-select
        @input="$emit('input', $event)"
        class="elevation-0"
      >
        <template #top>
          <v-text-field
            v-model="search"
            :prepend-inner-icon="mdiMagnify"
            :label="$t('generic.search')"
            single-line
            hide-details
            filled
            class="mx-4 mt-4 mb-2"
            style="max-width: 300px"
          />
        </template>

        <template #[`header.data-table-select`]>
          <!-- slot vazio -->
        </template>

        <template #[`item.exampleName`]="{ item }">
          <div class="d-flex align-center">
            <v-icon small class="mr-2 primary--text">{{ mdiFileDocument }}</v-icon>
            {{ exampleNameMap[item.exampleName] }}
          </div>
        </template>

        <template #[`item.labelValue`]="{ item }">
          <div class="label-value" v-html="item.labelsValue.replace(/\n/g, '<br>')"></div>
        </template>

        <template #[`item.discrepancyBool`]="{ item }">
          <v-chip
            :color="item.discrepancyBool === 'Yes' ? 'error' : 'success'"
            small
            class="font-weight-medium"
          >
            <v-icon left small>{{ item.discrepancyBool === 'Yes' ? mdiAlert : mdiCheck }}</v-icon>
            {{ item.discrepancyBool }}
          </v-chip>
        </template>
      </v-data-table>
    </v-card>
  </div>
</template>

<script lang="ts">
import Vue from 'vue'
import {
  mdiMagnify,
  mdiPencil,
  mdiAlert,
  mdiCheck,
  mdiFileDocument,
  mdiFileDocumentOutline,
  mdiHelpCircleOutline,
  mdiCheckboxMultipleMarkedOutline,
  mdiFilterRemove
} from '@mdi/js'
import type { PropType } from 'vue'
import { Percentage } from '~/domain/models/metrics/metrics'
import { Distribution } from '~/domain/models/statistics/statistics'
import { ExampleDTO } from '~/services/application/example/exampleData'

export default Vue.extend({
  props: {
    isLoading: {
      type: Boolean,
      default: false,
      required: true
    },
    items: {
      type: Object as PropType<Percentage>,
      required: true
    },
    discrepancyThreshold: {
      type: Number,
      default: 0,
      required: true
    }
  },

  data() {
    return {
      search: '',
      mdiMagnify,
      mdiPencil,
      mdiAlert,
      mdiCheck,
      mdiFileDocument,
      mdiFileDocumentOutline,
      mdiHelpCircleOutline,
      mdiCheckboxMultipleMarkedOutline,
      mdiFilterRemove,
      selectedExample: 'Todas as anotações',
      exampleNameMap: {} as Record<string, string>,
      isReady: false,
      selectedPerspectiveQuestion: '',
      selectedPerspectiveAnswer: [] as string[],
      perspectiveDistribution: {} as Distribution,
      example: {} as ExampleDTO,
      showWarningDialog: false
    }
  },

  computed: {
    perspectiveQuestions(): Array<{ text: string; value: string }> {
      return Object.entries(this.perspectiveDistribution).map(([id, q]) => ({
        text: q.question,
        value: id
      }))
    },

    possibleAnswers(): string[] {
      const entry = this.perspectiveDistribution[this.selectedPerspectiveQuestion]
      return entry ? Object.keys(entry.answers) : []
    },
    // Header com três colunas: Criador, Pergunta e Resposta
    headers() {
      return [
        { text: 'Example', value: 'exampleName', sortable: true },
        { text: 'Has Discrepancy', value: 'discrepancyBool', sortable: false },
        { text: 'Label', value: 'labelValue', sortable: true }
      ]
    },
    projectId(): string {
      return this.$route.params.id
    },
    flatItems(): Array<{
      exampleName: string
      labelsValue: string
      discrepancyBool: string
    }> {
      const rows = []

      const source = this.filteredItems
      for (const [exampleName, labels] of Object.entries(source)) {
        // If no question is selected, use original percentages
        if (!this.selectedPerspectiveQuestion) {
          const labelsValue = Object.entries(labels)
            .filter(([label]) => this.matchesSearch(label))
            .map(([label, percent]) => `${label}: ${Math.round(Number(percent))}%`)
            .join('\n')

          if (labelsValue) {
            const notHasDiscrepancy = Object.values(labels).some(
              (percentage) => Number(percentage) > this.discrepancyThreshold
            )

            rows.push({
              exampleName,
              labelsValue,
              discrepancyBool: notHasDiscrepancy ? 'No' : 'Yes'
            })
          }
          continue
        }

        // Get the example's perspective answers for the selected question
        const examplePerspectiveAnswers = this.perspectiveDistribution[this.selectedPerspectiveQuestion]?.answers || {}
        console.log(examplePerspectiveAnswers)
        // Filter answers based on selected answers
        const filteredAnswers = this.selectedPerspectiveAnswer.length > 0
          ? Object.entries(examplePerspectiveAnswers).filter(([answer]) => 
              this.selectedPerspectiveAnswer.includes(answer)
            )
          : Object.entries(examplePerspectiveAnswers)

        // Calculate total annotators for the filtered answers
        const totalAnnotators = filteredAnswers.reduce((sum, [_, count]) => sum + count, 0)

        // Calculate percentages based on filtered annotators
        const filteredLabels = Object.entries(labels).map(([label, percentage]) => {
          // For each label, calculate how many annotators selected it
          const labelAnnotators = Math.round((Number(percentage) * totalAnnotators) / 100)
          // Calculate the percentage based on the actual number of annotators
          const adjustedPercentage = totalAnnotators > 0 
            ? (labelAnnotators / totalAnnotators) * 100
            : 0
          return [label, adjustedPercentage] as [string, number]
        })

        const labelsValue = filteredLabels
          .filter(([label]) => this.matchesSearch(label))
          .map(([label, percent]) => `${label}: ${Math.round(percent)}%`)
          .join('\n')

        if (labelsValue) {
          const notHasDiscrepancy = filteredLabels.some(
            ([_, percentage]) => percentage > this.discrepancyThreshold
          )

          rows.push({
            exampleName,
            labelsValue,
            discrepancyBool: notHasDiscrepancy ? 'No' : 'Yes'
          })
        }
      }

      return rows
    },

    exampleOptions(): Array<{ text: string; value: string }> {
      return [
        { text: 'Todas as anotações', value: 'Todas as anotações' },
        ...Object.entries(this.exampleNameMap).map(([id, name]) => ({
          text: name,
          value: id
        }))
      ]
    },

    filteredItems(): Percentage {
      console.log(this.items)
      if (!this.selectedExample || this.selectedExample === 'Todas as anotações') {
        return this.items
      }

      const selected = this.items[this.selectedExample]

      if (selected) {
        return { [this.selectedExample]: selected }
      }

      return {}
    },

    hasActiveFilters(): boolean {
      return (
        this.selectedExample !== 'Todas as anotações' ||
        this.selectedPerspectiveQuestion !== '' ||
        this.selectedPerspectiveAnswer.length > 0 ||
        this.search !== ''
      )
    }
  },

  watch: {
    items: {
      immediate: true,
      handler(newItems) {
        this.loadExampleNames(newItems)
      }
    }
  },
  async created() {
    try {
      this.perspectiveDistribution =
        await this.$repositories.statistics.fetchPerspectiveAnswerDistribution(this.projectId)
    } catch (error) {
      console.error(error)
    }
  },
  mounted() {
    this.showWarningDialog = localStorage.getItem(`project_closed_${this.projectId}`) !== 'true'
  },

  methods: {
    matchesSearch(label: string): boolean {
      return label.toLowerCase().includes(this.search.toLowerCase())
    },
    async resolveExampleName(id: string) {
      if (!this.exampleNameMap[id]) {
        const example = await this.$repositories.example.findById(this.projectId, Number(id))
        this.$set(this.exampleNameMap, id, example.filename.replace(/\.[^/.]+$/, ''))
      }
      return this.exampleNameMap[id]
    },
    async loadExampleNames(items: Percentage) {
      const exampleNames = Object.keys(items)
      await Promise.all(exampleNames.map(this.resolveExampleName))
    },
    onProceed() {
      localStorage.setItem(`project_closed_${this.projectId}`, 'true')
      this.showWarningDialog = false
    },
    onCancel() {
      this.showWarningDialog = false
      this.$router.push(this.localePath(`/projects/${this.projectId}`))
    },
    clearFilters() {
      this.selectedExample = 'Todas as anotações'
      this.selectedPerspectiveQuestion = ''
      this.selectedPerspectiveAnswer = [] as string[]
      this.search = ''
    }
  }
})
</script>

<style scoped>
.filter-card {
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05) !important;
}

.table-card {
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05) !important;
}

::v-deep .v-data-table {
  background: transparent !important;
}

::v-deep .v-data-table thead th {
  font-weight: 600 !important;
  color: rgba(0, 0, 0, 0.87) !important;
  background: #f5f5f5 !important;
}

::v-deep .v-data-table tbody tr:hover {
  background: #f5f5f5 !important;
}

::v-deep .v-chip {
  font-size: 0.75rem;
  height: 24px;
}

.label-value {
  white-space: pre-line;
  line-height: 1.5;
  font-size: 0.875rem;
}

::v-deep .v-select .v-select__selections {
  padding-top: 0;
}

::v-deep .v-select.v-text-field--outlined .v-select__selections {
  padding: 0 8px;
}
</style>
