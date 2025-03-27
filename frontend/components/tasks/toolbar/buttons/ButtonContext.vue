<template>
  <v-tooltip bottom>
    <template #activator="{ on }">
      <v-btn icon v-on="on" @click="handleClick">
        <v-icon>
          {{ mdiStar }}
        </v-icon>
      </v-btn>
    </template>
    <span>{{ $t('Contexto da Anotação') }}</span>
  </v-tooltip>
</template>

<script lang="ts">
import Vue from 'vue'
import { mdiStar } from '@mdi/js'

export default Vue.extend({
  data() {
    return {
      mdiStar
    }
  },
  methods: {
    handleClick() {
      this.$emit('click')
    }
  }
})
</script>
