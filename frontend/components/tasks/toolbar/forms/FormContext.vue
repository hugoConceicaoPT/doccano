<template>
  <v-form>
    <v-text-field
      v-model="context.text"
      :label="$t('Define context')"
      :placeholder="$t('annotation.newActionPlaceholder')"
      outlined
      dense
    />
    <v-btn color="primary" type="button" @click="handleSubmit">
      {{ $t('Create') }}
    </v-btn>
    <v-btn color="secondary" type="button" @click="handleCancel">
      {{ $t('Cancel') }}
    </v-btn>
  </v-form>
</template>

<script lang="ts">
import Vue from 'vue'

export default Vue.extend({
  data() {
    return {
      context: {
        text: ''
      }
    }
  },

  watch: {
    'context.text'(newVal) {
      console.log('FormContext.vue: context.text changed to:', newVal)
    }
  },
  methods: {
    async handleSubmit() {
      if (!this.context.text) return
      try {
        await this.$repositories.context.create(this.$route.params.id, this.context.text)
        this.context.text = ''
        this.$emit('refresh:comments')
        this.$emit('comment:added')
      } catch (e) {
        console.error('Erro ao adicionar comentário', e)
      }
    },
    handleCancel() {
      this.context.text = ''
      this.$emit('cancel:annotation')
    }
  }
})
</script>
