<template>
  <div class="container">
    <v-card class="mb-4 pa-4">
      <v-card-title class="text-h6 font-weight-medium">
        <v-icon left class="mr-2">{{ mdiFilterVariant }}</v-icon>
        Filters
      </v-card-title>
      <v-card-text>
        <v-row>
          <v-col cols="12" md="6">
            <div class="d-flex">
              <v-select
                v-model="selectedQuestion"
                :items="availableQuestions"
                label="Question"
                clearable
                outlined
                dense
                hide-details
                class="mb-4 mr-2"
                :prepend-inner-icon="mdiHelpCircleOutline"
                multiple
              >
                <template #label>
                  Question
                </template>
              </v-select>
              <v-select
                v-model="selectedQuestionType"
                :items="questionTypes"
                label="Question Type"
                clearable
                outlined
                dense
                hide-details
                class="mb-4"
                :prepend-inner-icon="mdiFormatListBulletedType"
                multiple
              >
                <template #label>
                  Question Type
                </template>
              </v-select>
            </div>
          </v-col>
          <v-col cols="12" md="6">
            <div class="d-flex">
              <v-select
                v-model="selectedUser"
                :items="availableUsers"
                label="User"
                clearable
                outlined
                dense
                hide-details
                class="mb-4 mr-2"
                :prepend-inner-icon="mdiAccountOutline"
                multiple
              >
                <template #label>
                  Annotator
                </template>
              </v-select>
              <v-select
                v-model="selectedAnswer"
                :items="availableAnswers"
                label="Answer"
                clearable
                outlined
                dense
                hide-details
                class="mb-4"
                :prepend-inner-icon="mdiCommentTextOutline"
                multiple
              >
                <template #label>
                  Answer
                </template>
              </v-select>
            </div>
          </v-col>
        </v-row>
      </v-card-text>
    </v-card>

    <v-card>
      <v-card-title class="d-flex align-center">
        <span class="text-h6 font-weight-medium">
          Perspectives
        </span>
        <v-spacer></v-spacer>
        <v-text-field
          v-model="search"
          :label="$t('generic.search')"
          single-line
          hide-details
          filled
          dense
          class="ml-4"
          style="max-width: 300px"
        />
      </v-card-title>
      <v-data-table
        :items="processedItems"
        :headers="headers"
        :loading="isLoading"
        :loading-text="$t('generic.loading')"
        :no-data-text="$t('vuetify.noDataAvailable')"
        :footer-props="{
          showFirstLastPage: true,
          'items-per-page-text': $t('vuetify.itemsPerPageText'),
          'page-text': $t('dataset.pageText')
        }"
        item-key="id"
        show-select
        @input="$emit('input', $event)"
      >
        <!-- Oculta o checkbox do header -->
        <template #[`header.data-table-select`]>
          <!-- slot vazio -->
        </template>
        <template #[`item.memberName`]="{ item }">
          <div>{{ item.memberName }}</div>
        </template>
        <template #[`item.question`]="{ item }">
          <div>{{ item.question }}</div>
        </template>
        <template #[`item.questionType`]="{ item }">
          <v-chip
            small
            :color="getQuestionTypeColor(item.questionType)"
            text-color="white"
          >
            {{ item.questionType }}
          </v-chip>
        </template>
        <template #[`item.answer`]="{ item }">
          <div>{{ item.answer }}</div>
        </template>
      </v-data-table>
    </v-card>
  </div>
</template>

