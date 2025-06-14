<template>
  <v-card class="rules-card">
    <!-- Título apenas para administradores -->
    <div v-if="isAdmin">
      <v-card-title class="d-flex align-center py-4">
        <span class="text-h5 font-weight-medium">
          <v-icon left class="mr-2 primary--text">{{ mdiGavel }}</v-icon>
          Regras de Anotação
        </span>
        <v-spacer />
        <v-btn
          color="primary"
          class="ml-2"
          :disabled="loading || hasActiveVoting"
          @click="goToConfig"
        >
          <v-icon left>{{ mdiCog }}</v-icon>
          Configure Voting
        </v-btn>
      </v-card-title>
      <v-divider></v-divider>
    </div>

    <!-- Título simples para anotadores quando há votação ativa -->
    <div v-if="!isAdmin && activeVotingConfig">
      <v-card-title class="d-flex align-center py-4">
        <span class="text-h5 font-weight-medium">
          <v-icon left class="mr-2 primary--text">{{ mdiVote }}</v-icon>
          Votação nas Regras de Anotação Ativa
        </span>
      </v-card-title>
      <v-divider></v-divider>
    </div>

    <v-card-text class="pa-4">
      <v-alert v-if="successMessage" type="success" dismissible class="mb-4">
        <v-icon left>{{ mdiCheckCircle }}</v-icon>
        {{ successMessage }}
      </v-alert>
      <v-alert v-if="errorMessage" type="error" dismissible class="mb-4">
        <v-icon left>{{ mdiAlertCircle }}</v-icon>
        {{ errorMessage }}
      </v-alert>

      <v-alert v-if="hasActiveVoting && isAdmin" type="info" class="mb-4">
        Existe uma votação ativa (Versão {{ activeVotingConfig?.version }}). Não é possível criar
        uma nova votação até que todas as regras da votação atual estejam finalizadas.
      </v-alert>

      <v-alert v-if="isAdmin && !hasActiveVoting" type="success" class="mb-4">
        Não existe nenhuma votação ativa. Você pode configurar uma nova votação.
      </v-alert>

      <div v-if="loading" class="text-center my-8">
        <v-progress-circular
          indeterminate
          color="primary"
          size="64"
        ></v-progress-circular>
      </div>

      <!-- Botão voltar apenas para administradores -->
      <v-row v-if="!loading && isAdmin" class="mb-4">
        <v-col cols="12">
          <v-btn
            color="secondary"
            outlined
            @click="$router.push(localePath(`/projects/${projectId}`))"
          >
            <v-icon left>{{ mdiHome }}</v-icon>
            Voltar ao projeto
          </v-btn>
        </v-col>
      </v-row>

      <!-- Histórico de regras - apenas para administradores -->
      <div v-if="isAdmin">
        <rule-list v-if="!loading && items.length > 0" :items="items" :is-loading="loading" />

        <div v-if="!loading && items.length === 0" class="text-center my-8">
          <v-icon size="64" color="grey lighten-1" class="mb-4">{{ mdiFileDocumentOutline }}</v-icon>
          <p class="text-h6 grey--text">Nenhuma regra de anotação encontrada.</p>
        </div>
      </div>

      <!-- Interface para anotadores - apenas votação -->
      <div v-if="!isAdmin && !activeVotingConfig" class="text-center my-8">
        <v-icon size="64" color="grey lighten-1" class="mb-4">{{ mdiVote }}</v-icon>
        <p class="text-h6 grey--text">Não há votações ativas no momento.</p>
        <p class="text-body-2 grey--text">Aguarde o administrador configurar uma nova votação de regras.</p>
      </div>

      <!-- Votação para anotadores -->
      <div v-if="!isAdmin && activeVotingConfig">
        <!-- Informações sobre o período de votação -->
        <v-alert 
          :type="votingStatus.type" 
          class="mb-4"
          :icon="votingStatus.icon"
        >
          <div class="d-flex align-center">
            <div>
              <strong>{{ votingStatus.title }}</strong>
              <div class="text-caption mt-1">{{ votingStatus.message }}</div>
            </div>
          </div>
        </v-alert>

        <div v-if="pendingRules.length > 0 && isAnnotator && votingStatus.canVote">
          <v-row v-if="loading">
            <v-col cols="12" class="text-center">
              <v-progress-circular indeterminate color="primary" />
            </v-col>
          </v-row>
          <div v-else>
            <v-row class="mb-6">
              <v-col v-for="rule in pendingRules" :key="rule.id" cols="12" sm="6" md="4">
                <v-card outlined class="rule-card mb-4" :class="{ 'voted': rule.id in localVotes }">
                  <v-card-title class="text-subtitle-1 font-weight-medium d-flex align-center">
                    {{ rule.name }}
                    <v-spacer />
                    <v-chip v-if="rule.id in localVotes" small color="primary" text-color="white">
                      <v-icon small left>{{ localVotes[rule.id] ? mdiThumbUp : mdiThumbDown }}</v-icon>
                      {{ localVotes[rule.id] ? 'Sim' : 'Não' }}
                    </v-chip>
                  </v-card-title>
                  <v-card-actions class="justify-space-between">
                    <div>
                      <v-btn
                        small
                        color="success"
                        :disabled="rule.id in answeredRules"
                        :outlined="!(rule.id in localVotes && localVotes[rule.id])"
                        @click="vote(rule.id, true)"
                      >
                        <v-icon left>{{ mdiThumbUp }}</v-icon>
                        Aprovar
                      </v-btn>
                      <v-btn
                        small
                        color="error"
                        class="ml-2"
                        :disabled="rule.id in answeredRules"
                        :outlined="!(rule.id in localVotes && !localVotes[rule.id])"
                        @click="vote(rule.id, false)"
                      >
                        <v-icon left>{{ mdiThumbDown }}</v-icon>
                        Rejeitar
                      </v-btn>
                    </div>
                    <v-btn
                      v-if="rule.id in localVotes && !(rule.id in answeredRules)"
                      small
                      color="grey"
                      outlined
                      @click="removeVote(rule.id)"
                    >
                      <v-icon small>{{ mdiClose }}</v-icon>
                      Remover
                    </v-btn>
                  </v-card-actions>
                  <v-card-text v-if="rule.id in answeredRules" class="pt-0">
                    <v-chip small color="success" text-color="white">
                      <v-icon small left>{{ mdiCheckCircle }}</v-icon>
                      Já votado
                    </v-chip>
                  </v-card-text>
                </v-card>
              </v-col>
            </v-row>
            <v-row>
              <v-col cols="12" class="text-center">
                <v-btn
                  color="primary"
                  :disabled="!canSubmit"
                  @click="submitVotes"
                  class="px-6"
                  large
                >
                  <v-icon left>{{ mdiSend }}</v-icon>
                  Submeter Todos os Votos
                </v-btn>
                <p class="text-caption mt-2 grey--text">
                  {{ Object.keys(localVotes).length }} de {{ pendingRules.length }} regra(s) votada(s)
                  <span v-if="!canSubmit && pendingRules.length > 0" class="error--text">
                    - Vote em todas as regras para submeter
                  </span>
                </p>
              </v-col>
            </v-row>
          </div>
        </div>
        
        <!-- Casos especiais para anotadores -->
        <div v-else-if="isAnnotator">
          <!-- Já votou em todas as regras -->
          <div v-if="pendingRules.length === 0 && votingStatus.canVote">
            <v-row>
              <v-col cols="12" class="text-center">
                <v-icon size="64" color="success" class="mb-4">{{ mdiCheckCircle }}</v-icon>
                <p class="text-h6 success--text">Parabéns! Você já votou em todas as regras disponíveis.</p>
                <p class="text-body-2 grey--text">Aguarde o resultado da votação ou novas regras serem adicionadas.</p>
              </v-col>
            </v-row>
          </div>
          
          <!-- Votação não disponível por questões de tempo -->
          <div v-else>
            <v-row>
              <v-col cols="12" class="text-center">
                <v-icon size="64" :color="votingStatus.type" class="mb-4">{{ votingStatus.icon }}</v-icon>
                <p class="text-h6" :class="`${votingStatus.type}--text`">{{ votingStatus.title }}</p>
                <p class="text-body-2 grey--text">{{ votingStatus.message }}</p>
              </v-col>
            </v-row>
          </div>
        </div>
        
        <!-- Aviso para não-anotadores -->
        <div v-else>
          <v-row>
            <v-col cols="12" class="text-center">
              <v-icon size="64" color="warning" class="mb-4">{{ mdiInformation }}</v-icon>
              <p class="text-h6 warning--text">Sem permissão para votar</p>
              <p class="text-body-2 grey--text">Apenas anotadores podem participar da votação.</p>
            </v-col>
          </v-row>
        </div>
      </div>
    </v-card-text>
  </v-card>
