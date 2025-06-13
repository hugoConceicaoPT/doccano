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
    <v-col v-if="filtersApplied" cols="12">
      <perspective-percentage-distribution
        title="Perspective Distribution"
        :distribution="filteredPerspectiveDistribution"
        class="perspective-distribution"
        @chart-perspective-rendered="onPerspectiveChartReady"
      />
    </v-col>

    <v-col v-if="!!project.canDefineCategory && filtersApplied" cols="12">
      <label-percentage-distribution
        title="Label Discrepancy Percentage"
        :distribution="filteredCategoryPercentage"
        class="label-distribution"
        :examples="examples"
        :label-types="categoryTypes"
        @chart-label-rendered="onLabelChartReady"
      />
    </v-col>
  </v-row>
</template>

<script lang="ts">
import { mdiClose, mdiFilterCheck, mdiHome } from '@mdi/js'
import Papa from 'papaparse'
import html2canvas from 'html2canvas'
import { jsPDF as JsPDF } from 'jspdf'
import 'jspdf-autotable'
import Vue from 'vue'
import { mapGetters } from 'vuex'
import LabelPercentageDistribution from '~/components/statistics/LabelPercentageDistribution.vue'
import PerspectivePercentageDistribution from '~/components/statistics/PerspectivePercentageDistribution.vue'
import { MemberItem } from '~/domain/models/member/member'
import { Distribution } from '~/domain/models/statistics/statistics'

export default Vue.extend({
  components: {
    LabelPercentageDistribution,
    PerspectivePercentageDistribution
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

    filteredPerspectiveDistribution() {
      if (!this.selectedPerspectiveQuestion.length || !this.selectedPerspectiveAnswer.length) {
        return this.perspectiveDistribution
      }

      const dist: Distribution = {}

      for (const key in this.perspectiveDistribution) {
        const entry = this.perspectiveDistribution[key]

        if (this.selectedPerspectiveQuestion.includes(entry.question)) {
          const matchingAnswers = Object.keys(entry.answers).filter((answer) =>
            this.selectedPerspectiveAnswer.includes(answer)
          )

          if (matchingAnswers.length > 0) {
            dist[key] = {
              question: entry.question,
              answers: Object.fromEntries(matchingAnswers.map((a) => [a, entry.answers[a]])),
              total: matchingAnswers.reduce((sum, a) => sum + entry.answers[a], 0)
            }
          }
        }
      }

      return dist
    },

    filteredCategoryPercentage() {
      if (!this.filtersApplied) return this.categoryPercentage

      const filtered: Record<string, any> = {}

      for (const [key, value] of Object.entries(this.categoryPercentage)) {
        const matchesAnnotation =
          this.selectedAnnotations.length === 0 || this.selectedAnnotations.includes(Number(key))

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
      this.export()
    },
    onLabelChartReady() {
      this.isLabelChartReady = true
      this.export()
    },
    export() {
      if (this.isPerspectiveChartReady && this.isLabelChartReady) {
        try {
          if (this.exportOption === 'PDF') {
            this.exportPDF()
          } else if (this.exportOption === 'CSV') {
            this.exportCSV()
          } else if (this.exportOption === 'PDF & CSV') {
            this.exportPDF()
            this.exportCSV()
          }
        } catch (error) {
          this.handleError(error)
        } finally {
          this.isPerspectiveChartReady = false
          this.isLabelChartReady = false
        }
      }
    },
    exportCSV() {
      const data: any[] = []

      // Exportar Perspectivas
      for (const key in this.filteredPerspectiveDistribution) {
        const entry = this.filteredPerspectiveDistribution[key]
        for (const [answer, count] of Object.entries(entry.answers)) {
          data.push({
            Type: 'Perspective',
            Question: entry.question,
            Answer: answer,
            Percentage: count
          })
        }
      }

      // Exportar Discrepância de Categorias
      this.selectedAnnotations.forEach((annotationId, index) => {
        const categories = this.filteredCategoryPercentage[index]
        console.log(categories)
        if (!categories) return

        for (const [categoryName, percentage] of Object.entries(categories)) {
          data.push({
            Type: 'Label Discrepancy',
            AnnotationID: annotationId,
            Category: categoryName,
            Percentage: percentage
          })
        }
      })

      const csv = Papa.unparse(data)
      const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' })
      const link = document.createElement('a')
      link.href = URL.createObjectURL(blob)
      link.setAttribute('download', 'statistics.csv')
      document.body.appendChild(link)
      link.click()
      document.body.removeChild(link)
    },
    async exportPDF() {
      // Aguarda 500ms para garantir que os gráficos foram renderizados (podes ajustar o tempo conforme necessário)
      await new Promise((resolve) => setTimeout(resolve, 1000))

      const doc = new JsPDF()
      const filename = 'statistics.pdf'

      // Seleciona os gráficos pelo seletor de componente
      const perspectiveChart = document.querySelector('.perspective-distribution')
      const labelChart = document.querySelector('.label-distribution')

      if (!perspectiveChart || !labelChart) {
        console.error('Um ou mais elementos de gráfico não foram encontrados.')
        return
      }
      const addChartToPDF = async (element: Element, yOffset: number) => {
        if (!element) return yOffset

        const canvas = await html2canvas(element as HTMLElement, {
          scale: 2,
          useCORS: true
        })

        const imgData = canvas.toDataURL('image/png')
        const imgProps = doc.getImageProperties(imgData)
        const pdfWidth = doc.internal.pageSize.getWidth()
        const pdfHeight = (imgProps.height * pdfWidth) / imgProps.width

        doc.addImage(imgData, 'PNG', 10, yOffset, pdfWidth - 20, pdfHeight)
        return yOffset + pdfHeight + 10
      }

      const currentY = 10

      addChartToPDF(perspectiveChart, currentY)
        .then((y) => addChartToPDF(labelChart, y))
        .then(() => {
          doc.save(filename)
        })
        .catch((err) => {
          console.error('Erro ao gerar PDF com gráficos:', err)
        })
    }
  }
})
</script>