<script lang="ts">
import Vue from 'vue'
import {
  mdiMagnify,
  mdiHelpCircleOutline,
  mdiFormatListBulletedType,
  mdiAccountOutline,
  mdiCommentTextOutline,
  mdiFilterVariant
} from '@mdi/js'
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
    // Os itens (perspectivas) devem já vir filtrados ou possuir um atributo project_id
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
      mdiMagnify,
      mdiHelpCircleOutline,
      mdiFormatListBulletedType,
      mdiAccountOutline,
      mdiCommentTextOutline,
      mdiFilterVariant,
      // Selecção dos filtros: pergunta, utilizador e resposta
      selectedQuestion: [] as string[],
      selectedUser: [] as string[],
      selectedAnswer: [] as string[],
      selectedQuestionType: [] as string[],
      // Armazena os nomes carregados para os IDs de 0 a 100
      memberNames: {} as { [key: number]: string }
    }
  },

  computed: {
    // Header com três colunas: Criador, Pergunta e Resposta
    headers() {
      return [
        { text: this.$t('Created by'), value: 'memberName', sortable: true },
        { text: this.$t('Question'), value: 'question', sortable: true },
        { text: this.$t('Question Type'), value: 'questionType', sortable: true },
        { text: this.$t('Answer'), value: 'answer', sortable: true }
      ]
    },
    projectId(): string {
      return this.$route.params.id
    },
    // Extrai as perguntas disponíveis
    availableQuestions() {

      const questionsSet = new Set<string>()
      const projectItems = this.items.filter(
        (item) => Number(item.project_id) === Number(this.projectId)
      )
      projectItems.forEach((item) => {
        if (Array.isArray(item.questions)) {
          item.questions.forEach((q) => {
            if (q.question) {
              questionsSet.add(q.question)
            }
          })
        }
      })
      return Array.from(questionsSet)
    },
    // Extrai os utilizadores disponíveis a partir das respostas
    availableUsers() {
      const usersSet = new Set<string>()
      const projectItems = this.items.filter(
        (item) => Number(item.project_id) === Number(this.projectId)
      )
      projectItems.forEach((item) => {
        if (Array.isArray(item.questions)) {
          item.questions.forEach((q) => {
            if (Array.isArray(q.answers)) {
              q.answers.forEach((a: any) => {
                let memberName = ''
                if (a.member) {
                  if (typeof a.member === 'object' && a.member.name) {
                    memberName = a.member.name
                  } else if (typeof a.member === 'number') {
                    memberName = this.memberNames[a.member] || a.member.toString()
                  }
                  if (memberName) {
                    usersSet.add(memberName)
                  }
                }
              })
            }
          })
        }
      })
      return Array.from(usersSet)
    },
    // Extrai as respostas disponíveis
    availableAnswers() {
      const answersSet = new Set<string>()
      const projectItems = this.items.filter(
        (item) => Number(item.project_id) === Number(this.projectId)
      )
      projectItems.forEach((item) => {
        if (Array.isArray(item.questions)) {
          item.questions.forEach((q) => {
            if (Array.isArray(q.answers)) {
              q.answers.forEach((a: any) => {
                const answerText = a.answer_text || a.answer_option || ''
                if (answerText) {
                  answersSet.add(answerText)
                }
              })
            }
          })
        }
      })
      return Array.from(answersSet)
    },
    questionTypes() {
      return [
        { text: 'Text', value: 'string' },
        { text: 'Integer', value: 'int' },
        { text: 'True/False', value: 'boolean' }
      ]
    },
    // Processa os itens gerando uma linha para cada resposta e aplicando os filtros selecionados
    processedItems() {
      const result: Array<{ id: number; memberName: string; question: string; questionType: string; answer: string }> = []
      const projectItems = this.items.filter(
        (item) => Number(item.project_id) === Number(this.projectId)
      )
      let counter = 0
      projectItems.forEach((item) => {
        if (Array.isArray(item.questions)) {
          item.questions.forEach((q) => {
            // Filtra pela pergunta, se houver seleções
            if (
              this.selectedQuestion.length > 0 &&
              q.question &&
              !this.selectedQuestion.includes(q.question)
            ) {
              return
            }
            // Filtra pelo tipo de pergunta, se houver seleções
            if (
              this.selectedQuestionType.length > 0 &&
              q.answer_type &&
              !this.selectedQuestionType.includes(q.answer_type)
            ) {
              return
            }
            if (Array.isArray(q.answers)) {
              q.answers.forEach((a: any) => {
                let memberId: number
                let memberName = ''
                if (a.member) {
                  if (typeof a.member === 'object' && a.member.id != null) {
                    memberId = a.member.id
                    memberName = a.member.name || memberId.toString()
                  } else if (typeof a.member === 'number') {
                    memberId = a.member
                    memberName = this.memberNames[memberId] || memberId.toString()
                  }
                }
                const answerText = a.answer_text || a.answer_option
                // Cria um registro para cada resposta
                const row = {
                  id: counter++,
                  memberName,
                  question: q.question,
                  questionType: this.translateQuestionType(q.answer_type || ''),
                  answer: answerText
                }
                // Filtro de busca (buscando em todas as colunas)
                if (this.search) {
                  const searchLower = this.search.toLowerCase()
                  const combinedText =
                    `${row.memberName} ${row.question} ${row.questionType} ${row.answer}`.toLowerCase()
                  if (!combinedText.includes(searchLower)) {
                    return
                  }
                }
                // Filtro por utilizador, se houver seleções
                if (this.selectedUser.length > 0 && !this.selectedUser.includes(row.memberName)) {
                  return
                }
                // Filtro por resposta, se houver seleções
                if (this.selectedAnswer.length > 0 && !this.selectedAnswer.includes(row.answer)) {
                  return
                }
                result.push(row)
              })
            }
          })
        }
      })
      return result
    }
  },

  watch: {
    // Quando os itens mudam, recarrega os nomes dos membros
    items: {
      handler() {
        this.$nextTick(() => {
          this.loadMemberNames()
        })
      },
      deep: true,
      immediate: true
    }
  },

  mounted() {
    this.$nextTick(() => {
      this.loadMemberNames()
    })
  },

  methods: {
    // Exemplo de método para carregar os nomes dos membros (supondo um repositório para membros)
    loadMemberNames() {
      // Garante que a estrutura de nomes de membros está vazia/inicializada
      this.memberNames = {}

      // Itera por todos os items
      this.items.forEach((item) => {
        // Itera por todos os member IDs do item
        item.members.forEach((memberId) => {
          // Verifica se ainda não carregou esse membro
          if (!this.memberNames[memberId]) {
            this.$repositories.member
              .findById(this.projectId, memberId)
              .then((response: any) => {
                this.$set(this.memberNames, memberId, response.username)
              })
              .catch(() => {
                console.log(`Member not found for ID ${memberId}`)
              })
          }
        })
      })
    },
    translateQuestionType(type: string): string {
      switch (type) {
        case 'string':
          return 'Text'
        case 'int':
          return 'Integer'
        case 'boolean':
          return 'True/False'
        default:
          return type
      }
    },
    getQuestionTypeColor(type: string): string {
      switch (type) {
        case 'Text':
          return 'primary'
        case 'Integer':
          return 'success'
        case 'True/False':
          return 'warning'
        default:
          return 'grey'
      }
    }
  }
})
</script>

<style scoped>
.container {
  padding: 16px;
}

::v-deep .v-data-table {
  border-radius: 4px;
}

::v-deep .v-data-table-header th {
  font-weight: 600 !important;
  white-space: nowrap;
}

::v-deep .v-select__selections {
  padding-top: 4px;
}
</style>
