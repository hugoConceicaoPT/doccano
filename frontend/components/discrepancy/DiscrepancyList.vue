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
            <v-select v-model="selectedExample" :items="exampleOptions" label="Selecione a anotação" dense outlined
              multiple hide-details placeholder="Select" :prepend-inner-icon="mdiFileDocumentOutline" />
          </v-col>
          <v-col cols="12" md="4">
            <v-select v-model="selectedPerspectiveQuestion" :items="perspectiveQuestions" label="Perspective Question"
              dense outlined hide-details placeholder="Select a question" :prepend-inner-icon="mdiHelpCircleOutline" />
          </v-col>
          <v-col v-if="selectedPerspectiveQuestion" cols="12" md="4">
            <v-select v-model="selectedPerspectiveAnswer" :items="possibleAnswers" label="Perspective Answer" dense
              outlined multiple hide-details placeholder="Select answer(s)"
              :prepend-inner-icon="mdiCheckboxMultipleMarkedOutline" />
          </v-col>
        </v-row>
        <v-row>
          <v-col cols="12" class="d-flex justify-start">
            <v-btn color="primary" outlined small :disabled="!hasActiveFilters" @click="clearFilters">
              <v-icon left small>{{ mdiFilterRemove }}</v-icon>
              Clear Filters
            </v-btn>
            <v-btn color="secondary" outlined small class="ml-2" @click="$router.push(localePath(`/projects/${projectId}`))">
              <v-icon left small>{{ mdiHome }}</v-icon>
              Home
            </v-btn>
          </v-col>
        </v-row>
      </v-card-text>
    </v-card>

    <v-card class="table-card">
      <v-data-table :items="flatItems" :headers="headers" :loading="isLoading" :loading-text="$t('generic.loading')"
        :no-data-text="$t('vuetify.noDataAvailable')" :footer-props="{
          showFirstLastPage: true,
          'items-per-page-text': $t('vuetify.itemsPerPageText'),
          'page-text': $t('dataset.pageText')
        }" :item-key="items.exampleName + '-' + items.labelName" show-select class="elevation-0"
        @input="$emit('input', $event)">
        <template #top>
          <v-text-field v-model="search" :prepend-inner-icon="mdiMagnify" :label="$t('generic.search')" single-line
            hide-details filled class="mx-4 mt-4 mb-2" style="max-width: 300px" />
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
          <v-chip :color="item.discrepancyBool === 'Yes' ? 'error' : 'success'" small class="font-weight-medium">
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
  mdiFilterRemove,
  mdiHome
} from '@mdi/js'
import type { PropType } from 'vue'
import { Percentage } from '~/domain/models/metrics/metrics'
import { Distribution } from '~/domain/models/statistics/statistics'
import { ExampleDTO } from '~/services/application/example/exampleData'
import { PerspectiveDTO } from '~/services/application/perspective/perspectiveData'
import { MemberItem } from '~/domain/models/member/member'

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
    perspective: {
      type: Object as PropType<PerspectiveDTO>,
      required: true
    },
    categoryDistribution: {
      type: Object as PropType<Distribution>,
      required: true
    },
    discrepancyThreshold: {
      type: Number,
      default: 0,
      required: true
    },
    members: {
      type: Array as PropType<MemberItem[]>,
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
      mdiHome,
      selectedExample: [] as string[],
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
    flatItems(): Array<{ exampleName: string; labelsValue: string; discrepancyBool: string }> {
      const rows: Array<{ exampleName: string; labelsValue: string; discrepancyBool: string }> = []

      const source = this.filteredItems
      for (const [exampleName, labels] of Object.entries(source)) {
        // Sem pergunta ou resposta selecionada, usa percentuais originais
        if (!this.selectedPerspectiveQuestion || !this.selectedPerspectiveAnswer.length) {
          const labelsValue = Object.entries(labels)
            .filter(([label]) => this.matchesSearch(label))
            .map(([label, percent]) => {
              return `${label}: ${Math.round(Number(percent))}%`
            })
            .join('\n')

          if (labelsValue) {
            const hasDiscrepancy = Object.values(labels).every(
            (percentage) => percentage < this.discrepancyThreshold
            );

            rows.push({
              exampleName,
              labelsValue,
              discrepancyBool: hasDiscrepancy ? 'Yes' : 'No'
            })
          }
          continue
        }
        const questionId = Number(this.selectedPerspectiveQuestion)

        // Para cada resposta selecionada, obter percentuais por example
        const percentagesForAnswers = this.selectedPerspectiveAnswer
          .map(answerText => this.getLabelPercentagesForAnswer(questionId, answerText))
          .filter(p => Object.keys(p).length > 0)

        // Combina percentuais para o example atual
        const combinedPercentages: Record<string, number> = {}

        for (const percentagesByExample of percentagesForAnswers) {
          const examplePercentages = percentagesByExample[exampleName]
          if (!examplePercentages) continue

          for (const [label, percent] of Object.entries(examplePercentages)) {
            combinedPercentages[label] = (combinedPercentages[label] || 0) + percent
          }
        }

        const totalPercent = Object.values(combinedPercentages).reduce((sum, val) => sum + val, 0)
        const normalizedPercentages = totalPercent > 0
          ? Object.fromEntries(
            Object.entries(combinedPercentages).map(([label, percent]) => [label, (percent / totalPercent) * 100])
          )
          : {}

        const labelsValue = Object.entries(normalizedPercentages)
          .filter(([label]) => this.matchesSearch(label))
          .map(([label, percent]) => {
            return `${label}: ${Math.round(percent)}%`
          })
          .join('\n')
        
        if (labelsValue) {
          const hasDiscrepancy = Object.values(normalizedPercentages).every(
            (percentage) => percentage < this.discrepancyThreshold
          );

          rows.push({
            exampleName,
            labelsValue,
            discrepancyBool: hasDiscrepancy ? 'Yes' : 'No'
          })
        }
      }

      return rows
    },

    exampleOptions(): Array<{ text: string; value: string }> {
      return Object.entries(this.exampleNameMap).map(([id, name]) => ({
        text: name,
        value: id
      }))
    },

    filteredItems(): Percentage {
      if (!this.selectedExample || this.selectedExample.length === 0) {
        return this.items
      }

      const filtered: Percentage = {}
      for (const exampleId of this.selectedExample) {
        const selected = this.items[exampleId]
        if (selected) {
          filtered[exampleId] = selected
        }
      }

      return filtered
    },

    hasActiveFilters(): boolean {
      return (
        this.selectedExample.length > 0 ||
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
    getLabelPercentagesForAnswer(questionId: number, selectedAnswerText: string): Record<string, Record<string, number>> {
      const percentagesByExample: Record<string, Record<string, number>> = {}

      // 1. Encontrar a pergunta
      const question = this.perspective.questions.find(q => q.id === questionId)
      if (!question) return {}
      // 2. Filtrar respostas que têm o texto desejado
      const matchingAnswers = question.answers.filter(a => a.answer_text === selectedAnswerText)
      if (matchingAnswers.length === 0) return {}
      // 3. Obter IDs dos membros que deram essa resposta
      const memberIds = matchingAnswers.map(a => a.member).filter(m => m !== undefined)
      if (memberIds.length === 0) return {}

      // 4. Obter nomes dos membros
      const memberNames = memberIds.map(id => {
        const member = this.members.find((m: MemberItem) => m.id === id)
        return member ? member.name : null
      }).filter(name => name !== null) as string[]

      // 5. Para cada membro, somar os votos por example e calcular percentagens
      for (const memberName of memberNames) {
        const examples = this.categoryDistribution[memberName]
        if (!examples) continue

        for (const [exampleId, labelCounts] of Object.entries(examples)) {
          // Inicializar objeto se não existir
          if (!percentagesByExample[exampleId]) {
            percentagesByExample[exampleId] = {}
          }

          // Somar os votos por label para aquele example
          for (const [label, count] of Object.entries(labelCounts)) {
            const value = Number(count) || 0
            percentagesByExample[exampleId][label] = (percentagesByExample[exampleId][label] || 0) + value
          }
        }
      }

      // 6. Agora calcular porcentagens por label para cada exampleId
      for (const exampleId in percentagesByExample) {
        const labelCounts = percentagesByExample[exampleId]

        const totalVotes = Object.values(labelCounts).reduce((sum, val) => sum + val, 0)
        if (totalVotes === 0) {
          for (const label of Object.keys(labelCounts)) {
            labelCounts[label] = 0
          }
        } else {
          for (const label of Object.keys(labelCounts)) {
            labelCounts[label] = (labelCounts[label] / totalVotes) * 100
          }
        }
      }
      return percentagesByExample
    },


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
      this.selectedExample = [] as string[]
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
