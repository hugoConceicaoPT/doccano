<template>
  <v-card class="voting-card">
    <!-- Título da votação -->
    <v-card-title class="d-flex align-center py-4">
      <span class="text-h5 font-weight-medium">
        <v-icon left class="mr-2 primary--text">{{ mdiVote }}</v-icon>
        Annotation Rules Voting
      </span>
      <v-spacer />
      <v-btn color="secondary" outlined @click="$router.push(localePath(`/projects/${projectId}`))">
        <v-icon left>{{ mdiArrowLeft }}</v-icon>
        Back to project
      </v-btn>
    </v-card-title>
    <v-divider></v-divider>

    <v-card-text class="pa-4">
      <v-alert v-if="successMessage" type="success" dismissible class="mb-4">
        {{ successMessage }}
      </v-alert>
      <v-alert v-if="errorMessage" type="error" dismissible class="mb-4">
        {{ errorMessage }}
      </v-alert>

      <div v-if="loading" class="text-center my-8">
        <v-progress-circular indeterminate color="primary" size="64"></v-progress-circular>
        <p class="mt-4 text-h6">Loading rules for voting...</p>
      </div>

      <!-- Informações sobre o período de votação -->
      <v-alert v-if="!loading && activeVotingConfig" :type="votingStatus.type" class="mb-4" :icon="votingStatus.icon">
        <div class="d-flex align-center">
          <div>
            <strong>{{ votingStatus.title }}</strong>
            <div class="text-caption mt-1">{{ votingStatus.message }}</div>
            <div v-if="activeVotingConfig" class="text-caption mt-1">
            </div>
          </div>
        </div>
      </v-alert>

      <!-- Sem votação ativa -->
      <div v-if="!loading && !activeVotingConfig" class="text-center my-8">
        <v-icon size="64" color="grey lighten-1" class="mb-4">{{ mdiVoteOutline }}</v-icon>
        <p class="text-h6 grey--text">There are no active votes at the moment.</p>
        <p class="text-body-2 grey--text">Wait for the administrator to set up a new rule vote.</p>

      </div>

      <!-- Interface de votação -->
      <div v-if="!loading && activeVotingConfig && pendingRules.length > 0 && votingStatus.canVote">
        <!-- Estatísticas da votação -->
        <v-row class="mb-4">
          <v-col cols="12" md="4">
            <v-card outlined>
              <v-card-text class="text-center">
                <v-icon size="32" color="primary" class="mb-2">{{ mdiClipboardList }}</v-icon>
                <div class="text-h6">{{ pendingRules.length }}</div>
                <div class="text-caption">Rules to vote</div>
              </v-card-text>
            </v-card>
          </v-col>
          <v-col cols="12" md="4">
            <v-card outlined>
              <v-card-text class="text-center">
                <v-icon size="32" color="success" class="mb-2">{{ mdiCheckCircle }}</v-icon>
                <div class="text-h6">{{ Object.keys(localVotes).length }}</div>
                <div class="text-caption">Selected votes</div>
              </v-card-text>
            </v-card>
          </v-col>
          <v-col cols="12" md="4">
            <v-card outlined>
              <v-card-text class="text-center">
                <v-icon size="32" color="info" class="mb-2">{{ mdiPercent }}</v-icon>
                <div class="text-h6">{{ Math.round((Object.keys(localVotes).length / pendingRules.length) * 100) }}%
                </div>
                <div class="text-caption">Progress</div>
              </v-card-text>
            </v-card>
          </v-col>
        </v-row>

        <!-- Lista de regras para votação -->
        <v-row class="mb-6">
          <v-col v-for="rule in pendingRules" :key="rule.id" cols="12" sm="6" md="4">
            <v-card outlined class="rule-voting-card mb-4"
              :class="{ 'voted': rule.id in localVotes, 'elevation-4': rule.id in localVotes }">
              <v-card-title class="text-subtitle-1 font-weight-medium d-flex align-center">
                <v-icon left color="primary">{{ mdiGavel }}</v-icon>
                {{ rule.name }}
                <v-spacer />
                <v-chip v-if="rule.id in localVotes" small color="primary" text-color="white">
                  <v-icon small left>{{ localVotes[rule.id] ? mdiThumbUp : mdiThumbDown }}</v-icon>
                  {{ localVotes[rule.id] ? 'Approve' : 'Reject' }}
                </v-chip>
              </v-card-title>

              <v-card-text v-if="!(rule.id in localVotes)" class="pb-2">
                <p class="text-body-2 grey--text mb-0">Select your decision for this rule:</p>
              </v-card-text>

              <v-card-actions class="justify-space-between pa-3">
                <div class="d-flex gap-2">
                  <v-btn small color="success" :outlined="!(rule.id in localVotes && localVotes[rule.id])"
                    :depressed="rule.id in localVotes && localVotes[rule.id]" @click="vote(rule.id, true)">
                    <v-icon left small>{{ mdiThumbUp }}</v-icon>
                    Approve
                  </v-btn>
                  <v-btn small color="error" :outlined="!(rule.id in localVotes && !localVotes[rule.id])"
                    :depressed="rule.id in localVotes && !localVotes[rule.id]" @click="vote(rule.id, false)">
                    <v-icon left small>{{ mdiThumbDown }}</v-icon>
                    Reject
                  </v-btn>
                </div>
                <v-btn v-if="rule.id in localVotes" small color="grey" outlined @click="removeVote(rule.id)">
                  <v-icon small>{{ mdiClose }}</v-icon>
                  Remove
                </v-btn>
              </v-card-actions>
            </v-card>
          </v-col>
        </v-row>

        <!-- Botão de submissão -->
        <v-row>
          <v-col cols="12" class="text-center">
            <v-btn color="primary" :disabled="!canSubmit" class="px-8" large :loading="submitting" @click="submitVotes">
              <v-icon left>{{ mdiSend }}</v-icon>
              Submit All Votes
            </v-btn>
            <div class="mt-3">
              <p class="text-body-2 grey--text mb-1">
                {{ Object.keys(localVotes).length }} of {{ pendingRules.length }} rule(s) voted
              </p>
              <p v-if="!canSubmit && pendingRules.length > 0" class="text-caption error--text mb-0">
                Vote on all rules to submit
              </p>
              <p v-if="canSubmit" class="text-caption success--text mb-0">
                Ready to submit!
              </p>
            </div>
          </v-col>
        </v-row>
      </div>

      <!-- Casos especiais -->
      <div v-else-if="!loading && activeVotingConfig">
        <!-- Já votou em todas as regras -->
        <div v-if="pendingRules.length === 0 && votingStatus.canVote">
          <v-row>
            <v-col cols="12" class="text-center">
              <v-icon size="64" color="success" class="mb-4">{{ mdiCheckCircle }}</v-icon>
              <p class="text-h6 grey--text">You have already voted on all available rules.</p>
            </v-col>
          </v-row>
        </div>

        <!-- Votação não pode ser realizada (expirada ou não iniciada) -->
        <div v-else-if="!votingStatus.canVote">
          <v-row>
            <v-col cols="12" class="text-center">
              <v-icon size="64" :color="votingStatus.type === 'error' ? 'error' : 'warning'" class="mb-4">
                {{ votingStatus.icon }}
              </v-icon>
              <p class="text-h6 grey--text">{{ votingStatus.title }}</p>
              <p class="text-body-1 grey--text">{{ votingStatus.message }}</p>
            </v-col>
          </v-row>
        </div>
      </div>

      <!-- Aviso para não-anotadores -->
      <div v-if="!loading && !isAnnotator" class="text-center my-8">
        <v-icon size="64" color="warning" class="mb-4">{{ mdiInformation }}</v-icon>
        <p class="text-h6 warning--text">No permission to vote</p>
        <p class="text-body-2 grey--text">Only annotators can participate in voting.</p>
      </div>
    </v-card-text>
  </v-card>
