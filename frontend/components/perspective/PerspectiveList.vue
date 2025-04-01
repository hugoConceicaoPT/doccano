<template>
  <div class="container">
    <!-- Add question selection at the top -->
    <v-select v-model="selectedQuestion" :items="availableQuestions" label="Selecione a pergunta" clearable
      class="mb-4" />
    <v-data-table :value="value" :headers="headers" :items="filteredItems" :search="search" :loading="isLoading"
      :loading-text="$t('generic.loading')" :no-data-text="$t('vuetify.noDataAvailable')" :footer-props="{
        showFirstLastPage: true,
        'items-per-page-text': $t('vuetify.itemsPerPageText'),
        'page-text': $t('dataset.pageText')
      }" item-key="id" show-select @input="$emit('input', $event)">
      <template #top>
        <v-text-field v-model="search" :prepend-inner-icon="mdiMagnify" :label="$t('generic.search')" single-line
          hide-details filled />
      </template>
      <!-- eslint-disable-next-line vue/valid-v-slot -->
      <template #[`header.data-table-select`]>
        <!-- Hide the header checkbox by providing an empty slot -->
      </template>
      <template #[`item.members`]="{ item }">
        <span>
          {{ getMemberNames(item) }}
        </span>
      </template>
      <template #[`item.responses`]="{ item }">
        <div style="white-space: pre-line;">
          {{ getResponseTexts(item) }}
        </div>
      </template>
    </v-data-table>
  </div>
</template>

<script lang="ts">
import Vue from 'vue'
import { mdiMagnify, mdiPencil } from '@mdi/js'
import type { PropType } from 'vue'
import { PerspectiveDTO } from '~/services/application/perspective/perspectiveData'
export default Vue.extend({
  name: 'PerspectiveList',
  props: {
    isLoading: {
      type: Boolean,
      default: false,
      required: true
    },
    items: {
      type: Array as PropType<PerspectiveDTO[]>,
      default: () => [],
      required: true
    },
    value: {
      type: Array as PropType<PerspectiveDTO[]>,
      default: () => [],
      required: true
    },
    disableEdit: {
      type: Boolean,
      default: false
    },
    members: {
      type: Array as PropType<any[]>,
      default: () => []
    }
  },

  data() {
    return {
      search: '',
      mdiPencil,
      mdiMagnify,
      selectedQuestion: null as string | null
    }
  },

  computed: {
    headers() {
      const headers = [
        { text: this.$t('Created by'), value: 'members', sortable: false },
        { text: this.$t('Answers'), value: 'responses', sortable: false }
      ];
      return headers;
    },
    availableQuestions() {
      const questionsSet = new Set();
      this.items.forEach(item => {
        if (Array.isArray(item.questions)) {
          item.questions.forEach(q => {
            if (q.question) {
              questionsSet.add(q.question);
            }
          });
        }
      });
      return Array.from(questionsSet);
    },
    filteredItems() {
      const selected = this.selectedQuestion;
      console.log('Filtering items with selected question:', selected);
      if (!selected) {
        return this.items;
      }
      const filtered = this.items.filter(item => {
        return Array.isArray(item.questions) && item.questions.some((q: any) => {
          return q.question && q.question.toLowerCase() === selected.toLowerCase();
        });
      });
      console.log('Filtered items:', filtered);
      return filtered;
    }
  },

  watch: {
    selectedQuestion(newVal) {
      console.log('selectedQuestion changed:', newVal);
    }
  },

  methods: {
    getResponseTexts(item: any): string {
      if (!Array.isArray(item.questions) || item.questions.length === 0) {
        return this.$t('No answers') as string;
      }
      // Filter the questions in the item based on the selected question (if any)
      let questionsToUse = item.questions;
      if (this.selectedQuestion) {
        const selected = this.selectedQuestion;
        questionsToUse = item.questions.filter((q: any) => {
          return q.question && q.question.toLowerCase() === selected.toLowerCase();
        });
      }
      const responses: string[] = [];
      questionsToUse.forEach((q: any) => {
        if (Array.isArray(q.answers)) {
          q.answers.forEach((a: any) => {
            const username = (a.member && a.member.name) ? a.member.name + ': ' : '';
            let answerContent = '';
            if (a.answer_text) {
              answerContent = a.answer_text;
            } else if (a.answer_option) {
              answerContent = a.answer_option;
            }
            responses.push(username + answerContent);
          });
        }
      });
      return responses.join('\n') || (this.$t('No answers') as string);
    },
    getMemberNames(item: any): string {
      if (!Array.isArray(item.members) || item.members.length === 0) {
        return this.$t('Unknown') as string;
      }
      return item.members
        .map((id: number) => this.findMemberById(id))
        .filter(Boolean)
        .join(', ');
    },
    findMemberById(id: number | string): string {
      const member = this.members.find((m: any) => Number(m.id) === Number(id));
      return member ? member.name : 'Unknown';
    }
  }
})
</script>

<style scoped>
.container {
  padding-left: 20px;
  /* Adjust spacing as needed */
  padding-right: 20px;
  /* Optional: add right padding for symmetry */
  margin-top: 10px;
  /* Optional: some top margin */
}

/* You can also add additional styles if needed to further improve the layout */
</style>
