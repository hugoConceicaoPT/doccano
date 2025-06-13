<template>
  <div>
    <v-card>
      <v-alert
        v-if="errorMessage"
        class="mx-4 my-4"
        type="error"
        dismissible
        @click="errorMessage = ''"
      >
        {{ errorMessage }}
      </v-alert>
      <v-alert
        v-if="message.text"
        class="mx-4 my-4"
        :type="message.type"
        dismissible
        @click="message = { type: '', text: '' }"
      >
        {{ message.text }}
      </v-alert>
      <v-card-title>
        Discrepancy Threshold:
        {{ project && project.minPercentage !== undefined ? project.minPercentage : '-' }} %
      </v-card-title>
      <discrepancy-list
        v-model="selected"
        :items="items"
        :is-loading="isLoading"
        :discrepancy-threshold="
          project && project.minPercentage !== undefined ? project.minPercentage : 0
        "
        @message="handleMessage"
      />
    </v-card>
  </div>
</template>

<script lang="ts">
import Vue from 'vue'
import { mapGetters } from 'vuex'
import DiscrepancyList from '~/components/discrepancy/DiscrepancyList.vue'
import { Percentage } from '~/domain/models/metrics/metrics'

export default Vue.extend({
  components: {
    DiscrepancyList
  },

  layout: 'project',

  middleware: ['check-auth', 'auth'],

  data() {
    return {
      items: {} as Percentage,
      isLoading: false,
      drawerLeft: null,
      selected: {} as Percentage,
      errorMessage: '',
      message: {
        type: '',
        text: ''
      }
    }
  },

  async fetch() {
    this.isLoading = true
    try {
      this.items = await this.$repositories.metrics.fetchCategoryPercentage(this.projectId)
    } catch (error) {
      this.handleError(error)
    }
    this.isLoading = false
  },

  computed: {
    ...mapGetters('projects', ['project']),

    projectId(): string {
      return this.$route.params.id
    }
  },

  watch: {
    project: {
      handler(newVal) {
        if (newVal) {
          this.$fetch()
        }
      },
      immediate: true,
      deep: true
    }
  },
  methods: {
    handleError(error: any) {
      if (error.response && error.response.status === 400) {
        this.errorMessage = 'Error retrieving data.'
      } else {
        this.errorMessage = 'Database is slow or unavailable. Please try again later.'
      }
    },
    handleMessage(message: { type: string; text: string }) {
      this.message = message
    }
  }
})
</script>

<style scoped>
::v-deep .v-dialog {
  width: 800px;
}
</style>
