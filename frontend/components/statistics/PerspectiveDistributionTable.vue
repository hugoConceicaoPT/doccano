<template>
  <v-card class="perspective-distribution mb-4">
    <v-card-title class="d-flex align-center">
      <span class="text-h6">Perspective Distribution</span>
    </v-card-title>

    <v-data-table
      :headers="perspectiveHeaders"
      :items="perspectiveTableItems"
      :items-per-page="5"
      class="elevation-1"
    >
      <template #[`item.question`]="{ item }">
        <div class="font-weight-medium">{{ item.question }}</div>
      </template>

      <template #[`item.answers`]="{ item }">
        <div class="d-flex flex-column gap-1">
          <div v-for="answer in item.answers" :key="answer.answer" class="d-flex align-center">
            <span class="text-body-1">{{ answer.answer }}</span>
          </div>
        </div>
      </template>

      <template #[`item.annotator`]="{ item }">
        <div class="d-flex flex-column gap-1">
          <div v-for="answer in item.answers" :key="answer.answer" class="d-flex align-center">
            <span class="text-body-1">{{ answer.annotator }}</span>
          </div>
        </div>
      </template>

      <template #[`item.distribution`]="{ item }">
        <div class="d-flex flex-column gap-2">
          <div v-for="answer in item.distribution" :key="answer.answer" class="d-flex align-center">
            <div class="percentage-bar-container">
              <div
                class="percentage-bar"
                :style="{
                  width: `${answer.percentage}%`
                }"
              ></div>
              <span class="percentage-text">{{ answer.percentage }}%</span>
            </div>
          </div>
        </div>
      </template>
    </v-data-table>
  </v-card>
</template>

<script lang="ts">
import Vue from 'vue'
import { PropType } from 'vue/types/options'

interface DistributionEntry {
  question: string
  answers: {
    [key: string]: {
      percentage: number
      annotator: string
    }
  }
}

export default Vue.extend({
  props: {
    perspectiveDistribution: {
      type: Object as PropType<{ [key: string]: DistributionEntry }>,
      required: true
    },
    selectedAnnotators: {
      type: Array as PropType<string[]>,
      default: () => []
    }
  },

  data() {
    return {
      headers: [
        { text: 'Question', value: 'question', sortable: true },
        { text: 'Answer', value: 'answer', sortable: true },
        { text: 'Percentage', value: 'percentage', sortable: true }
      ]
    }
  },

  computed: {
    perspectiveHeaders() {
      return [
        { text: 'Question', value: 'question' },
        { text: 'Answers', value: 'answers' },
        { text: 'Annotator', value: 'annotator' },
        { text: 'Distribution', value: 'distribution' }
      ]
    },

    perspectiveTableItems(): any[] {
      const items = []
      for (const key in this.perspectiveDistribution) {
        const entry = this.perspectiveDistribution[key]
        const answers = Object.entries(entry.answers)
          .map(([answer, data]) => ({
            answer,
            percentage: this.selectedAnnotators.length === 1 ? 100 : data.percentage,
            annotator: data.annotator
          }))
          .filter(answer => 
            this.selectedAnnotators.length === 0 || 
            this.selectedAnnotators.includes(answer.annotator)
          )

        if (answers.length > 0) {
          items.push({
            question: entry.question,
            answers,
            distribution: answers
          })
        }
      }
      return items
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
  width: 100%;
}

.percentage-bar {
  position: absolute;
  height: 100%;
  background-color: #73D8FF;
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
  pointer-events: none;
}
</style>
  