<template>
  <v-card>
    <v-alert v-if="successMessage" type="success" dismissible @click="successMessage = ''">
      {{ successMessage }}
    </v-alert>
    <v-alert v-if="errorMessage" type="error" dismissible @click="errorMessage = ''">
      {{ errorMessage }}
    </v-alert>
    <template v-if="isAnswered">
      <v-card-title>Perspectiva pessoal já definida</v-card-title>
    </template>
    <template v-else>
      <template v-if="isAdmin">
        <v-card-title>
          <v-btn
            v-if="!hasPerspective"
            color="primary"
            class="text-capitalize"
            @click="$router.push('perspectives/add')"
          >
            Create
          </v-btn>
        </v-card-title>
        <perspective-list :items="items" :is-loading="isLoading" :value="[]" />
      </template>
      <template v-else>
        <!-- O componente form-answer deverá interpretar as perguntas e renderizar as opções de escolha múltipla -->
        <form-answer
          :questions-list="questionsList"
          :options-list="optionsList"
          @submit-answers="submitAnswers"
        />
      </template>
    </template>
  </v-card>
</template>

<script lang="ts">
import Vue from 'vue'
import { mapGetters } from 'vuex'
import PerspectiveList from '@/components/perspective/PerspectiveList.vue'
import FormAnswer from '~/components/perspective/FormAnswer.vue'
import { MemberItem } from '~/domain/models/member/member'
import { PerspectiveDTO } from '~/services/application/perspective/perspectiveData'
import { OptionsQuestionItem, QuestionItem } from '~/domain/models/perspective/question/question'
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
      optionsList: [] as OptionsQuestionItem[], // Lista de perguntas para o FormAnswer
      answersList: [] as AnswerItem[],
      // Mapa de escolha múltipla onde a chave é o question id
      multipleChoiceMap: {} as { [questionId: number]: boolean },
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
      } finally {
        this.isLoading = false
      }
    },

    async fetchAnswers() {
      this.isLoading = true
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
      } finally {
        this.isLoading = false
      }
    },

    async fetchQuestions() {
      this.isLoading = true
      try {
        // Obtém a perspectiva (assumindo que há apenas uma)
        const perspectives = await this.$services.perspective.list(this.projectId)
        const perspectiveId = perspectives.id
        const questions = await this.$services.question.list(perspectiveId, this.projectId)
        this.questionsList = questions.filter(
          (question) => question.perspective_id === perspectiveId
        )
        this.questionsList = questions

        // Cria um mapa onde a chave é o question id
        // e o valor é true se options_group estiver preenchido
        this.multipleChoiceMap = {}
        let index = 0
        for (const q of questions) {
          this.multipleChoiceMap[index] = q.options_group !== null && q.options_group !== undefined
          if (this.multipleChoiceMap[index]) {
            if (q.options_group !== undefined && q.options_group !== null) {
              const options = await this.$services.optionsQuestion.list(this.projectId)
              this.optionsList = options
            }
          }
          index++
        }
      } catch (error) {
        console.error('Erro ao buscar perguntas:', error)
      } finally {
        this.isLoading = false
      }
    },

    async submitAnswers(
      formattedAnswers: { questionId: number; answer: string; answerType: string }[]
    ) {
      console.log('Respostas submetidas:', formattedAnswers)
      try {
        // Mapeia as respostas com base no multipleChoiceMap, usando o question id como chave
        let index = 0
        const answersToSubmit: CreateAnswerCommand[] = formattedAnswers.map((formattedAnswer) => {
          const isMultipleChoice = this.multipleChoiceMap[index] || false
          index++
          if (isMultipleChoice) {
            return {
              member: this.myRole?.id || 0,
              question: formattedAnswer.questionId,
              answer_option: formattedAnswer.answer // Para escolha múltipla
            }
          } else {
            return {
              member: this.myRole?.id || 0,
              question: formattedAnswer.questionId,
              answer_text: formattedAnswer.answer // Para perguntas normais
            }
          }
        })

        for (const answer of answersToSubmit) {
          await this.$services.answer.create(this.projectId, answer)
        }
        this.successMessage = 'Answers successfully submitted!'
        setTimeout(() => {
          this.successMessage = ''
          this.submitted = true
          this.$router.push(`/projects/${this.projectId}/perspectives`)
        }, 7000)
        window.location.reload()
      } catch (error: any) {
        console.error('Erro ao submeter respostas:', error)
        if (error.response && error.response.status === 400) {
          const errors = error.response.data
          if (errors.answer_text) {
            this.errorMessage = errors.answer_text[0]
          } else {
            this.errorMessage = JSON.stringify(errors)
          }
        } else if (error.response && error.response.status === 500) {
          this.errorMessage = 'Database is slow or unavailable. Please try again later.'
        } else {
          this.errorMessage = 'Database is slow or unavailable. Please try again later.'
        }
      }
    }
  }
})
</script>

<style scoped>
::v-deep .v-dialog {
  width: 800px;
}
</style>
