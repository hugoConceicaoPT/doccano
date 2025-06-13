<template>
  <v-card>
    <v-card-title v-text="title" />
    <v-divider />
    <v-tabs show-arrows>
      <v-tab v-for="(value, questionId) in chartJSFormat" :key="questionId" class="text-capitalize">
        {{ value.question }}
      </v-tab>

      <v-tab-item v-for="(value, questionId) in chartJSFormat" :key="questionId">
        <v-card-text>
          <chart-pie :chart-data="value" @chart-ready="onPerspectiveChartReady" />
        </v-card-text>
      </v-tab-item>
    </v-tabs>
  </v-card>
</template>

<script lang="ts">
import type { PropType } from 'vue'
import Vue from 'vue'
import ChartPie from './ChartPie.vue'
import { Distribution } from '~/domain/models/statistics/statistics'

export default Vue.extend({
  components: {
    ChartPie
  },

  props: {
    title: {
      type: String,
      required: true,
      default: 'Distribution'
    },
    distribution: {
      type: Object as PropType<Distribution>,
      required: true
    }
  },

  computed: {
    chartJSFormat(): any {
      const data: {
        [questionId: string]: { labels: string[]; datasets: any[]; question: string }
      } = {}

      for (const questionId in this.distribution) {
        const { question, answers } = this.distribution[questionId]

        const labels = Object.keys(answers)
        labels.sort()

        const counts = labels.map((label) => parseFloat(answers[label].toString()))
        const colors = labels.map((_label, index) => this.pickColor(index))

        data[questionId] = {
          question,
          labels,
          datasets: [
            {
              data: counts,
              backgroundColor: colors
            }
          ]
        }
      }
      return data
    }
  },

  methods: {
    pickColor(index: number): string {
      const colors = ['#00d1b2', '#ff3860', '#ffdd57', '#3273dc', '#23d160', '#b86bff']
      return colors[index % colors.length]
    },
    onPerspectiveChartReady() {
      this.$emit('chart-perspective-rendered')
    }
  }
})
</script>