</template>

<script lang="ts">
import Vue from 'vue'
import { mapGetters } from 'vuex'
import {
  mdiVote,
  mdiVoteOutline,
  mdiArrowLeft,
  mdiCheckCircle,
  mdiAlertCircle,
  mdiGavel,
  mdiThumbUp,
  mdiThumbDown,
  mdiSend,
  mdiClose,
  mdiClockOutline,
  mdiCalendarClock,
  mdiFileDocumentOutline,
  mdiClipboardList,
  mdiPercent,
  mdiInformation
} from '@mdi/js'

interface AnnotationRuleItem {
  id: number
  name: string
  voting_configuration: number
  is_finalized: boolean
  final_result: string
}

interface VotingAnswer {
  id: number
  project: number
  voting_threshold: number
  percentage_threshold: number
  begin_date: string
  end_date: string
  is_closed: boolean
  version: number
}

export default Vue.extend({

  layout: 'project',
  middleware: ['check-auth', 'auth', 'setCurrentProject'],

  data() {
    return {
      successMessage: '',
      errorMessage: '',
      loading: false,
      submitting: false,
      pendingRules: [] as AnnotationRuleItem[],
      localVotes: {} as Record<number, boolean>,
      activeVotingConfig: {} as VotingAnswer | null,
      currentTime: 0,
      timerId: 0,
      isAnnotator: false,
      mdiVote,
      mdiVoteOutline,
      mdiArrowLeft,
      mdiCheckCircle,
      mdiAlertCircle,
      mdiGavel,
      mdiThumbUp,
      mdiThumbDown,
      mdiSend,
      mdiClose,
      mdiClockOutline,
      mdiCalendarClock,
      mdiFileDocumentOutline,
      mdiClipboardList,
      mdiPercent,
      mdiInformation
    }
  },

  head() {
    return {
      title: 'Voting'
    }
  },

  async fetch() {
    this.loading = true
    try {
      const projectId = this.projectId

      // Verificar se o usuário é anotador
      const member = await this.$repositories.member.fetchMyRole(projectId)
      this.isAnnotator = member.isAnnotator

      if (!this.isAnnotator) {
        this.loading = false
        return
      }

      // Buscar regras não votadas
      const unvotedData = await this.$services.annotationRule.listUnvoted(projectId)
      this.pendingRules = unvotedData.rules as AnnotationRuleItem[]

      // Buscar configurações de votação
      const votingConfigs = await this.$services.votingConfiguration.list(projectId)
      const projectConfigs = votingConfigs.filter(
        (config) => config.project === Number(projectId)
      )

      // Identificar votação ativa
      if (unvotedData.activeVotings.length > 0) {
        const activeVoting = unvotedData.activeVotings.find(v => v.is_active) ||
          unvotedData.activeVotings.find(v => !v.is_expired)
        if (activeVoting) {
          this.activeVotingConfig = projectConfigs.find(c => c.id === activeVoting.id) || null
        }
      }


    } catch (error) {
      this.handleError(error)
    } finally {
      this.loading = false
    }
  },


  computed: {
    ...mapGetters('projects', ['project']),
    projectId() {
      return this.$route.params.id
    },
    canSubmit() {
      return this.pendingRules.length > 0 &&
        this.pendingRules.every(rule => rule.id in this.localVotes)
    },
    votingStatus() {
      if (!this.activeVotingConfig) {
        return {
          type: 'info',
          icon: this.mdiVoteOutline,
          title: 'No active voting',
          message: 'There are no votes available at the moment.',
          canVote: false
        }
      }

      const now = new Date()
      const beginDate = new Date(this.activeVotingConfig.begin_date)
      const endDate = new Date(this.activeVotingConfig.end_date)

      if (now < beginDate) {
        return {
          type: 'warning',
          icon: this.mdiClockOutline,
          title: 'Voting has not started yet',
          message: `Voting will start on ${this.formatDate(beginDate)}`,
          canVote: false
        }
      }

      if (now > endDate) {
        return {
          type: 'error',
          icon: this.mdiCalendarClock,
          title: 'Voting expired',
          message: `Voting ended on ${this.formatDate(endDate)}. Unvoted rules were automatically finalized.`,
          canVote: false
        }
      }

      return {
        type: 'success',
        icon: this.mdiVote,
        title: 'Active voting',
        message: `You can vote until ${this.formatDate(endDate)}`,
        canVote: true
      }
    }
  },

  mounted() {
    this.timerId = window.setInterval(() => {
      this.currentTime = Date.now()
    }, 60000)
  },

  beforeDestroy() {
    window.clearInterval(this.timerId)
  },

  methods: {
    vote(ruleId: number, answer: boolean) {
      this.$set(this.localVotes, ruleId, answer)
    },
    removeVote(ruleId: number) {
      this.$delete(this.localVotes, ruleId)
    },

    async submitVotes() {
      if (!this.canSubmit) return

      this.submitting = true
      try {
        const member = await this.$repositories.member.fetchMyRole(this.projectId)

        for (const [ruleIdStr, answer] of Object.entries(this.localVotes)) {
          const ruleId = Number(ruleIdStr)
          await this.$services.annotationRuleAnswerService.create(this.projectId, {
            annotation_rule: ruleId,
            member: member.id,
            answer
          })
        }

        const votedCount = Object.keys(this.localVotes).length
        this.localVotes = {}

        // Recarregar regras não votadas
        const unvotedData = await this.$services.annotationRule.listUnvoted(this.projectId)
        this.pendingRules = unvotedData.rules as AnnotationRuleItem[]

        if (unvotedData.totalUnvotedRules === 0) {
          this.successMessage = 'You voted on all available rules. Rules that received votes from all annotators have been automatically finalized.'
        } else {
          this.successMessage = `Votes submitted successfully! You voted on ${votedCount} rule(s). ${unvotedData.totalUnvotedRules} rule(s) remaining to vote. Rules that receive votes from all annotators are automatically finalized.`
        }

      } catch (error: any) {
        this.handleVotingError(error)
      } finally {
        this.submitting = false
      }
    },

    handleVotingError(error: any) {
              console.error('Error submitting votes:', error)
      
      // Verificar se é erro de conexão com a base de dados (usando interceptor)
      if (error.isNetworkError || error.isDatabaseError || error.isServerError || error.isTimeoutError) {
        this.errorMessage = error.userMessage
        return
      }

      // Verificar se é erro de conexão sem interceptor (fallback)
      if (!error.response) {
        this.errorMessage = 'Erro de conexão: Não foi possível conectar ao servidor. Verifique sua conexão com a internet e tente novamente.'
        return
      }

      // Verificar se é erro 503 (Service Unavailable - base de dados indisponível)
      if (error.response.status === 503) {
        this.errorMessage = 'Database is slow or unavailable. Please try again later.'
        return
      }

      // Verificar se é erro 500 (erro interno do servidor/base de dados)
      if (error.response.status >= 500) {
        this.errorMessage = 'Error:Database is slow or unavailable. Please try again later.'
        return
      }

      // Tratamento específico de outros erros
      if (error.response?.status === 403) {
        this.errorMessage = 'You do not have permission to vote. Only annotators can vote on annotation rules.'
      } else if (error.response?.status === 400) {
        const detail = error.response.data?.detail
        if (detail?.includes('já votou')) {
          this.errorMessage = 'You have already voted on one or more of these rules. Updating page...'
          setTimeout(() => {
            this.$fetch()
          }, 2000)
        } else if (detail?.includes('votação já foi fechada')) {
          this.errorMessage = 'This vote has already been closed. It is no longer possible to vote.'
        } else if (detail?.includes('regra já foi finalizada')) {
          this.errorMessage = 'One or more rules have already been finalized. It is no longer possible to vote on them.'
        } else if (detail?.includes('ainda não começou')) {
          this.errorMessage = detail
          setTimeout(() => {
            this.$fetch()
          }, 2000)
        } else if (detail?.includes('já expirou')) {
          this.errorMessage = detail
          setTimeout(() => {
            this.$fetch()
          }, 2000)
        } else {
          this.errorMessage = 'Error submitting votes. Please try again.'
        }
      } else {
        this.errorMessage = 'Unexpected error. Check your connection and try again.'
      }
    },

    handleError(error: any) {
      console.error('Erro na aplicação:', error)

      // Verificar se é erro de conexão com a base de dados (usando interceptor)
      if (error.isNetworkError || error.isDatabaseError || error.isServerError || error.isTimeoutError) {
        this.errorMessage = error.userMessage
        return
      }

      // Verificar se é erro de conexão sem interceptor (fallback)
      if (!error.response) {
        this.errorMessage = 'Erro de conexão: Não foi possível conectar ao servidor. Verifique sua conexão com a internet e tente novamente.'
        return
      }

      // Verificar se é erro 503 (Service Unavailable - base de dados indisponível)
      if (error.response.status === 503) {
        this.errorMessage = 'Base de dados indisponível: A base de dados está temporariamente desligada ou sem conexão. Tente novamente em alguns instantes.'
        return
      }

      // Verificar se é erro 500 (erro interno do servidor/base de dados)
      if (error.response.status >= 500) {
        this.errorMessage = ' Database is slow or unavailable. Please try again later.'
        return
      }

      // Tratamento específico de outros erros
      if (error.response && error.response.status === 400) {
        this.errorMessage = 'Error loading data. Some data may be inconsistent.'
      } else if (error.response && error.response.status === 403) {
        this.errorMessage = 'You do not have permission to access this data.'
      } else if (error.response && error.response.status === 404) {
        this.errorMessage = 'Data not found. The project or vote may have been removed.'
      } else {
        this.errorMessage = 'Unexpected error loading data. Check your connection and try again.'
      }
    },

    formatDate(date: Date): string {
      return date.toLocaleString('pt-PT', {
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit'
      })
    }
  }
})
</script>

<style scoped>
.voting-card {
  max-width: 1200px;
  margin: 0 auto;
}

.rule-voting-card {
  transition: all 0.3s ease;
  border: 2px solid transparent;
}

.rule-voting-card.voted {
  border-color: var(--v-primary-base);
  background-color: rgba(var(--v-primary-base), 0.05);
}

.rule-voting-card:hover {
  transform: translateY(-2px);
}

.gap-2>*+* {
  margin-left: 8px;
}
</style>