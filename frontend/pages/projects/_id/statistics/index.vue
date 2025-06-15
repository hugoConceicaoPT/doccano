<template>
  <v-row>
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

    <!-- Filters -->
    <v-col cols="12">
      <v-card class="mb-4">
        <v-card-title>Filters</v-card-title>
        <v-card-text>
          <v-row>
            <v-col cols="12" sm="6" md="3">
              <v-select
                v-model="selectedPerspectiveQuestion"
                :items="perspectiveQuestions"
                label="Perspective Questions"
                multiple
                chips
                deletable-chips
              ></v-select>
            </v-col>
            <v-col cols="12" sm="6" md="3">
              <v-select
                v-model="selectedPerspectiveAnswer"
                :items="perspectiveAnswers"
                label="Perspective Answers"
                multiple
                chips
                deletable-chips
              ></v-select>
            </v-col>
            <v-col cols="12" sm="6" md="3">
              <v-select
                v-model="selectedAnnotations"
                :items="annotationOptions"
                label="Annotations"
                multiple
                chips
                deletable-chips
              ></v-select>
            </v-col>
            <v-col cols="12" sm="6" md="3">
              <v-select
                v-model="selectedAnnotators"
                :items="annotatorOptions"
                label="Annotators"
                multiple
                chips
                deletable-chips
              ></v-select>
            </v-col>
            <v-col cols="12" sm="6" md="3">
              <v-select
                v-model="selectedDiscrepancy"
                :items="discrepancyOptions"
                label="Discrepancy Status"
              ></v-select>
            </v-col>
            <v-col cols="12" sm="6" md="3">
              <v-select
                v-model="exportOption"
                :items="exportOptions"
                label="Export Format"
              ></v-select>
            </v-col>
          </v-row>
          <v-row>
            <v-col cols="12" class="d-flex justify-end">
              <v-btn
                color="primary"
                class="mr-2"
                @click="applyFilters"
              >
                Apply Filters
              </v-btn>
              <v-btn
                color="error"
                class="mr-2"
                :disabled="!hasActiveFilters"
                @click="resetFilters"
              >
                Clear All Filters
              </v-btn>
              <v-btn
                color="secondary"
                :to="localePath(`/projects/${projectId}`)"
              >
                Back to Home
              </v-btn>
            </v-col>
          </v-row>
        </v-card-text>
      </v-card>
    </v-col>

    <!-- Filtered Results -->
    <v-col v-if="filtersApplied" cols="12">
      <perspective-distribution-table
        :perspective-distribution="perspectiveDistribution"
        :selected-perspective-question="selectedPerspectiveQuestion"
        :selected-perspective-answer="selectedPerspectiveAnswer"
        :selected-annotations="selectedAnnotations"
        :selected-annotators="selectedAnnotators"
        :example-map="exampleMap"
      />
    </v-col>

    <v-col v-if="filtersApplied" cols="12">
      <label-percentage-distribution
        title="Label Discrepancy Percentage"
        :distribution="filteredCategoryPercentage"
        :examples="examples"
        :label-types="categoryTypes"
        :dataset-reviews="datasetReviews"
        :example-map="exampleMap"
        :selected-discrepancy="selectedDiscrepancy"
      />
    </v-col>
  </v-row>
</template>

