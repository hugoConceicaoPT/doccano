<template>
  <div>
    <v-dialog v-model="showWarningDialog" persistent max-width="500">
      <v-card>
        <v-card-title class="headline">Attention</v-card-title>
        <v-card-text>
          If you proceed, the project will be closed and you will no longer be able to annotate, import datasets, etc. Do you wish to continue?
        </v-card-text>
        <v-card-actions>
          <v-spacer></v-spacer>
          <v-btn color="primary" text @click="onProceed">Proceed</v-btn>
          <v-btn color="secondary" text @click="onCancel">Cancel</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
    <v-col cols="12" class="ms-1" md="4">
      <v-select v-model="selectedExample" :items="exampleOptions" label="Selecione a anotação" dense outlined clearable
        hide-details placeholder="Select" />
    </v-col>
    <v-row>
      <v-col cols="12" class="ms-4 mb-4" md="4">
        <v-select v-model="selectedPerspectiveQuestion" :items="perspectiveQuestions" label="Perspective Question" dense outlined
          hide-details placeholder="Select a question" />
      </v-col>

      <v-col v-if="selectedPerspectiveQuestion" cols="12" md="4">
        <v-select v-model="selectedPerspectiveAnswer" :items="possibleAnswers" label="Perspective Answer" dense outlined
          multiple hide-details placeholder="Select a answer(s)" />
      </v-col>
    </v-row>
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

      <template #[`item.labelValue`]="{ item }">
        <div v-html="item.labelsValue.replace(/\n/g, '<br>')"></div>
      </template>

      <template #[`item.discrepancyBool`]="{ item }">
        <v-chip :color="item.discrepancyBool === 'Yes' ? 'error' : 'success'" dark>
          {{ item.discrepancyBool }}
        </v-chip>
      </template>
    </v-data-table>
  </div>
</template>

<script lang="ts">
import Vue from 'vue'
import { mdiMagnify, mdiPencil } from '@mdi/js'
import type { PropType } from 'vue'
import { Percentage } from '~/domain/models/metrics/metrics'
import { Distribution } from '~/domain/models/statistics/statistics'
import { ExampleDTO } from '~/services/application/example/exampleData'

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
      selectedExample: 'Todas as anotações',
      exampleNameMap: {} as Record<string, string>,
      isReady: false,
      selectedPerspectiveQuestion: '',
      selectedPerspectiveAnswer: '',
      perspectiveDistribution: {} as Distribution,
      example: {} as ExampleDTO,
      showWarningDialog: false,
    }
  },

  computed: {
    perspectiveQuestions(): Array<{ text: string, value: string }> {
      return Object.entries(this.perspectiveDistribution).map(([id, q]) => ({
        text: q.question,
        value: id
      }))
    },

    possibleAnswers(): string[] {
      const entry = this.perspectiveDistribution[this.selectedPerspectiveQuestion];
      return entry ? Object.keys(entry.answers) : [];
    },
    // Header com três colunas: Criador, Pergunta e Resposta
    headers() {
      return [
        { text: 'Example', value: 'exampleName', sortable: true },
        { text: 'Has Discrepancy', value: 'discrepancyBool', sortable: false },
        { text: 'Label', value: 'labelValue', sortable: true }
      ]
    },
    projectId(): string {
      return this.$route.params.id
    },
    flatItems(): Array<{
      exampleName: string;
      labelsValue: string;
      discrepancyBool: string;
    }> {
      const rows = [];

      const source = this.filteredItems;
      for (const [exampleName, labels] of Object.entries(source)) {
        console.log(this.discrepancyThreshold)
        const notHasDiscrepancy = Object.values(labels).some(
          (percentage) => percentage > this.discrepancyThreshold
        )

        const labelsValue = Object.entries(labels)
          .filter(([label]) => this.matchesSearch(label))
          .map(([label, percent]) => `${label}: ${percent}%`)
          .join('\n');

        if (labelsValue) {
          rows.push({
            exampleName,
            labelsValue,
            discrepancyBool: notHasDiscrepancy ? 'No' : 'Yes'
          });
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
      console.log(this.items)
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
    },
    onProceed() {
      localStorage.setItem(`project_closed_${this.projectId}`, 'true');
      this.showWarningDialog = false;
    },
    onCancel() {
      this.showWarningDialog = false;
      this.$router.push(this.localePath(`/projects/${this.projectId}`));
    },
  },
  async created() {
    try {
      this.perspectiveDistribution = await this.$repositories.statistics.fetchPerspectiveAnswerDistribution(this.projectId)
    }
    catch (error) {
      console.error(error)
    }
  },
  mounted() {
    this.showWarningDialog = localStorage.getItem(`project_closed_${this.projectId}`) !== 'true';
  },
})
</script>

<style scoped>
.container {
  padding-left: 20px;
  padding-right: 20px;
  margin-top: 10px;
}
</style>