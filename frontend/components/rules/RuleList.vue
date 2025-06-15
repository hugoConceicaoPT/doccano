<template>
  <div>
    <v-card class="filter-card mb-4">
      <v-card-text>
        <v-row>
          <v-col cols="12" md="6">
            <v-select
              v-model="selectedVersion"
              :items="availableVersions"
              label="Select the version"
              clearable
              outlined
              dense
              hide-details
              class="mb-4"
              :prepend-inner-icon="mdiTagMultiple"
              color="primary"
              multiple
              chips
            />
          </v-col>
          <v-col cols="12" md="6">
            <v-select
              v-model="selectedRule"
              :items="availableRules"
              label="Select the rule"
              clearable
              outlined
              dense
              hide-details
              class="mb-4"
              :prepend-inner-icon="mdiFileDocument"
              color="primary"
              multiple
              chips
            />
          </v-col>
          <v-col cols="12" md="6">
            <v-select
              v-model="selectedResult"
              :items="resultOptions"
              label="Select the result"
              clearable
              outlined
              dense
              hide-details
              class="mb-4"
              :prepend-inner-icon="mdiCheckCircle"
              color="primary"
              multiple
              chips
            />
          </v-col>
        </v-row>
      </v-card-text>
    </v-card>

    <v-card class="table-card">
      <v-card-title class="d-flex align-center py-3">
        <span class="text-subtitle-1 font-weight-medium">
          <v-icon class="mr-1 primary--text">{{ mdiViewList }}</v-icon>
          Rules List
        </span>
        <v-spacer></v-spacer>
        <v-text-field
          v-model="search"
          :prepend-inner-icon="mdiMagnify"
          :label="$t('generic.search')"
          single-line
          hide-details
          filled
          dense
          class="ml-4 search-field"
          color="primary"
        />
      </v-card-title>

      <v-divider></v-divider>

      <v-data-table
        class="rules-table"
        :items="filteredItems"
        :headers="headers"
        :loading="isLoading"
        :loading-text="$t('generic.loading')"
        :no-data-text="$t('vuetify.noDataAvailable')"
        :footer-props="{
          showFirstLastPage: true,
          'items-per-page-text': $t('vuetify.itemsPerPageText'),
          'page-text': $t('dataset.pageText')
        }"
        item-key="exampleName + id"
        @input="$emit('input', $event)"
      >
        <template #[`header.data-table-select`]> </template>
        <template #[`item.numberVersion`]="{ item }">
          <v-chip
            small
            outlined
            color="primary"
            class="font-weight-medium"
          >
            {{ item.numberVersion }}
          </v-chip>
        </template>

        <template #[`item.ruleDiscussion`]="{ item }">
          <div class="text-body-2">{{ item.ruleDiscussion }}</div>
        </template>

        <template #[`item.votesFor`]="{ item }">
          <v-chip
            color="success"
            dark
            small
            class="font-weight-medium"
          >
            {{ item.votesFor }}
          </v-chip>
        </template>

        <template #[`item.votesAgainst`]="{ item }">
          <v-chip
            color="error"
            dark
            small
            class="font-weight-medium"
          >
            {{ item.votesAgainst }}
          </v-chip>
        </template>

        <template #[`item.result`]="{ item }">
          <v-chip
            :color="
              item.result === 'Approved'
                ? 'success'
                : item.result === 'Rejected'
                ? 'error'
                : 'warning'
            "
            dark
            class="font-weight-medium"
          >
            {{ item.result }}
          </v-chip>
        </template>
      </v-data-table>
    </v-card>
  </div>
</template>

<script lang="ts">
import Vue from 'vue'
import type { PropType } from 'vue'
import {
  mdiMagnify,
  mdiPencil,
  mdiTagMultiple,
  mdiFileDocument,
  mdiViewList,
  mdiCheckCircle
} from '@mdi/js'
import { Discussion } from '~/pages/projects/_id/rules/index.vue'

export default Vue.extend({
  props: {
    isLoading: {
      type: Boolean,
      default: false,
      required: true
    },
    items: {
      type: Array as PropType<Discussion[]>,
      required: true
    }
  },

  data() {
    return {
      search: '',
      mdiMagnify,
      mdiPencil,
      mdiTagMultiple,
      mdiFileDocument,
      mdiViewList,
      mdiCheckCircle,
      selectedVersion: [] as string[],
      exampleNameMap: {} as Record<string, string>,
      selectedRule: [] as string[],
      selectedResult: [] as string[],
      isReady: false
    }
  },

  computed: {
    headers() {
      return [
        { text: 'Version', value: 'numberVersion', sortable: true },
        { text: 'Rule', value: 'ruleDiscussion', sortable: true },
        { text: 'Votes For', value: 'votesFor', sortable: true },
        { text: 'Votes Against', value: 'votesAgainst', sortable: true },
        { text: 'Result', value: 'result', sortable: true }
      ]
    },
    projectId(): string {
      return this.$route.params.id
    },
    resultOptions() {
      return ['Approved', 'Rejected']
    },
    filteredItems(): Discussion[] {
      let result = this.items.filter(
        (item) =>
          item.numberVersion.toLowerCase().includes(this.search.toLowerCase()) ||
          item.ruleDiscussion.toLowerCase().includes(this.search.toLowerCase())
      )

      if (this.selectedVersion.length > 0) {
        result = result.filter((item) => this.selectedVersion.includes(item.numberVersion))
      }
      if (this.selectedRule.length > 0) {
        result = result.filter((item) => this.selectedRule.includes(item.ruleDiscussion))
      }
      if (this.selectedResult.length > 0) {
        result = result.filter((item) => this.selectedResult.includes(item.result))
      }

      return result
    },
    availableVersions(): string[] {
      if (this.selectedRule.length === 0) {
        return [...new Set(this.items.map((item) => item.numberVersion))]
      }

      return [
        ...new Set(
          this.items
            .filter((item) => this.selectedRule.includes(item.ruleDiscussion))
            .map((item) => item.numberVersion)
        )
      ]
    },
    availableRules(): string[] {
      if (this.selectedVersion.length === 0) {
        return [...new Set(this.items.map((item) => item.ruleDiscussion))]
      }

      return [
        ...new Set(
          this.items
            .filter((item) => this.selectedVersion.includes(item.numberVersion))
            .map((item) => item.ruleDiscussion)
        )
      ]
    }
  }
})
</script>

<style scoped>
.filter-card {
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05) !important;
}

.table-card {
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05) !important;
}

.search-field {
  max-width: 300px;
}

::v-deep .v-data-table {
  border-radius: 8px;
}

::v-deep .v-data-table-header th {
  font-weight: 600 !important;
  white-space: nowrap;
  color: rgba(0, 0, 0, 0.87) !important;
  font-size: 0.875rem !important;
  background-color: #f5f5f5 !important;
}

::v-deep .v-data-table__wrapper {
  border-radius: 8px;
}

::v-deep .v-data-table__wrapper table {
  border-collapse: separate;
  border-spacing: 0;
}

::v-deep .v-data-table__wrapper table tbody tr:hover {
  background-color: #f5f5f5;
}

::v-deep .v-chip {
  font-size: 0.75rem;
  height: 24px;
  margin: 2px;
}

::v-deep .v-select__selections {
  padding-top: 4px;
}
</style>
