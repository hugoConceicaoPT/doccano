<template>
  <div>
    <v-card class="discrepancies-card">
      <v-card-title class="d-flex align-center py-4">
        <span class="text-h5 font-weight-medium">
          <v-icon left class="mr-2 primary--text">{{ mdiAlertCircle }}</v-icon>
          Discrepancies
        </span>
        <v-spacer></v-spacer>
        <v-chip
          color="primary"
          outlined
          class="ml-2"
        >
          <v-icon left small>{{ mdiPercent }}</v-icon>
          Threshold: {{ project && project.minPercentage !== undefined ? project.minPercentage : '-' }}%
        </v-chip>
      </v-card-title>

      <v-divider></v-divider>

      <v-card-text class="pa-4">
        <v-alert
          v-if="errorMessage"
          class="mb-4"
          type="error"
          dismissible
          @click="errorMessage = ''"
        >
          
          {{ errorMessage }}
        </v-alert>
        <v-alert
          v-if="message.text"
          class="mb-4"
          :type="message.type"
          dismissible
          @click="message = { type: '', text: '' }"
        >
          <v-icon left>{{ mdiInformation }}</v-icon>
          {{ message.text }}
        </v-alert>

        <discrepancy-list
          v-model="selected"
          :items="items"
          :perspective="perspective"
          :category-distribution="categoryDistribution"
          :is-loading="isLoading"
          :discrepancy-threshold="
            project && project.minPercentage !== undefined ? project.minPercentage : 0
          "
          :members="members"
          @message="handleMessage"
        />
      </v-card-text>
    </v-card>
  </div>
</template>

<script lang="ts">
import Vue from 'vue'
import { mapGetters } from 'vuex'
import {
  mdiAlertCircle,
  mdiInformation,
  mdiPercent
} from '@mdi/js'
import DiscrepancyList from '~/components/discrepancy/DiscrepancyList.vue'
import { Percentage } from '~/domain/models/metrics/metrics'
import { PerspectiveDTO } from '~/services/application/perspective/perspectiveData'
import { Distribution } from '~/domain/models/metrics/metrics'
import { MemberItem } from '~/domain/models/member/member'

export default Vue.extend({
  components: {
    DiscrepancyList
  },

  layout: 'project',

  middleware: ['check-auth', 'auth'],

  data() {
    return {
      items: {} as Percentage,
      perspective: {} as PerspectiveDTO | null,
      categoryDistribution: {} as Distribution,
      isLoading: false,
      drawerLeft: null,
      selected: {} as Percentage,
      errorMessage: '',
      message: {
        type: '',
        text: ''
      },
      mdiAlertCircle,
      mdiInformation,
      mdiPercent,
      members: [] as MemberItem[]
    }
  },

  async fetch() {
    this.isLoading = true
    try {
      this.items = await this.$repositories.metrics.fetchCategoryPercentage(this.projectId)
      this.perspective = await this.$services.perspective.list(this.projectId)
      this.categoryDistribution = await this.$repositories.metrics.fetchCategoryDistribution(this.projectId)
      this.members = await this.$repositories.member.list(this.projectId)
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
.discrepancies-card {
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05) !important;
}

::v-deep .v-card__title {
  padding: 16px;
}

::v-deep .v-card__text {
  padding: 16px;
}

::v-deep .v-alert {
  border-radius: 8px;
}

::v-deep .v-chip {
  font-size: 0.875rem;
  height: 32px;
}
</style>