<script lang="ts">
import Vue from 'vue'
import { mdiClose, mdiFilterCheck, mdiHome, mdiAlert } from '@mdi/js'
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
      mdiAlert,
      showWarningDialog: false,
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

  async fetch() {
    try {
      this.categoryTypes = await this.$services.categoryType.list(this.projectId)
      this.categoryPercentage = await this.$repositories.metrics.fetchCategoryPercentage(this.projectId)
      this.perspectiveDistribution = await this.$repositories.statistics.fetchPerspectiveAnswerDistribution(this.projectId)
      this.datasetReviews = await this.$services.datasetReviewService.list(this.projectId)
      this.members = await this.$repositories.member.list(this.projectId)
      this.examples = await this.$services.example.list(this.projectId, {})
      this.annotators = this.members
        .filter((m: MemberItem) => m.isAnnotator)
        .map((item) => item.name)
      
      // Check if project is already closed in localStorage
      const isProjectClosed = localStorage.getItem(`project_closed_${this.projectId}`) === 'true'
      
      // Only show warning dialog if project is not closed
      this.showWarningDialog = !isProjectClosed
    } catch (error) {
      this.handleError(error)
    }
  },

  computed: {
    ...mapGetters('projects', ['project']),

    projectId() {
      return this.$route.params.id
    },

    exampleMap(): Record<string, string> {
      return this.examples?.items
        ? Object.fromEntries(
            this.examples.items.map((example: any) => [
              example.id,
              example.filename.replace(/\.[^/.]+$/, '')
            ])
          )
        : {}
    },

    filteredCategoryPercentage() {
      if (!this.filtersApplied) return this.categoryPercentage

      const filtered: Record<string, any> = {}

      for (const [key, value] of Object.entries(this.categoryPercentage)) {
        // Check if the annotation matches the selected annotations
        const matchesAnnotation = 
          this.selectedAnnotations.length === 0 || 
          this.selectedAnnotations.includes(Number(key))

        // Check if the discrepancy matches
        const datasetReview = this.datasetReviews.find(review => review.example === Number(key))
        let isDiscrepant = false

        if (datasetReview) {
          isDiscrepant = !datasetReview.is_approved
        } else {
          const minPercentage = this.$store.getters['projects/project']?.minPercentage || 70
          isDiscrepant = Object.values(value).every(percentage => Number(percentage) < minPercentage)
        }

        const matchesDiscrepancy = 
          this.selectedDiscrepancy === 'all' ||
          (this.selectedDiscrepancy === 'yes' && isDiscrepant) ||
          (this.selectedDiscrepancy === 'no' && !isDiscrepant)

        if (matchesAnnotation && matchesDiscrepancy) {
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
        this.exportOption !== 'None' ||
        this.selectedDiscrepancy !== 'all'
      )
    },

    perspectiveQuestions() {
      return Object.values(this.perspectiveDistribution).map((q) => q.question)
    },

    perspectiveAnswers() {
      if (!this.selectedPerspectiveQuestion.length) {
        // If no questions are selected, return all possible answers
        const allAnswers = new Set<string>()
        Object.values(this.perspectiveDistribution).forEach((entry: any) => {
          Object.keys(entry.answers).forEach(answer => allAnswers.add(answer))
        })
        return Array.from(allAnswers)
      }
      
      const answers = new Set<string>()
      for (const question of this.selectedPerspectiveQuestion) {
        const entry = Object.values(this.perspectiveDistribution).find(
          (q) => q.question === question
        )
        if (entry) {
          Object.keys(entry.answers).forEach(answer => answers.add(answer))
        }
      }
      return Array.from(answers)
    },

    annotationOptions() {
      return this.examples?.items?.map((item: any) => ({
        text: item.filename.replace(/\.[^/.]+$/, ''),
        value: item.id
      })) || []
    },

    annotatorOptions() {
      return this.annotators
    },

    discrepancyOptions() {
      return [
        { text: 'All', value: 'all' },
        { text: 'Discrepancy', value: 'yes' },
        { text: 'Non Discrepancy', value: 'no' }
      ]
    },

    exportOptions() {
      return ['None', 'PDF', 'CSV', 'PDF & CSV']
    }
  },

  methods: {
    async applyFilters() {
      this.filtersApplied = true
      try {
        // Fetch perspective distribution with filters
        this.perspectiveDistribution = await this.$repositories.statistics.fetchPerspectiveAnswerDistribution(
          this.projectId
        )

        // Fetch category percentage with filters
        this.categoryPercentage = await this.$repositories.metrics.fetchCategoryPercentage(
          this.projectId
        )

        if (this.exportOption !== 'None') {
          this.export()
        }
      } catch (error) {
        this.handleError(error)
      }
    },

    resetFilters() {
      this.selectedPerspectiveQuestion = []
      this.selectedPerspectiveAnswer = []
      this.selectedAnnotations = []
      this.selectedAnnotators = []
      this.exportOption = 'None'
      this.selectedDiscrepancy = 'all'
      this.filtersApplied = false
      this.$fetch()
    },

    handleError(error: any) {
      console.error(error)
      if (error.response && error.response.status === 400) {
        this.errorMessage = 'Error retrieving data.'
      } else {
        this.errorMessage = 'Database is slow or unavailable. Please try again later.'
      }
    },

    export() {
      try {
        if (this.exportOption === 'None') return

        const projectName = this.project.name

        if (this.exportOption === 'PDF' || this.exportOption === 'PDF & CSV') {
          const doc = new JsPDF()
          let y = 20

          // Add project name and title
          doc.setFontSize(20)
          doc.text(`Project: ${projectName}`, 14, y)
          y += 10
          doc.setFontSize(16)
          doc.text('Statistics Report', 14, y)
          y += 15

          // Add applied filters
          if (this.hasActiveFilters) {
            doc.setFontSize(14)
            doc.text('Applied Filters:', 14, y)
            y += 10
            doc.setFontSize(12)

            if (this.selectedPerspectiveQuestion.length) {
              doc.text(`Perspective Questions: ${this.selectedPerspectiveQuestion.join(', ')}`, 20, y)
              y += 7
            }
            if (this.selectedPerspectiveAnswer.length) {
              doc.text(`Perspective Answers: ${this.selectedPerspectiveAnswer.join(', ')}`, 20, y)
              y += 7
            }
            if (this.selectedAnnotations.length) {
              const annotationNames = this.selectedAnnotations.map(id => this.exampleMap[id] || id)
              doc.text(`Annotations: ${annotationNames.join(', ')}`, 20, y)
              y += 7
            }
            if (this.selectedAnnotators.length) {
              doc.text(`Annotators: ${this.selectedAnnotators.join(', ')}`, 20, y)
              y += 7
            }
            if (this.selectedDiscrepancy !== 'all') {
              doc.text(`Discrepancy: ${this.selectedDiscrepancy === 'yes' ? 'Discrepancy' : 'Non Discrepancy'}`, 20, y)
              y += 7
            }
            y += 5
          }

          // Add perspective distribution table
          doc.setFontSize(14)
          doc.text('Perspective Distribution', 14, y)
          y += 10

          const perspectiveData = []
          for (const key in this.perspectiveDistribution) {
            const entry = this.perspectiveDistribution[key]
            
            // Filter by selected perspective question
            if (this.selectedPerspectiveQuestion.length > 0 && 
                !this.selectedPerspectiveQuestion.includes(entry.question)) {
              continue
            }

            const answers = Object.entries(entry.answers)
              .map(([answer, data]) => ({
                answer,
                percentage: this.selectedAnnotators.length === 1 ? 100 : data.percentage,
                annotator: data.annotator
              }))
              .filter(answer => {
                // Filter by selected annotators
                const matchesAnnotator = 
                  this.selectedAnnotators.length === 0 || 
                  this.selectedAnnotators.includes(answer.annotator)

                // Filter by selected perspective answer
                const matchesAnswer = 
                  this.selectedPerspectiveAnswer.length === 0 ||
                  this.selectedPerspectiveAnswer.includes(answer.answer)

                return matchesAnnotator && matchesAnswer
              })

            if (answers.length > 0) {
              perspectiveData.push({
                question: entry.question,
                answers: answers.map(a => `${a.answer} (${a.percentage}%)`).join(', '),
                annotator: answers.map(a => a.annotator).join(', ')
              })
            }
          }

          if (perspectiveData.length > 0) {
            autoTable(doc, {
              startY: y,
              head: [['Question', 'Answers', 'Annotator']],
              body: perspectiveData.map(item => [item.question, item.answers, item.annotator]),
              theme: 'grid',
              headStyles: { fillColor: [41, 128, 185], textColor: 255 },
              styles: { fontSize: 10, cellPadding: 5 },
              columnStyles: {
                0: { cellWidth: 60 },
                1: { cellWidth: 70 },
                2: { cellWidth: 60 }
              }
            })
          } else {
            doc.setFontSize(12)
            doc.text('No data available', 14, y)
          }

          y = (doc as any).lastAutoTable.finalY + 15

          // Add label distribution table
          doc.setFontSize(14)
          doc.text('Label Distribution', 14, y)
          y += 10

          const labelData = []
          for (const [datasetId, labels] of Object.entries(this.filteredCategoryPercentage)) {
            const datasetName = this.exampleMap[datasetId] || datasetId
            const datasetReview = this.datasetReviews.find(review => review.example === Number(datasetId))
            let isDiscrepant = false

            if (datasetReview) {
              isDiscrepant = !datasetReview.is_approved
            } else {
              const minPercentage = this.$store.getters['projects/project']?.minPercentage || 70
              isDiscrepant = Object.values(labels).every(percentage => Number(percentage) < minPercentage)
            }

            const labelInfo = Object.entries(labels)
              .map(([label, percentage]) => `${label}: ${Math.round(Number(percentage))}%`)
              .join(', ')

            labelData.push({
              dataset: datasetName,
              labels: labelInfo,
              isDiscrepant: isDiscrepant ? 'Yes' : 'No'
            })
          }

          if (labelData.length > 0) {
            autoTable(doc, {
              startY: y,
              head: [['Dataset', 'Labels', 'Discrepancy']],
              body: labelData.map(item => [item.dataset, item.labels, item.isDiscrepant]),
              theme: 'grid',
              headStyles: { fillColor: [41, 128, 185], textColor: 255 },
              styles: { fontSize: 10, cellPadding: 5 },
              columnStyles: {
                0: { cellWidth: 50 },
                1: { cellWidth: 100 },
                2: { cellWidth: 40 }
              }
            })
          } else {
            doc.setFontSize(12)
            doc.text('No data available', 14, y)
          }

          doc.save(`${projectName}_statistics_report.pdf`)
        }

        if (this.exportOption === 'CSV' || this.exportOption === 'PDF & CSV') {
          // Create metadata section with project name and applied filters
          const metadata = [
            ['Project', projectName],
            ['']
          ]
          
          if (this.hasActiveFilters) {
            metadata.push(['Applied Filters'])
            metadata.push([''])
            
            if (this.selectedPerspectiveQuestion.length) {
              metadata.push(['Perspective Questions', this.selectedPerspectiveQuestion.join(', ')])
            }
            if (this.selectedPerspectiveAnswer.length) {
              metadata.push(['Perspective Answers', this.selectedPerspectiveAnswer.join(', ')])
            }
            if (this.selectedAnnotations.length) {
              metadata.push(['Annotations', this.selectedAnnotations.map(id => this.exampleMap[id] || id).join(', ')])
            }
            if (this.selectedAnnotators.length) {
              metadata.push(['Annotators', this.selectedAnnotators.join(', ')])
            }
            if (this.selectedDiscrepancy !== 'all') {
              metadata.push(['Discrepancy', this.selectedDiscrepancy === 'yes' ? 'Discrepancy' : 'Non Discrepancy'])
            }
            metadata.push([''])
          }

          // Prepare perspective distribution data
          const perspectiveData = []
          for (const key in this.perspectiveDistribution) {
            const entry = this.perspectiveDistribution[key]
            
            // Filter by selected perspective question
            if (this.selectedPerspectiveQuestion.length > 0 && 
                !this.selectedPerspectiveQuestion.includes(entry.question)) {
              continue
            }

            const answers = Object.entries(entry.answers)
              .map(([answer, data]) => ({
                answer,
                percentage: this.selectedAnnotators.length === 1 ? 100 : data.percentage,
                annotator: data.annotator
              }))
              .filter(answer => {
                // Filter by selected annotators
                const matchesAnnotator = 
                  this.selectedAnnotators.length === 0 || 
                  this.selectedAnnotators.includes(answer.annotator)

                // Filter by selected perspective answer
                const matchesAnswer = 
                  this.selectedPerspectiveAnswer.length === 0 ||
                  this.selectedPerspectiveAnswer.includes(answer.answer)

                return matchesAnnotator && matchesAnswer
              })

            if (answers.length > 0) {
              perspectiveData.push({
                Question: entry.question,
                Answers: answers.map(a => `${a.answer} (${a.percentage}%)`).join(', '),
                Annotator: answers.map(a => a.annotator).join(', ')
              })
            }
          }

          // Prepare label distribution data
          const labelData = []
          for (const [datasetId, labels] of Object.entries(this.filteredCategoryPercentage)) {
            const datasetName = this.exampleMap[datasetId] || datasetId
            const datasetReview = this.datasetReviews.find(review => review.example === Number(datasetId))
            let isDiscrepant = false

            if (datasetReview) {
              isDiscrepant = !datasetReview.is_approved
            } else {
              const minPercentage = this.$store.getters['projects/project']?.minPercentage || 70
              isDiscrepant = Object.values(labels).every(percentage => Number(percentage) < minPercentage)
            }

            const labelInfo = Object.entries(labels)
              .map(([label, percentage]) => `${label}: ${Math.round(Number(percentage))}%`)
              .join(', ')

            labelData.push({
              Dataset: datasetName,
              Labels: labelInfo,
              Discrepancy: isDiscrepant ? 'Yes' : 'No'
            })
          }

          // Combine all data
          const combinedData = [
            ...metadata,
            [''],
            ['Perspective Distribution'],
            ['']
          ]

          if (perspectiveData.length > 0) {
            combinedData.push(['Question', 'Answers', 'Annotator'])
            // Add perspective data
            perspectiveData.forEach(item => {
              combinedData.push([
                item.Question,
                item.Answers,
                item.Annotator
              ])
            })
          } else {
            combinedData.push(['No data available'])
          }

          // Add separator and label distribution header
          combinedData.push([''])
          combinedData.push(['Label Distribution'])
          combinedData.push([''])

          if (labelData.length > 0) {
            combinedData.push(['Dataset', 'Labels', 'Discrepancy'])
            // Add label data
            labelData.forEach(item => {
              combinedData.push([
                item.Dataset,
                item.Labels,
                item.Discrepancy
              ])
            })
          } else {
            combinedData.push(['No data available'])
          }

          // Create and download CSV file
          const csv = Papa.unparse(combinedData)
          const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' })
          const link = document.createElement('a')
          link.href = URL.createObjectURL(blob)
          link.download = `${projectName}_statistics_report.csv`
          link.click()
        }
      } catch (error) {
        this.handleError(error)
      }
    },

    onProceed() {
      localStorage.setItem(`project_closed_${this.projectId}`, 'true')
      this.showWarningDialog = false
    },

    onCancel() {
      this.showWarningDialog = false
      this.$router.push(this.localePath(`/projects/${this.projectId}`))
    }
  }
})
</script>
