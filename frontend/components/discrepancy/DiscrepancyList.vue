<template>
  <div>
    <v-select v-model="selectedExample" :items="exampleOptions" label="Selecione a anotação" clearable
      class="mb-4 mx-4" />

    <v-data-table class="mx-4" :items="flatItems" :headers="headers" :loading="isLoading"
      :loading-text="$t('generic.loading')" :no-data-text="$t('vuetify.noDataAvailable')" :footer-props="{
        showFirstLastPage: true,
        'items-per-page-text': $t('vuetify.itemsPerPageText'),
        'page-text': $t('dataset.pageText')
      }" :item-key="items.exampleName + '-' + items.labelName" show-select @input="$emit('input', $event)">
      <template #top>
        <v-text-field v-model="search" :prepend-inner-icon="mdiMagnify" :label="$t('generic.search')" single-line
          hide-details filled />
      </template>
      <!-- Oculta o checkbox do header -->
      <template #[`header.data-table-select`]>
        <!-- slot vazio -->
      </template>
      <template #[`item.exampleName`]="{ item }">
        {{ exampleNameMap[item.exampleName] }}
      </template>

      <template #[`item.labelPercentage`]="{ item }">
        {{ parseInt(item.labelPercentage) + "%" }}
      </template>

      <template #[`item.discrepancyBool`]="{ item }">
        <v-chip :color="item.discrepancyBool === 'Yes' ? 'error' : 'success'" dark>
          {{ item.discrepancyBool }}
        </v-chip>
      </template>
      <template #[`item.actions`]="{ item }">
        <v-icon small @click="$emit('edit', item)">
          {{ mdiPencil }}
        </v-icon>
      </template>
    </v-data-table>
  </div>
</template>

<script lang="ts">
import Vue from 'vue'
import { mdiMagnify, mdiPencil } from '@mdi/js'
import type { PropType } from 'vue'
import { Percentage } from '~/domain/models/metrics/metrics'

export default Vue.extend({
  props: {
    isLoading: {
      type: Boolean,
      default: false,
      required: true
    },
    items: {
      type: Object as PropType<Percentage>,
      required: true
    },
    discrepancyThreshold: {
      type: Number,
      default: 0,
      required: true
    }
  },

  data() {
    return {
      search: '',
      mdiMagnify,
      mdiPencil,
      selectedExample: null as string | null,
      exampleNameMap: {} as Record<string, string>,
      isReady: false
    }
  },

  computed: {
    // Header com três colunas: Criador, Pergunta e Resposta
    headers() {
      return [
        { text: 'Example', value: 'exampleName', sortable: true },
        { text: 'Has Discrepancy', value: 'discrepancyBool', sortable: false },
        { text: 'Name', value: 'labelName', sortable: true },
        { text: 'Percentage', value: 'labelPercentage', sortable: true },
        { text: 'Actions', value: 'actions', sortable: false }
      ]
    },
    projectId(): string {
      return this.$route.params.id
    },
    flatItems(): Array<{
      exampleName: string;
      labelName: string;
      labelPercentage: number;
      discrepancyBool: string;
    }> {
      const rows = [];

      const source = this.filteredItems;
      for (const [exampleName, labels] of Object.entries(source)) {
        const hasDiscrepancy = Object.values(labels).some(
          (percentage) => percentage > this.discrepancyThreshold
        );
        for (const [labelName, percentage] of Object.entries(labels)) {
          if (this.matchesSearch(labelName)) {
            rows.push({
              exampleName,
              labelName,
              labelPercentage: percentage,
              discrepancyBool: hasDiscrepancy ? 'Yes' : 'No',
            });
          }
        }
      }

      return rows;
    },

    exampleOptions(): Array<{ text: string; value: string }> {
      return [
        { text: 'Todas as anotações', value: 'Todas as anotações' },
        ...Object.entries(this.exampleNameMap).map(([id, name]) => ({
          text: name,
          value: id
        }))
      ]
    },

    filteredItems(): Percentage {
      if (!this.selectedExample || this.selectedExample === 'Todas as anotações') {
        return this.items;
      }

      const selected = this.items[this.selectedExample];

      if (selected) {
        return { [this.selectedExample]: selected };
      }

      return {};
    }
  },

  watch: {
    items: {
      immediate: true,
      handler(newItems) {
        this.loadExampleNames(newItems);
      }
    }
  },

  methods: {
    matchesSearch(label: string): boolean {
      return label.toLowerCase().includes(this.search.toLowerCase())
    },
    async resolveExampleName(id: string) {
      if (!this.exampleNameMap[id]) {
        const example = await this.$repositories.example.findById(this.projectId, Number(id))
        this.$set(this.exampleNameMap, id, example.filename.replace(/\.[^/.]+$/, ''))
      }
      return this.exampleNameMap[id]
    },
    async loadExampleNames(items: Percentage) {
      const exampleNames = Object.keys(items);
      await Promise.all(exampleNames.map(this.resolveExampleName));
    }
  }
})
</script>

<style scoped>
.container {
  padding-left: 20px;
  padding-right: 20px;
  margin-top: 10px;
}
</style>