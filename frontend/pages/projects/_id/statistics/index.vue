<template>
  <v-row>
    <v-col cols="12">
      <v-alert
        v-if="errorMessage"
        class="mx-4 my-4"
        type="error"
        dismissible
        @click="errorMessage = ''"
      >
        {{ errorMessage }}
      </v-alert>
    </v-col>
    <v-col cols="12">
      <!-- Filtros -->
      <v-card class="pa-4 mb-4 elevation-1">
        <v-form>
          <v-row dense>
            <!-- Pergunta -->
            <v-col cols="12" md="4">
              <v-select
                v-model="selectedPerspectiveQuestion"
                :items="perspectiveQuestions"
                label="Perspective Question"
                multiple
                dense
                outlined
                hide-details
                placeholder="Select"
              />
            </v-col>

            <!-- Resposta -->
            <v-col v-if="selectedPerspectiveQuestion" cols="12" md="4">
              <v-select
                v-model="selectedPerspectiveAnswer"
                :items="possibleAnswers"
                label="Perspective Answer"
                dense
                outlined
                multiple
                hide-details
                placeholder="Select"
              />
            </v-col>

            <!-- Anotação -->
            <v-col cols="12" md="4">
              <v-select
                v-model="selectedAnnotations"
                :items="formattedAnnotations"
                item-text="text"
                item-value="value"
                label="Annotation"
                dense
                outlined
                multiple
                hide-details
                placeholder="Select"
              />
            </v-col>

            <!-- Anotador -->
            <v-col cols="12" md="4">
              <v-select
                v-model="selectedAnnotators"
                :items="annotators"
                label="Annotator"
                dense
                outlined
                hide-details
                multiple
                placeholder="Select"
              />
            </v-col>

            <!-- Exportação -->
            <v-col cols="12" md="4">
              <v-select
                v-model="exportOption"
                :items="['None', 'PDF', 'CSV', 'PDF & CSV']"
                label="Export"
                dense
                outlined
                hide-details
                placeholder="Format"
              />
            </v-col>
            <v-col cols="12" md="4">
              <v-select
                v-model="selectedDiscrepancy"
                :items="[
                  { text: 'All', value: 'all' },
                  { text: 'Discrepancy', value: 'yes' },
                  { text: 'Non Discrepancy', value: 'no' }
                ]"
                label="Discrepancy"
                dense
                outlined
                hide-details
              />
            </v-col>

            <!-- Botões -->
            <v-col cols="12" md="4" class="d-flex align-center">
              <v-btn color="primary" small class="mr-2" @click="applyFilters">
                <v-icon left small>{{ mdiFilterCheck }}</v-icon>
                Apply Filters
              </v-btn>
              <v-btn color="grey" small :disabled="!hasActiveFilters" @click="resetFilters">
                <v-icon left small>{{ mdiClose }}</v-icon>
                Clear All
              </v-btn>
              <v-btn
                color="secondary"
                class="ms-2"
                small
                @click="$router.push(localePath(`/projects/${projectId}`))"
              >
                <v-icon left small>{{ mdiHome }}</v-icon>
                Home
              </v-btn>
            </v-col>
          </v-row>
        </v-form>
      </v-card>
    </v-col>

    <!-- Resultados filtrados -->
    <v-col v-if="!!projectId && filtersApplied" cols="12">
      <perspective-distribution-table
        :perspective-distribution="perspectiveDistribution"
        :selected-perspective-question="selectedPerspectiveQuestion"
        :selected-perspective-answer="selectedPerspectiveAnswer"
        :selected-annotators="selectedAnnotators"
      />
    </v-col>

    <v-col v-if="!!projectId && filtersApplied" cols="12">
      <label-percentage-distribution
        title="Label Discrepancy Percentage"
        :distribution="filteredCategoryPercentage"
        class="label-distribution"
        :examples="examples"
        :label-types="categoryTypes"
        :dataset-reviews="datasetReviews"
        @chart-label-rendered="onLabelChartReady"
      />
    </v-col>
  </v-row>
