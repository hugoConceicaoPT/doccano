<template>
  <confirm-form
    :items="selected"
    :title="title"
    :message="message"
    item-key="text"
    @ok="handleOk"
    @cancel="$emit('cancel')"
  />
</template>

<script lang="ts">
import Vue from 'vue'
import ConfirmForm from '@/components/utils/ConfirmForm.vue'

export default Vue.extend({
  components: {
    ConfirmForm
  },

  props: {
    selected: {
      type: Array,
      default: () => []
    }
  },

  computed: {
    title() {
      return this.selected.length > 0 ? 'Apagar Utilizadores Selecionados' : 'Apagar Todos os Não Superusers'
    },
    message() {
      return this.selected.length > 0
        ? 'Tem a certeza que deseja apagar estes utilizadores do projeto?'
        : 'Tem a certeza que deseja apagar todos os utilizadores não superusers do projeto?'
    }
  },

  methods: {
    handleOk() {
      if (this.selected.length > 0) {
        this.$emit('remove', this.selected)
      } else {
        this.$emit('removeAllNonSuperusers')
      }
    }
  }
})
</script>