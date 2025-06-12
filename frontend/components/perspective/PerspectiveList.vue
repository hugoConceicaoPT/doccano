<template>
  <div class="container">
    <!-- Seleção da pergunta -->
    <v-select v-model="selectedQuestion" :items="availableQuestions" label="Selecione a pergunta" clearable
      class="mb-4" multiple/>
    <!-- Seleção do utilizador -->
    <v-select v-model="selectedUser" :items="availableUsers" label="Selecione o utilizador" clearable class="mb-4" multiple/>
    <!-- Seleção da resposta -->
    <v-select v-model="selectedAnswer" :items="availableAnswers" label="Selecione a resposta" clearable class="mb-4" multiple/>
    <v-data-table :items="processedItems" :headers="headers" :loading="isLoading" :loading-text="$t('generic.loading')"
      :no-data-text="$t('vuetify.noDataAvailable')" :footer-props="{
        showFirstLastPage: true,
        'items-per-page-text': $t('vuetify.itemsPerPageText'),
        'page-text': $t('dataset.pageText')
      }" item-key="id" show-select @input="$emit('input', $event)">
      <template #top>
        <v-text-field v-model="search" :prepend-inner-icon="mdiMagnify" :label="$t('generic.search')" single-line
          hide-details filled />
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
      selectedQuestion: [] as string[],
      selectedUser: [] as string[],
      selectedAnswer: [] as string[],
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
    // Extrai as perguntas disponíveis
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
      return Array.from(questionsSet)
    },
    // Extrai os utilizadores disponíveis a partir das respostas
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
      return Array.from(usersSet)
    },
    // Extrai as respostas disponíveis
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
      return Array.from(answersSet)
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
            // Filtra pela pergunta, se houver seleções
            if (this.selectedQuestion.length > 0 && 
                q.question && 
                !this.selectedQuestion.includes(q.question)) {
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
                // Filtro por utilizador, se houver seleções
                if (this.selectedUser.length > 0 && 
                    !this.selectedUser.includes(row.memberName)) {
                  return
                }
                // Filtro por resposta, se houver seleções
                if (this.selectedAnswer.length > 0 && 
                    !this.selectedAnswer.includes(row.answer)) {
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
      this.items.forEach(item => {
        // Itera por todos os member IDs do item
        item.members.forEach(memberId => {
          // Verifica se ainda não carregou esse membro
          if (!this.memberNames[memberId]) {
            this.$repositories.member.findById(this.projectId, memberId)
              .then((response: any) => {
                this.$set(this.memberNames, memberId, response.username)
              })
              .catch(() => {
                console.log(`Member not found for ID ${memberId}`)
              })
          }
        })
      })
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