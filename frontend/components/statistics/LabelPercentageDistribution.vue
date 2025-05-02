<template>
  <v-card>
    <v-card-title v-text="title" />
    <v-divider />
    <v-tabs show-arrows>
      <v-tab v-for="(value, user) in chartJSFormat" :key="user" class="text-capitalize">
        {{ exampleMap[user] }}
      </v-tab>
      <v-tab-item v-for="(value, user) in chartJSFormat" :key="user">
        <v-card-text>
          <chart-pie  @chart-ready="onLabelChartReady" :chart-data="value" />
        </v-card-text>
      </v-tab-item>
    </v-tabs>
  </v-card>
</template>

<script lang="ts">
import type { PropType } from 'vue'
import Vue from 'vue'
import ChartPie from './ChartPie.vue'
import { Distribution } from '~/domain/models/metrics/metrics'
import { LabelDTO } from '~/services/application/label/labelData'
import { ExampleListDTO } from '~/services/application/example/exampleData'

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
    },
    labelTypes: {
      type: Array as PropType<LabelDTO[]>,
      default: () => [],
      required: true
    },
    examples: {
      type: Object as PropType<ExampleListDTO>,
      default: () => {},
      required: true
    }
  },

  computed: {
    exampleMap(): Record<string, string> {
      return this.examples?.items
        ? Object.fromEntries(this.examples.items.map(example => [example.id, example.filename.replace(/\.[^/.]+$/, '')]))
        : {}
    },
    colorMapping(): { [text: string]: string } {
      return Object.fromEntries(
        this.labelTypes.map((labelType) => [labelType.text, labelType.backgroundColor])
      )
    },

    chartJSFormat(): any {
      const data: { [user: string]: { labels: string[]; datasets: any[] } } = {}
      for (const user in this.distribution) {
        const labels = Object.keys(this.distribution[user])
        labels.sort()
        const counts = labels.map((label) => parseInt((this.distribution[user][label]).toString()))
        const colors = labels.map((label) =>
          this.colorMapping[label] || '#00d1b2'
        )

        data[user] = {
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
    onLabelChartReady() {
      this.$emit('chart-label-rendered')
    }
  }
})
</script>