</template>

<script lang="ts">
import Vue from 'vue'
import { mapGetters } from 'vuex'
import {
  mdiHome,
  mdiGavel,
  mdiCog,
  mdiCheckCircle,
  mdiAlertCircle,
  mdiInformation,
  mdiFileDocumentOutline,
  mdiVote,
  mdiThumbUp,
  mdiThumbDown,
  mdiSend,
  mdiClose,
  mdiClockOutline,
  mdiCalendarClock
} from '@mdi/js'
import { VotingConfigurationItem, AnnotationRuleItem } from '~/domain/models/rules/rule'
import { MemberItem } from '~/domain/models/member/member'
import RuleList from '~/components/rules/RuleList.vue'
import datasetNameMixin from '~/mixins/datasetName.js'

export type Discussion = {
  numberVersion: string
  ruleDiscussion: string
  isFinalized: boolean
  result: string
  votesFor: number
  votesAgainst: number
}

export type VotingAnswer = VotingConfigurationItem & {
  fileName?: string
}

export default Vue.extend({
  components: {
    RuleList
  },
  mixins: [datasetNameMixin],
  
  layout: 'project',
  middleware: ['check-auth', 'auth', 'setCurrentProject'],
  data() {
    return {
      successMessage: '',
      errorMessage: '',
      loading: true,
      rules: [] as any[],
      votesYes: {} as Record<number, number>,
      votesNo: {} as Record<number, number>,
      // regras já votadas (dados do servidor ou após submit)
      answeredRules: {} as Record<number, boolean>,
      // regras finalizadas quando atingem número mínimo de votos
      finalizedRules: {} as Record<number, boolean>,
      // votos locais antes de enviar
      localVotes: {} as Record<number, boolean>,
      votingConfigs: [] as VotingAnswer[],
      groupedRules: {} as Record<number, any[]>,
      memberId: 0,
      annotationRuleTypes: [] as any[],
      isAdmin: false,
      items: [] as Discussion[],
      currentTime: Date.now(),
      timerId: 0 as number,
      mdiHome,
      mdiGavel,
      mdiCog,
      mdiCheckCircle,
      mdiAlertCircle,
      mdiInformation,
      mdiFileDocumentOutline,
      mdiVote,
      mdiThumbUp,
      mdiThumbDown,
      mdiSend,
      mdiClose,
      mdiClockOutline,
      mdiCalendarClock,
      activeVotingConfig: null as VotingAnswer | null,
      pendingRules: [] as AnnotationRuleItem[],
      isAnnotator: false
    }
  },
  computed: {
    ...mapGetters('projects', ['project']),
    projectId() {
      return this.$route.params.id
    },
    hasActiveVoting() {
      return this.activeVotingConfig !== null
    },
    canSubmit() {
      // Só pode submeter se todas as regras pendentes têm voto selecionado
      return this.pendingRules.length > 0 && 
             this.pendingRules.every(rule => rule.id in this.localVotes)
    },
    votingStatus() {
      if (!this.activeVotingConfig) {
        return {
          type: 'info',
          icon: this.mdiInformation,
          title: 'Sem votação ativa',
          message: 'Não há votações disponíveis no momento.',
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
          title: 'Votação ainda não iniciou',
          message: `A votação começará em ${this.formatDate(beginDate)}`,
          canVote: false
        }
      }

      if (now > endDate) {
        return {
          type: 'error',
          icon: this.mdiCalendarClock,
          title: 'Votação expirada',
          message: `A votação terminou em ${this.formatDate(endDate)}`,
          canVote: false
        }
      }

      return {
        type: 'success',
        icon: this.mdiVote,
        title: 'Votação ativa',
        message: `Você pode votar até ${this.formatDate(endDate)}`,
        canVote: true
      }
    }
  },
  async fetch() {
    this.loading = true
    try {
      const projectId = this.projectId
      // buscar todos os membros e filtrar apenas anotadores
      const members: MemberItem[] = await this.$repositories.member.list(projectId)
      const annotatorIds: number[] = members.filter((m) => m.isAnnotator).map((m) => m.id)
      // membro
      const member = await this.$repositories.member.fetchMyRole(projectId)
      this.memberId = member.id
      this.isAdmin = member.isProjectAdmin
      this.isAnnotator = member.isAnnotator
      
      // configs e regras
      this.votingConfigs = await this.$services.votingConfiguration.list(projectId)
      // Filtrar apenas as configurações do projeto atual
      this.votingConfigs = this.votingConfigs.filter(
        (config) => config.project === Number(projectId)
      )
      
      // Para anotadores, usar a nova API que retorna apenas regras não votadas
      if (this.isAnnotator && !this.isAdmin) {
        const unvotedData = await this.$services.annotationRule.listUnvoted(projectId)
        this.rules = unvotedData.rules
        this.pendingRules = unvotedData.rules as AnnotationRuleItem[]
        
        // Atualizar informações de votação ativa baseado na resposta da API
        if (unvotedData.activeVotings.length > 0) {
          const activeVoting = unvotedData.activeVotings.find(v => v.is_active)
          if (activeVoting) {
            this.activeVotingConfig = this.votingConfigs.find(c => c.id === activeVoting.id) || null
          }
        }
        
        // Para anotadores, não precisamos processar histórico
        this.items = []
        this.answeredRules = {}
        this.finalizedRules = {}
        
        console.log(`Anotador: ${unvotedData.totalUnvotedRules} regra(s) disponível(is) para votação`)
      } else {
        // Para administradores, manter o comportamento original
        this.rules = await this.$services.annotationRule.list(projectId)

        // Identificar a configuração de votação ativa (não fechada) para o projeto atual
        this.activeVotingConfig = this.votingConfigs.find((config) => 
          !config.is_closed && config.project === Number(projectId)
        ) || null

        // inicializa agrupamentos e estados
        this.groupedRules = {}
        this.answeredRules = {}
        this.finalizedRules = {}
        // processa todas as configurações
        this.votingConfigs.forEach(async (cfg) => {
          const list = this.rules.filter((r) => r.voting_configuration === cfg.id)
          this.groupedRules[cfg.id] = list

          for (const r of list) {
            const ans = await this.$services.annotationRuleAnswerService.list(projectId, r.id)
            const endTime = Date.parse(cfg.end_date)
            const isExpired = this.currentTime >= endTime
            const numberVersion = 'V_' + String(cfg.version).padStart(2, '0');

            this.$set(this.votesYes, r.id, ans.filter((a) => a.answer).length)
            this.$set(this.votesNo, r.id, ans.filter((a) => !a.answer).length)
            const yes = this.votesYes[r.id] || 0
            const no = this.votesNo[r.id] || 0
            const total = yes + no

            // marca finalizada quando todos os anotadores votaram
            const votesFromAnnotators = ans.filter((a) => annotatorIds.includes(a.member)).length
            if (votesFromAnnotators >= annotatorIds.length || isExpired) {
              this.$set(this.finalizedRules, r.id, true)
            }

            const percentageFavor = total ? Math.round((yes / total) * 100) : 0

            let result = ''
            if (percentageFavor >= cfg.percentage_threshold) {
              result = 'Approved'
            } else {
              result = 'Rejected'
            }
            // persiste finalização e resultado no backend
            if (votesFromAnnotators >= annotatorIds.length || isExpired) {
              await this.$services.annotationRule.update(projectId, r.id, {
                is_finalized: true,
                final_result: result
              })
            }
            if (r.is_finalized === true) {
              this.items.push({
                numberVersion,
                ruleDiscussion: r.name,
                isFinalized: r.is_finalized,
                result,
                votesFor: this.votesYes[r.id] || 0,
                votesAgainst: this.votesNo[r.id] || 0
              })
            }
            if (ans.some((a) => a.member === this.memberId)) {
              this.$set(this.answeredRules, r.id, true)
            }
          }
        })

        this.pendingRules = this.rules.filter(
          (rule) => !this.answeredRules[rule.id]
        ) as AnnotationRuleItem[]
      }
    } catch (error) {
      this.handleError(error)
    } finally {
      this.loading = false
    }
  },
  async mounted() {
    this.timerId = window.setInterval(() => {
      this.currentTime = Date.now()
      this.checkAndCloseCompletedVotings()
    }, 60000)

    await this.checkAndCloseCompletedVotings()
  },
  beforeDestroy() {
    window.clearInterval(this.timerId)
  },
  methods: {
    async checkAndCloseCompletedVotings() {
      try {
        // Permitir que não-admins verifiquem o status, mas apenas admins podem atualizar
        const configs = await this.$services.votingConfiguration.list(this.projectId)
        // Filtrar para garantir que apenas as configurações do projeto atual sejam consideradas
        const projectConfigs = configs.filter(
          (config) => config.project === Number(this.projectId)
        )
        const activeConfigs = projectConfigs.filter((config) => !config.is_closed)

        let votingStatusChanged = false
        const now = new Date()

        for (const config of activeConfigs) {
          const rules = await this.$services.annotationRule.list(this.projectId)
          const configRules = rules.filter((rule) => rule.voting_configuration === config.id)

          const allFinalized =
            configRules.length > 0 && configRules.every((rule) => rule.is_finalized)
          
          // Verificar se a votação expirou por tempo
          const endDate = new Date(config.end_date)
          const isExpired = now > endDate

          if (allFinalized || isExpired) {
            if (this.isAdmin) {
              // Apenas admins podem atualizar o status
              await this.$services.votingConfiguration.update(this.projectId, config.id, {
                ...config,
                is_closed: true
              })
              
              if (isExpired) {
                console.log(`Configuração de votação ${config.id} fechada automaticamente por expiração.`)
                this.successMessage = 'Uma votação foi fechada automaticamente porque o prazo expirou.'
              } else {
                console.log(`Configuração de votação ${config.id} fechada automaticamente.`)
                this.successMessage = 'Uma votação foi fechada automaticamente porque todas as suas regras foram finalizadas.'
              }
            }

            votingStatusChanged = true
          }
        }

        if (votingStatusChanged) {
          // Re-buscar dados e atualizar regras pendentes
          await this.$fetch()
          this.pendingRules = this.rules.filter(
            (rule) => !this.answeredRules[rule.id]
          ) as AnnotationRuleItem[]

          // Atualizar activeVotingConfig
          this.activeVotingConfig = this.votingConfigs.find(
            (config) => !config.is_closed && config.project === Number(this.projectId)
          ) || null
        }
      } catch (error) {
        console.error('Erro ao verificar votações completas:', error)
      }
    },
    goToConfig() {
      this.$router.push({ path: `/projects/${this.projectId}/rules/add` })
    },
    vote(ruleId: number, answer: boolean) {
      this.$set(this.localVotes, ruleId, answer)
      if (answer) this.$set(this.votesYes, ruleId, (this.votesYes[ruleId] || 0) + 1)
      else this.$set(this.votesNo, ruleId, (this.votesNo[ruleId] || 0) + 1)
    },
    removeVote(ruleId: number) {
      // Remove o voto local
      this.$delete(this.localVotes, ruleId)
      
      // Atualizar contadores visuais se necessário
      if (this.votesYes[ruleId] > 0) {
        this.$set(this.votesYes, ruleId, this.votesYes[ruleId] - 1)
      }
      if (this.votesNo[ruleId] > 0) {
        this.$set(this.votesNo, ruleId, this.votesNo[ruleId] - 1)
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
        this.errorMessage = 'Erro do servidor: A base de dados está temporariamente indisponível. Tente novamente em alguns instantes.'
        return
      }
      
      // Verificar se é timeout ou erro de gateway
      if (error.code === 'ECONNABORTED' || error.response.status === 502 || error.response.status === 504) {
        this.errorMessage = 'Erro de conexão: O servidor está sobrecarregado ou a base de dados está indisponível. Tente novamente em alguns minutos.'
        return
      }
      
      // Tratamento específico de outros erros
      if (error.response && error.response.status === 400) {
        this.errorMessage = 'Erro ao carregar dados. Alguns dados podem estar inconsistentes.'
      } else if (error.response && error.response.status === 403) {
        this.errorMessage = 'Você não tem permissão para acessar estes dados.'
      } else if (error.response && error.response.status === 404) {
        this.errorMessage = 'Dados não encontrados. O projeto ou votação pode ter sido removido.'
      } else {
        this.errorMessage = 'Erro inesperado ao carregar dados. Verifique sua conexão e tente novamente.'
      }
    },
    async submitVotes() {
      try {
        for (const [ruleIdStr, answer] of Object.entries(this.localVotes)) {
          const ruleId = Number(ruleIdStr)
          await this.$services.annotationRuleAnswerService.create(this.projectId, {
            annotation_rule: ruleId,
            member: this.memberId,
            answer
          })
          this.$set(this.answeredRules, ruleId, true)
        }
        this.localVotes = {}
        this.successMessage = `Votos submetidos com sucesso! Você votou em ${Object.keys(this.localVotes).length || Object.keys(this.answeredRules).length} regra(s).`

        // Para anotadores, recarregar apenas regras não votadas
        if (this.isAnnotator && !this.isAdmin) {
          const unvotedData = await this.$services.annotationRule.listUnvoted(this.projectId)
          this.rules = unvotedData.rules
          this.pendingRules = unvotedData.rules as AnnotationRuleItem[]
          
          console.log(`Após votação: ${unvotedData.totalUnvotedRules} regra(s) restante(s) para votação`)
          
          // Se não há mais regras para votar, mostrar mensagem específica
          if (unvotedData.totalUnvotedRules === 0) {
            this.successMessage = 'Parabéns! Você votou em todas as regras disponíveis.'
          }
        } else {
          // Para administradores, manter comportamento original
          this.pendingRules = this.rules.filter(
            (rule) => !this.answeredRules[rule.id]
          ) as AnnotationRuleItem[]
        }

        // Verificar se a votação pode ser fechada agora
        if (this.activeVotingConfig) {
          await this.checkAndCloseCompletedVotings()
        }
      } catch (error: any) {
        console.error('Erro ao submeter votos:', error)
        
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
          this.errorMessage = 'Erro do servidor: A base de dados está temporariamente indisponível. Tente novamente em alguns instantes.'
          return
        }
        
        // Verificar se é timeout ou erro de gateway
        if (error.code === 'ECONNABORTED' || error.response.status === 502 || error.response.status === 504) {
          this.errorMessage = 'Erro de conexão: O servidor está sobrecarregado ou a base de dados está indisponível. Tente novamente em alguns minutos.'
          return
        }
        
        // Tratamento específico de outros erros
        if (error.response?.status === 403) {
          this.errorMessage = 'Você não tem permissão para votar. Apenas anotadores podem votar nas regras de anotação.'
        } else if (error.response?.status === 400) {
          const detail = error.response.data?.detail
          if (detail?.includes('já votou')) {
            this.errorMessage = 'Você já votou em uma ou mais dessas regras. Atualizando a página...'
            // Recarregar dados para sincronizar
            setTimeout(() => {
              this.$fetch()
            }, 2000)
          } else if (detail?.includes('votação já foi fechada')) {
            this.errorMessage = 'Esta votação já foi fechada. Não é mais possível votar.'
          } else if (detail?.includes('regra já foi finalizada')) {
            this.errorMessage = 'Uma ou mais regras já foram finalizadas. Não é mais possível votar nelas.'
          } else if (detail?.includes('ainda não começou')) {
            this.errorMessage = detail
            // Recarregar dados para atualizar status
            setTimeout(() => {
              this.$fetch()
            }, 2000)
          } else if (detail?.includes('já expirou')) {
            this.errorMessage = detail
            // Recarregar dados para atualizar status
            setTimeout(() => {
              this.$fetch()
            }, 2000)
          } else {
            this.errorMessage = 'Erro ao submeter votos. Tente novamente.'
          }
        } else {
          this.errorMessage = 'Erro inesperado. Verifique sua conexão e tente novamente.'
        }
      }
    },
    stripExtension(filename?: string): string {
      // Agora retorna o nome completo em vez de remover a extensão
      return filename || ''
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
.rules-card {
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05) !important;
}

.rule-card {
  transition: transform 0.2s, box-shadow 0.2s;
  border-radius: 8px;
}

.rule-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1) !important;
}

.rule-card.voted {
  border: 2px solid #1976d2;
  background: linear-gradient(135deg, #f8f9ff 0%, #ffffff 100%);
}

.rule-card.voted:hover {
  transform: translateY(-3px);
  box-shadow: 0 6px 12px rgba(25, 118, 210, 0.15) !important;
}

::v-deep .v-card__title {
  padding: 16px;
}

::v-deep .v-card__text {
  padding: 16px;
}

/* Animação para botões de voto */
.v-btn {
  transition: all 0.3s ease;
}

.v-btn:not(.v-btn--outlined) {
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.v-btn:not(.v-btn--outlined):hover {
  box-shadow: 0 4px 8px rgba(0, 0, 0, 0.15);
  transform: translateY(-1px);
}

/* Estilo para alertas */
.v-alert {
  border-radius: 8px;
}

/* Estilo para chips de voto */
.v-chip {
  font-weight: 500;
}
</style>
