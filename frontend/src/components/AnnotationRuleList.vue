<template>
  <div class="annotation-rule-list">
    <div v-for="rule in rules" :key="rule.id" class="rule-item">
      <h3>{{ rule.name }}</h3>
      <p>{{ rule.description }}</p>
      // ... existing code ...
    </div>
  </div>
</template>

<script lang="ts">
import { defineComponent } from 'vue'

interface AnnotationRule {
  id: number
  name: string
  description: string
}

export default defineComponent({
  name: 'AnnotationRuleList',
  props: {
    rules: {
      type: Array as () => AnnotationRule[],
      required: true
    }
  }
})
</script>

// ... existing code ... 