<template>
  <v-card>
    <v-card-title class="d-flex align-center">
      <span class="text-h6">{{ title }}</span>
    </v-card-title>
    <v-divider />
    <v-data-table
      :headers="headers"
      :items="tableItems"
      :search="search"
      :items-per-page="10"
      class="elevation-1"
    >
      <template #[`item.dataset`]="{ item }">
        <div class="font-weight-medium text-subtitle-1">{{ item.dataset }}</div>
      </template>

      <template #[`item.labels`]="{ item }">
        <div class="d-flex flex-column gap-2">
          <div v-for="(label, index) in item.labels" :key="index" class="d-flex align-center">
            <div class="d-flex align-center" style="min-width: 150px">
              <div
                class="color-dot mr-2"
                :style="{ backgroundColor: label.color }"
              ></div>
              <span class="text-body-1">{{ label.name }}</span>
            </div>
          </div>
        </div>
      </template>

      <template #[`item.distribution`]="{ item }">
        <div class="d-flex flex-column gap-2">
          <div v-for="(label, index) in item.labels" :key="index" class="d-flex align-center">
            <div class="percentage-bar-container" style="width: 200px">
              <div
                class="percentage-bar"
                :style="{
                  width: `${label.percentage}%`,
                  backgroundColor: label.color
                }"
              ></div>
              <span class="percentage-text">{{ label.percentage }}%</span>
            </div>
          </div>
        </div>
      </template>

      <template #[`item.isDiscrepant`]="{ item }">
        <v-chip
          :color="item.isDiscrepant ? 'error' : 'success'"
          small
          class="font-weight-bold px-3"
          :outlined="!item.isDiscrepant"
        >
          <v-icon left small :color="item.isDiscrepant ? 'error' : 'success'">
            {{ item.isDiscrepant ? 'mdi-alert-circle' : 'mdi-check-circle' }}
          </v-icon>
          {{ item.isDiscrepant ? 'Yes' : 'No' }}
        </v-chip>
      </template>
    </v-data-table>
  </v-card>
</template>

<script lang="ts">
import type { PropType } from 'vue'
import Vue from 'vue'
import { Distribution } from '~/domain/models/metrics/metrics'
import { LabelDTO } from '~/services/application/label/labelData'
import { ExampleListDTO } from '~/services/application/example/exampleData'
import { DatasetReviewItem } from '~/domain/models/datasetReview/datasetReview'

export default Vue.extend({
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
    },
    datasetReviews: {
      type: Array as PropType<DatasetReviewItem[]>,
      required: true
    }
  },

  data() {
    return {
      search: '',
      headers: [
        { text: 'Dataset', value: 'dataset', sortable: true, width: '25%' },
        { text: 'Labels', value: 'labels', sortable: false, width: '25%' },
        { text: 'Distribution', value: 'distribution', sortable: false, width: '35%' },
        { text: 'Discrepancy', value: 'isDiscrepant', sortable: true, width: '15%' }
      ]
    }
  },

  computed: {
    exampleMap(): Record<string, string> {
      return this.examples?.items
        ? Object.fromEntries(
            this.examples.items.map((example) => [
              example.id,
              example.filename.replace(/\.[^/.]+$/, '')
            ])
          )
        : {}
    },

    colorMapping(): { [text: string]: string } {
      return Object.fromEntries(
        this.labelTypes.map((labelType) => [labelType.text, labelType.backgroundColor])
      )
    },

    tableItems(): any[] {
      const items = []
      const discrepancyThreshold = 70 // You can make this a prop if needed

      for (const [datasetId, labels] of Object.entries(this.distribution)) {
        const datasetName = this.exampleMap[datasetId] || datasetId
        const labelItems = []
        
        // Verifica se existe um dataset review para este example
        const datasetReview = this.datasetReviews.find(review => review.example === Number(datasetId))
        let isDiscrepant: boolean

        if (datasetReview) {
          // Se existe dataset review, usa is_approved para determinar discrepância
          isDiscrepant = !datasetReview.is_approved
        } else {
          // Se não existe dataset review, usa a lógica anterior baseada no threshold
          isDiscrepant = Object.values(labels).every(percentage => Number(percentage) < discrepancyThreshold)
        }
        
        for (const [labelName, percentage] of Object.entries(labels)) {
          const percentageValue = Number(percentage)
          labelItems.push({
            name: labelName,
            percentage: Math.round(percentageValue),
            color: this.colorMapping[labelName] || '#00d1b2'
          })
        }

        items.push({
          dataset: datasetName,
          labels: labelItems,
          isDiscrepant
        })
      }

      return items
    }
  },

  methods: {
    onLabelChartReady() {
      this.$emit('chart-label-rendered')
    }
  }
})
</script>

<style scoped>
.percentage-bar-container {
  position: relative;
  height: 24px;
  background-color: #f5f5f5;
  border-radius: 4px;
  overflow: hidden;
  margin: 4px 0;
}

.percentage-bar {
  position: absolute;
  height: 100%;
  transition: all 0.3s ease;
}

.percentage-text {
  position: absolute;
  left: 50%;
  top: 50%;
  transform: translate(-50%, -50%);
  color: #666;
  font-size: 0.875rem;
  font-weight: bold;
  z-index: 1;
}

.color-dot {
  width: 12px;
  height: 12px;
  border-radius: 50%;
}

.search-field {
  max-width: 200px;
}

.v-chip {
  min-width: 100px;
  justify-content: center;
  font-size: 0.9rem;
  letter-spacing: 0.5px;
}
</style>
