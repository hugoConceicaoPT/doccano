<template>
  <div class="perspectives-page">
    <!-- Conteúdo principal -->
    <v-container fluid class="pa-0">
      <!-- Perspectiva já respondida -->
      <v-card v-if="isAnswered" elevation="2" class="ma-4">
        <v-card-title class="success white--text">
          <v-icon left color="white" size="28">mdi-check-circle</v-icon>
          <span class="text-h6">Perspectiva Pessoal Definida</span>
        </v-card-title>
        <v-card-text class="text-center pa-6">
          <v-icon size="80" color="success" class="mb-4">mdi-clipboard-check-outline</v-icon>
          <h2 class="text-h6 mb-3">Suas respostas foram registadas com sucesso!</h2>
          <p class="text-body-1 grey--text">
            Obrigado por definir a sua perspectiva pessoal. As suas respostas foram guardadas 
            e serão utilizadas para análise do projeto.
          </p>
        </v-card-text>
      </v-card>

      <!-- Conteúdo para não respondidas -->
      <div v-else>
        <!-- Alertas de sucesso e erro -->
        <v-alert 
          v-if="successMessage" 
          type="success" 
          dismissible 
          prominent
          border="left"
          elevation="1"
          class="ma-4"
          @input="successMessage = ''"
        >
          <v-icon slot="prepend" color="success">mdi-check-circle</v-icon>
          {{ successMessage }}
        </v-alert>
        
        <v-alert 
          v-if="errorMessage" 
          type="error" 
          dismissible 
          prominent
          border="left"
          elevation="1"
          class="ma-4"
          @input="errorMessage = ''"
        >
          <v-icon slot="prepend" color="error">mdi-alert-circle</v-icon>
          {{ errorMessage }}
        </v-alert>

        <!-- Vista do Administrador -->
        <v-card v-if="isAdmin" elevation="2" class="ma-4">
          <v-card-title class="primary white--text">
            <v-icon left color="white">mdi-cog</v-icon>
            Gestão de Perspectivas
            <v-spacer />
            <v-btn
              v-if="!hasPerspective"
              color="white"
              outlined
              class="text-capitalize"
              @click="$router.push('perspectives/add')"
            >
              <v-icon left>mdi-plus</v-icon>
              Criar Perspectiva
            </v-btn>
          </v-card-title>
          
          <v-card-text v-if="!hasPerspective" class="text-center pa-6">
            <v-icon size="80" color="grey lighten-1" class="mb-4">mdi-clipboard-text-outline</v-icon>
            <h2 class="text-h6 mb-3 grey--text">Nenhuma perspectiva configurada</h2>
            <p class="text-body-1 grey--text mb-4">
              Para começar a recolher perspectivas dos anotadores, é necessário criar primeiro uma perspectiva para este projeto.
            </p>
            <v-btn
              color="primary"
              elevation="1"
              @click="$router.push('perspectives/add')"
            >
              <v-icon left>mdi-plus-circle</v-icon>
              Criar Primeira Perspectiva
            </v-btn>
          </v-card-text>
          
          <v-card-text v-else class="pa-4">
            <perspective-list :items="items" :is-loading="isLoading" :value="[]" />
          </v-card-text>
        </v-card>

        <!-- Vista do Utilizador -->
        <div v-else>
          <!-- Loading State -->
          <v-card v-if="isLoading" elevation="1" class="ma-4">
            <v-card-text class="text-center pa-6">
              <v-progress-circular 
                indeterminate 
                color="primary" 
                size="48" 
                width="3"
                class="mb-4"
              />
              <p class="text-h6 mb-2">A carregar perspectiva...</p>
              <p class="grey--text">Por favor aguarde enquanto carregamos as questões.</p>
            </v-card-text>
          </v-card>

          <!-- Formulário de respostas -->
          <div v-else-if="questionsList.length > 0">
            <form-answer
              :questions-list="questionsList"
              @submit-answers="submitAnswers"
            />
          </div>

          <!-- Nenhuma perspectiva encontrada -->
          <v-card v-else elevation="1" class="ma-4">
            <v-card-text class="text-center pa-6">
              <v-icon size="80" color="orange" class="mb-4">mdi-clipboard-search-outline</v-icon>
              <h2 class="text-h6 mb-3">Nenhuma perspectiva disponível</h2>
              <p class="text-body-1 grey--text">
                Ainda não foi configurada uma perspectiva para este projeto. 
                Entre em contacto com o administrador do projeto para mais informações.
              </p>
            </v-card-text>
          </v-card>
        </div>
      </div>
    </v-container>
  </div>
</template>

<script lang="ts">
import Vue from 'vue'
import { mapGetters } from 'vuex'
import PerspectiveList from '@/components/perspective/PerspectiveList.vue'
import FormAnswer from '~/components/perspective/FormAnswer.vue'
import { MemberItem } from '~/domain/models/member/member'
import { PerspectiveDTO } from '~/services/application/perspective/perspectiveData'
import { QuestionItem } from '~/domain/models/perspective/question/question'
import { AnswerItem } from '~/domain/models/perspective/answer/answer'
import { CreateAnswerCommand } from '~/services/application/perspective/answer/answerCommand'

