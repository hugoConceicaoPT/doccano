



<template>
  <div class="container">
    <!-- Seleção da pergunta -->
    <v-select
      v-model="selectedQuestion"
      :items="availableQuestions"
      label="Selecione a pergunta"
      clearable
      class="mb-4"
    />
    <!-- Seleção do utilizador -->
    <v-select
      v-model="selectedUser"
      :items="availableUsers"
      label="Selecione o utilizador"
      clearable
      class="mb-4"
    />
    <!-- Seleção da resposta -->
    <v-select
      v-model="selectedAnswer"
      :items="availableAnswers"
      label="Selecione a resposta"
      clearable
      class="mb-4"
    />
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
      <template #top>
        <v-text-field
          v-model="search"
          :prepend-inner-icon="mdiMagnify"
          :label="$t('generic.search')"
          single-line
          hide-details
          filled
        />
      </template>
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
      <template #[`item.answer`]="{ item }">
        <div>{{ item.answer }}</div>
      </template>
    </v-data-table>
  </div>
</template>

<script lang="ts">
import Vue from 'vue'
import { mdiMagnify } from '@mdi/js'
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
      // Selecção dos filtros: pergunta, utilizador e resposta
      selectedQuestion: 'Todas as perguntas' as string | null,
      selectedUser: 'Todos os utilizadores' as string | null,
      selectedAnswer: 'Todas as respostas' as string | null,
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
        { text: this.$t('Answer'), value: 'answer', sortable: true }
      ]
    },
    projectId(): string {
      return this.$route.params.id
    },
    // Extrai as perguntas disponíveis e adiciona a opção "Todas as perguntas"
    availableQuestions() {
      const questionsSet = new Set<string>()
      const projectItems = this.items.filter(
        item => Number(item.project_id) === Number(this.projectId)
      )
      projectItems.forEach(item => {
        if (Array.isArray(item.questions)) {
          item.questions.forEach(q => {
            if (q.question) {
              questionsSet.add(q.question)
            }
          })
        }
      })
      return ['Todas as perguntas', ...Array.from(questionsSet)]
    },
    // Extrai os utilizadores disponíveis a partir das respostas e adiciona "Todos os utilizadores"
    availableUsers() {
      const usersSet = new Set<string>()
      const projectItems = this.items.filter(
        item => Number(item.project_id) === Number(this.projectId)
      )
      projectItems.forEach(item => {
        if (Array.isArray(item.questions)) {
          item.questions.forEach(q => {
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
      return ['Todos os utilizadores', ...Array.from(usersSet)]
    },
    // Extrai as respostas disponíveis e adiciona "Todas as respostas"
    availableAnswers() {
      const answersSet = new Set<string>()
      const projectItems = this.items.filter(
        item => Number(item.project_id) === Number(this.projectId)
      )
      projectItems.forEach(item => {
        if (Array.isArray(item.questions)) {
          item.questions.forEach(q => {
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
      return ['Todas as respostas', ...Array.from(answersSet)]
    },
    // Processa os itens gerando uma linha para cada resposta e aplicando os filtros selecionados
    processedItems() {
      const result: Array<{ id: number; memberName: string; question: string; answer: string }> = []
      const projectItems = this.items.filter(
        item => Number(item.project_id) === Number(this.projectId)
      )
      let counter = 0
      projectItems.forEach(item => {
        if (Array.isArray(item.questions)) {
          item.questions.forEach(q => {
            // Filtra pela pergunta, se selecionada e não for "Todas as perguntas"
            if (this.selectedQuestion && this.selectedQuestion !== 'Todas as perguntas' && 
                q.question && q.question.toLowerCase() !== this.selectedQuestion.toLowerCase()) {
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
                const answerText = a.answer_text || a.answer_option || ''
                // Cria um registro para cada resposta
                const row = {
                  id: counter++,
                  memberName,
                  question: q.question,
                  answer: answerText
                }
                // Filtro de busca (buscando em todas as colunas)
                if (this.search) {
                  const searchLower = this.search.toLowerCase()
                  const combinedText = `${row.memberName} ${row.question} ${row.answer}`.toLowerCase()
                  if (!combinedText.includes(searchLower)) {
                    return
                  }
                }
                // Filtro por utilizador, se selecionado
                if (this.selectedUser && this.selectedUser !== 'Todos os utilizadores' &&
                    row.memberName.toLowerCase() !== this.selectedUser.toLowerCase()) {
                  return
                }
                // Filtro por resposta, se selecionada
                if (this.selectedAnswer && this.selectedAnswer !== 'Todas as respostas' &&
                    row.answer.toLowerCase() !== this.selectedAnswer.toLowerCase()) {
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
    selectedQuestion(newVal) {
      console.log('selectedQuestion changed:', newVal)
    },
    selectedUser(newVal) {
      console.log('selectedUser changed:', newVal)
    },
    selectedAnswer(newVal) {
      console.log('selectedAnswer changed:', newVal)
    },
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
      for (let memberId = 0; memberId <= 100; memberId++) {
        this.$repositories.member.findById(this.projectId, memberId)
          .then((response: any) => {
            this.$set(this.memberNames, memberId, response.username)
            console.log(`Fetched member ${memberId}:`, response.username)
          })
          .catch(() => {
            console.log(`Member not found for ID ${memberId}`)
          })
      }
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