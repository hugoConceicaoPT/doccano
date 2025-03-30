<template>
  <v-card>
    <v-card-title>
      <action-menu @create="$router.push('perspectives/add')" />
    </v-card-title>
    <perspective-list v-model="selected" :items="items" :is-loading="isLoading" />
  </v-card>
</template>

<script lang="ts">
import Vue from 'vue'
import { mapGetters } from 'vuex'
import ActionMenu from '@/components/perspective/ActionMenu.vue'
import PerspectiveList from '@/components/perspective/PerspectiveList.vue'
import { PerspectiveDTO } from '~/services/application/perspective/perspectiveData'

export default Vue.extend({
  components: {
    ActionMenu,
    PerspectiveList
  },

  layout: 'project',

  middleware: ['check-auth', 'auth', 'isSuperUser', 'setCurrentProject'],

  data() {
    return {
      items: [] as PerspectiveDTO[],
      selected: [] as PerspectiveDTO[],
      isLoading: false,
      tab: 0,
      drawerLeft: null
    }
  },

  computed: {
    ...mapGetters('auth', ['isStaff', 'isSuperUser'])
  },

  mounted() {
    this.fetchPerspectives()
  },

  methods: {
    async fetchPerspectives() {
      this.isLoading = true
      try {
        // Obtém o projectId a partir dos parâmetros da rota
        const projectId = this.$route.params.id
        const response = await this.$services.perspective.list(projectId)
        this.items = response
      } catch (error) {
        console.error('Erro ao buscar perspectivas:', error)
      } finally {
        this.isLoading = false
      }
    }
  }
})
</script>

<style scoped>
::v-deep .v-dialog {
  width: 800px;
}
</style>