</template>

<script lang="ts">
import Vue from 'vue'
import { mdiClose, mdiFilterCheck, mdiHome } from '@mdi/js'
import Papa from 'papaparse'
import { jsPDF as JsPDF } from 'jspdf'
import autoTable from 'jspdf-autotable'
import { mapGetters } from 'vuex'
import LabelPercentageDistribution from '~/components/statistics/LabelPercentageDistribution.vue'
import PerspectiveDistributionTable from '~/components/statistics/PerspectiveDistributionTable.vue'
import { MemberItem } from '~/domain/models/member/member'
import { Distribution } from '~/domain/models/statistics/statistics'
import { DatasetReviewItem } from '~/domain/models/datasetReview/datasetReview'

declare module 'jspdf' {
  interface jsPDF {
    autoTable: (options: any) => jsPDF;
  }
}

export default Vue.extend({
  components: {
    LabelPercentageDistribution,
    PerspectiveDistributionTable
  },
  layout: 'project',

  middleware: ['check-auth', 'auth'],
  data() {
    return {
      selectedPerspectiveQuestion: [] as string[],
      selectedPerspectiveAnswer: [] as string[],
      selectedAnnotations: [] as number[],
      selectedAnnotators: [] as string[],
      exportOption: 'None',
      mdiClose,
      mdiFilterCheck,
      mdiHome,
      annotations: [],
      categoryTypes: [] as any[],
      categoryPercentage: {} as Record<string, any>,
      examples: {} as any,
      perspectiveDistribution: {} as Distribution,
      datasetReviews: [] as DatasetReviewItem[],
      annotators: [] as string[],
      members: [] as MemberItem[],
      errorMessage: '',
      isPerspectiveChartReady: false,
      isLabelChartReady: false,
      selectedDiscrepancy: 'all' as string,
      filtersApplied: false
    }
  },

  computed: {
    ...mapGetters('projects', ['project']),

    projectId() {
      return this.$route.params.id
    },

    filteredCategoryPercentage() {
      if (!this.filtersApplied) return this.categoryPercentage

      const filtered: Record<string, any> = {}

      for (const [key, value] of Object.entries(this.categoryPercentage)) {
        // Check if the annotation matches the selected annotations
        const matchesAnnotation = 
          this.selectedAnnotations.length === 0 || 
          this.selectedAnnotations.includes(Number(key))

        if (matchesAnnotation) {
          filtered[key] = value
        }
      }

      return filtered
    },

    hasActiveFilters(): boolean {
      return (
        this.selectedPerspectiveQuestion.length > 0 ||
        this.selectedPerspectiveAnswer.length > 0 ||
        this.selectedAnnotations.length > 0 ||
        this.selectedAnnotators.length > 0 ||
        this.exportOption !== 'None'
      )
    },

    perspectiveQuestions() {
      return Object.values(this.perspectiveDistribution).map((q) => q.question)
    },
    possibleAnswers() {
      // Permitir que selectedPerspectiveQuestion seja array
      const questions = Array.isArray(this.selectedPerspectiveQuestion)
        ? this.selectedPerspectiveQuestion
        : []
      // Coletar todas as respostas possíveis para as perguntas selecionadas
      const answersSet = new Set<string>()
      Object.values(this.perspectiveDistribution).forEach((entry: any) => {
        if (questions.includes(entry.question)) {
          Object.keys(entry.answers).forEach((answer) => answersSet.add(answer))
        }
      })
      return Array.from(answersSet)
    },
    formattedAnnotations(): { text: string; value: number }[] {
      if (!this.examples || !this.examples.items) return []
      return this.examples.items.map((item: any) => ({
        text: item.filename.replace(/\.[^/.]+$/, ''),
        value: item.id
      }))
    }
  },

  async created() {
    try {
      this.examples = await this.$services.example.list(this.projectId, this.$route.query)
      this.members = await this.$repositories.member.list(this.projectId)
      this.datasetReviews = await this.$services.datasetReviewService.list(this.projectId)
      this.annotators = this.members
        .filter((m: MemberItem) => m.isAnnotator)
        .map((item) => item.name)
      this.perspectiveDistribution =
        await this.$repositories.statistics.fetchPerspectiveAnswerDistribution(this.projectId)
    } catch (error) {
      this.handleError(error)
    }
  },

  methods: {
    async applyFilters() {
      try {
        this.categoryTypes = await this.$services.categoryType.list(this.projectId)
        this.categoryPercentage = await this.$repositories.metrics.fetchCategoryPercentage(
          this.projectId
        )
        this.filtersApplied = true
        if (this.exportOption !== 'None') {
          this.export()
        }
      } catch (error) {
        this.handleError(error)
      }
    },

    handleError(error: any) {
      if (error.response && error.response.status === 400) {
        this.errorMessage = 'Error retrieving data.'
      } else {
        this.errorMessage = 'Database is slow or unavailable. Please try again later.'
      }
    },
    resetFilters() {
      this.selectedPerspectiveQuestion = []
      this.selectedPerspectiveAnswer = []
      this.selectedAnnotations = []
      this.selectedAnnotators = []
      this.exportOption = 'None'
      this.filtersApplied = false
    },
    onPerspectiveChartReady() {
      this.isPerspectiveChartReady = true
      if (this.exportOption !== 'None') {
        this.export()
      }
    },
    onLabelChartReady() {
      this.isLabelChartReady = true
      if (this.exportOption !== 'None') {
        this.export()
      }
    },
    export() {
      try {
        if (this.exportOption === 'PDF') {
          this.exportToPDF()
        } else if (this.exportOption === 'CSV') {
          this.exportToCSV()
        } else if (this.exportOption === 'PDF & CSV') {
          this.exportToPDF()
          this.exportToCSV()
        }
      } catch (error) {
        this.errorMessage = 'Failed to export report'
        console.error('Export error:', error)
      } finally {
        this.exportOption = 'None'
      }
    },
    exportToPDF() {
      try {
        const doc = new JsPDF()
        const pageWidth = doc.internal.pageSize.getWidth()
        const margin = 20
        let yPos = 20

        // Add title
        doc.setFontSize(16)
        doc.text('Statistics Report', pageWidth / 2, yPos, { align: 'center' })
        yPos += 20

        // Add filters section
        doc.setFontSize(12)
        doc.text('Filters Applied:', margin, yPos)
        yPos += 10

        const filters = [
          ['Perspective Questions:', this.selectedPerspectiveQuestion.join(', ') || 'None'],
          ['Perspective Answers:', this.selectedPerspectiveAnswer.join(', ') || 'None'],
          ['Annotations:', this.selectedAnnotations.join(', ') || 'None'],
          ['Annotators:', this.selectedAnnotators.join(', ') || 'None'],
          ['Discrepancy Status:', this.selectedDiscrepancy]
        ]

        filters.forEach(([label, value]) => {
          doc.setFontSize(10)
          doc.text(`${label} ${value}`, margin, yPos)
          yPos += 7
        })

        yPos += 10

        // Add Perspective Distribution section
        doc.setFontSize(12)
        doc.text('Perspective Distribution', margin, yPos)
        yPos += 10

        const perspectiveData = []
        for (const data of Object.values(this.perspectiveDistribution)) {
          if (this.selectedPerspectiveQuestion.length === 0 || 
              this.selectedPerspectiveQuestion.includes(data.question)) {
            const answers = Object.entries(data.answers)
              .filter(([answer, _data]) => 
                this.selectedPerspectiveAnswer.length === 0 || 
                this.selectedPerspectiveAnswer.includes(answer)
              )
              .filter(([_answer, answerData]) =>
                this.selectedAnnotators.length === 0 ||
                this.selectedAnnotators.includes(answerData.annotator)
              )
              .map(([answer, answerData]) => ({
                answer,
                percentage: answerData.percentage,
                annotator: answerData.annotator
              }))

            if (answers.length > 0) {
              perspectiveData.push({
                question: data.question,
                answers
              })
            }
          }
        }

        if (perspectiveData.length > 0) {
          const tableData = perspectiveData.flatMap(qData => 
            qData.answers.map(answer => [
              qData.question,
              answer.answer,
              `${answer.percentage}%`,
              answer.annotator
            ])
          )

          // @ts-ignore
          autoTable(doc, {
            startY: yPos,
            head: [['Question', 'Answer', 'Percentage', 'Annotator']],
            body: tableData,
            margin: { left: margin }
          })
          // @ts-ignore
          yPos = doc.lastAutoTable.finalY + 10
        }

        // Add Label Discrepancy Percentage section
        doc.setFontSize(12)
        doc.text('Label Discrepancy Percentage', margin, yPos)
        yPos += 10

        const labelData = Object.entries(this.filteredCategoryPercentage)
          .map(([label, percentage]) => [label, `${percentage}%`])

        if (labelData.length > 0) {
          // @ts-ignore
          autoTable(doc, {
            startY: yPos,
            head: [['Label', 'Percentage']],
            body: labelData,
            margin: { left: margin }
          })
        }

        // Save the PDF
        doc.save('statistics_report.pdf')
      } catch (error) {
        console.error('Error generating PDF:', error)
        this.errorMessage = 'Failed to generate PDF report'
      }
    },

    exportToCSV() {
      const data = []

      // Add filters information
      data.push(['Filters Applied'])
      data.push(['Perspective Questions:', this.selectedPerspectiveQuestion.join(', ') || 'None'])
      data.push(['Perspective Answers:', this.selectedPerspectiveAnswer.join(', ') || 'None'])
      data.push(['Annotations:', this.selectedAnnotations.join(', ') || 'None'])
      data.push(['Annotators:', this.selectedAnnotators.join(', ') || 'None'])
      data.push(['Discrepancy Status:', this.selectedDiscrepancy])
      data.push([])

      // Add Perspective Distribution data
      data.push(['Perspective Distribution'])
      data.push(['Question', 'Answer', 'Percentage', 'Annotator'])

      for (const qData of Object.values(this.perspectiveDistribution)) {
        if (this.selectedPerspectiveQuestion.length === 0 || 
            this.selectedPerspectiveQuestion.includes(qData.question)) {
          const answers = Object.entries(qData.answers)
            .filter(([answer, _data]) => 
              this.selectedPerspectiveAnswer.length === 0 || 
              this.selectedPerspectiveAnswer.includes(answer)
            )
            .filter(([_answer, answerData]) =>
              this.selectedAnnotators.length === 0 ||
              this.selectedAnnotators.includes(answerData.annotator)
            )

          answers.forEach(([answer, answerData]) => {
            data.push([
              qData.question,
              answer,
              `${answerData.percentage}%`,
              answerData.annotator
            ])
          })
        }
      }

      data.push([])

      // Add Label Discrepancy Percentage data
      data.push(['Label Discrepancy Percentage'])
      data.push(['Label', 'Percentage'])

      Object.entries(this.filteredCategoryPercentage).forEach(([label, percentage]) => {
        data.push([label, `${percentage}%`])
      })

      // Convert to CSV and download
      const csv = Papa.unparse(data)
      const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' })
      const url = URL.createObjectURL(blob)
      const link = document.createElement('a')
      link.href = url
      link.download = 'statistics_report.csv'
      document.body.appendChild(link)
      link.click()
      document.body.removeChild(link)
      URL.revokeObjectURL(url)
    }
  }
})
</script>