export default Vue.extend({
  components: {
    PerspectiveList,
    FormAnswer
  },

  layout: 'project',

  middleware: ['check-auth', 'auth', 'setCurrentProject', 'project-closed'],

  data() {
    return {
      items: [] as PerspectiveDTO[],
      isLoading: false,
      myRole: null as MemberItem | null,
      questionsList: [] as QuestionItem[],
      answersList: [] as AnswerItem[],
      AlreadyAnswered: false,
      submitted: false,
      successMessage: '',
      errorMessage: ''
    }
  },

  computed: {
    ...mapGetters('auth', ['isStaff', 'isSuperUser']),
    projectId(): string {
      return this.$route.params.id
    },
    isAdmin(): boolean {
      return this.myRole?.isProjectAdmin ?? false
    },
    isSubmitted(): boolean {
      return this.submitted
    },
    isAnswered(): boolean {
      return this.AlreadyAnswered
    },
    hasPerspective(): boolean {
      return this.items && this.items.length > 0
    }
  },

  async mounted() {
    try {
      const memberRepository = this.$repositories.member
      this.myRole = await memberRepository.fetchMyRole(this.projectId)
      if (this.isAdmin) {
        await this.fetchPerspectives()
      } else {
        await this.fetchQuestions()
        await this.fetchAnswers()
      }
    } catch (error) {
      console.error('Erro ao buscar o papel ou perguntas:', error)
      this.errorMessage = 'Erro ao carregar dados. Tente recarregar a página.'
    }
  },

  methods: {
    async fetchPerspectives() {
      this.isLoading = true
      try {
        const projectId = this.$route.params.id
        const response = await this.$services.perspective.list(projectId)
        if (response) {
          this.items = Array.isArray(response) ? response : [response]
        } else {
          // Não há perspectivas neste projeto, mantém items vazio para mostrar o botão create
          this.items = []
        }
      } catch (error: any) {
        console.error('Erro ao buscar perspectivas:', error)
        this.items = []
        this.errorMessage = 'Erro ao carregar perspectivas.'
      } finally {
        this.isLoading = false
      }
    },

    async fetchAnswers() {
      try {
        const response = await this.$services.answer.list()
        this.AlreadyAnswered = response.some((answer: AnswerItem) => {
          return (
            this.questionsList.some((question) => question.id === answer.question) &&
            answer.member === this.myRole?.id
          )
        })
      } catch (error) {
        console.error('Erro ao buscar respostas:', error)
      }
    },

    async fetchQuestions() {
      this.isLoading = true
      try {
        // Obtém a perspectiva (assumindo que há apenas uma)
        const perspectives = await this.$services.perspective.list(this.projectId)
        if (!perspectives) {
          this.questionsList = []
          return
        }
        
        const perspectiveId = perspectives.id
        const questions = await this.$services.question.list(perspectiveId, this.projectId)
        
        // As questões já vêm filtradas por perspectiva do backend
        this.questionsList = questions
      } catch (error) {
        console.error('Erro ao buscar perguntas:', error)
        this.questionsList = []
        this.errorMessage = 'Erro ao carregar questões.'
      } finally {
        this.isLoading = false
      }
    },

    async submitAnswers(
      formattedAnswers: { questionId: number; answer: string; answerType: string }[]
    ) {
      console.log('Respostas submetidas:', formattedAnswers)
      try {
        // Criar comandos de resposta baseado no answer_type
        const answersToSubmit: CreateAnswerCommand[] = formattedAnswers.map((formattedAnswer) => {
          return {
            member: this.myRole?.id || 0,
            question: formattedAnswer.questionId,
            answer_text: formattedAnswer.answer // Tudo é armazenado como text no backend
          }
        })

        for (const answer of answersToSubmit) {
          await this.$services.answer.create(this.projectId, answer)
        }
        
        // Atualizar o status para mostrar que já foi respondido
        this.AlreadyAnswered = true
        
        // Scroll para o topo para mostrar a mensagem
        window.scrollTo({ top: 0, behavior: 'smooth' })
        
      } catch (error: any) {
        console.error('Erro ao submeter respostas:', error)
        if (error.response && error.response.status === 400) {
          const errors = error.response.data
          if (errors.answer_text) {
            this.errorMessage = errors.answer_text[0]
          } else {
            this.errorMessage = 'Dados inválidos. Verifique as suas respostas e tente novamente.'
          }
        } else if (error.response && error.response.status === 500) {
          this.errorMessage = 'Erro interno do servidor. Tente novamente mais tarde.'
        } else {
          this.errorMessage = 'Erro ao submeter respostas. Verifique a sua ligação à internet.'
        }
      }
    }
  }
})
</script>

<style scoped>
.perspectives-page {
  min-height: 100vh;
  background-color: #f5f5f5;
}

.success-card .v-card-title.success {
  background-color: #4caf50;
}

.v-card {
  border-radius: 8px !important;
}

.v-card-title.primary {
  background-color: #1976d2;
}

/* Alertas customizados */
.v-alert {
  border-radius: 8px !important;
}

.v-alert.v-alert--prominent {
  box-shadow: 0 2px 8px rgba(0,0,0,0.1) !important;
}

/* Responsividade */
@media (max-width: 960px) {
  .perspectives-page {
    background-color: #f8f9fa;
  }
  
  .v-container {
    padding: 0 8px !important;
  }
  
  .ma-4 {
    margin: 16px 8px !important;
  }
}
</style>
