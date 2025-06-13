<template>
  <v-card>
    <v-card-title>
      Regras de Anotação
      <v-spacer />
      <v-btn
        v-if="isAdmin"
        color="primary"
        class="ml-2"
        :disabled="loading || hasActiveVoting"
        @click="goToConfig"
      >
        Configure Voting
      </v-btn>
    </v-card-title>
    <v-card-text>
      <v-alert v-if="successMessage" type="success" dismissible>{{ successMessage }}</v-alert>
      <v-alert v-if="errorMessage" type="error" dismissible>{{ errorMessage }}</v-alert>

      <v-alert v-if="hasActiveVoting && isAdmin" type="info" class="mb-4">
        Existe uma votação ativa (Versão {{ activeVotingConfig?.version }}). Não é possível criar
        uma nova votação até que todas as regras da votação atual estejam finalizadas.
      </v-alert>

      <v-alert v-if="isAdmin && !hasActiveVoting" type="success" class="mb-4">
        Não existe nenhuma votação ativa. Você pode configurar uma nova votação.
      </v-alert>

      <div v-if="loading" class="text-center my-4">
        <v-progress-circular indeterminate />
      </div>

      <v-row v-else class="mb-4">
        <v-col cols="12">
          <v-btn color="secondary" @click="$router.push(localePath(`/projects/${projectId}`))">
            <v-icon left>{{ mdiHome }}</v-icon>
            Voltar ao projeto
          </v-btn>
        </v-col>
      </v-row>

      <rule-list v-if="!loading && items.length > 0" :items="items" :is-loading="loading" />

      <div v-if="!loading && items.length === 0" class="text-center my-4">
        <p>Nenhuma regra de anotação encontrada.</p>
      </div>

      <!-- Votação para não-admins -->
      <div v-if="!isAdmin && activeVotingConfig">
        <v-divider class="my-4"></v-divider>
        <h3 class="mb-4">Votação de Regras</h3>

        <div v-if="pendingRules.length > 0">
          <v-row v-if="loading">
            <v-col cols="12" class="text-center">
              <v-progress-circular indeterminate color="primary" />
            </v-col>
          </v-row>
          <div v-else>
            <v-row class="mb-6">
              <v-col v-for="rule in pendingRules" :key="rule.id" cols="12" sm="6" md="4">
                <v-card outlined class="mb-4">
                  <v-card-title>{{ rule.name }}</v-card-title>
                  <v-card-subtitle>{{ rule.description }}</v-card-subtitle>
                  <v-card-actions>
                    <v-btn
                      small
                      color="success"
                      :disabled="rule.id in answeredRules"
                      @click="vote(rule.id, true)"
                      >Sim</v-btn
                    >
                    <v-btn
                      small
                      color="error"
                      :disabled="rule.id in answeredRules"
                      @click="vote(rule.id, false)"
                      >Não</v-btn
                    >
                  </v-card-actions>
                </v-card>
              </v-col>
            </v-row>
            <v-row>
              <v-col cols="12" class="text-center">
                <v-btn color="primary" :disabled="!canSubmit" @click="submitVotes"
                  >Submeter Votos</v-btn
                >
              </v-col>
            </v-row>
          </div>
        </div>
        <div v-else>
          <v-row>
            <v-col cols="12" class="text-center">
              <p>Votação concluída com sucesso ou não há regras para votar no momento.</p>
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
import { mdiHome } from '@mdi/js'
import { VotingConfigurationItem, AnnotationRuleItem } from '~/domain/models/rules/rule'
import { MemberItem } from '~/domain/models/member/member'
import RuleList from '~/components/rules/RuleList.vue'

export type Discussion = {
  numberVersion: string
  ruleDiscussion: string
  isFinalized: boolean
  result: string
}

export type VotingAnswer = VotingConfigurationItem & {
  fileName?: string
}

export default Vue.extend({
  components: {
    RuleList
  },
  layout: 'project',
  middleware: ['check-auth', 'auth'],
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
      activeVotingConfig: null as VotingAnswer | null,
      pendingRules: [] as AnnotationRuleItem[]
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
      return Object.keys(this.localVotes).length > 0
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
      // configs e regras
      this.votingConfigs = await this.$services.votingConfiguration.list(projectId)
      this.rules = await this.$services.annotationRule.list(projectId)

      // Identificar a configuração de votação ativa (não fechada)
      this.activeVotingConfig = this.votingConfigs.find((config) => !config.is_closed) || null

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
          const rulesFilteredByName = this.rules.filter((rule) => rule.name === r.name)
          const votingConfigsOrderedByEndDate = this.votingConfigs.sort(
            (a, b) => new Date(a.end_date).getTime() - new Date(b.end_date).getTime()
          )

          const sortedRules = rulesFilteredByName.sort((ruleA, ruleB) => {
            const configA = this.votingConfigs.find((cfg) => cfg.id === ruleA.voting_configuration)
            const configB = this.votingConfigs.find((cfg) => cfg.id === ruleB.voting_configuration)
            if (!configA || !configB) return 0

            const indexA = votingConfigsOrderedByEndDate.indexOf(configA)
            const indexB = votingConfigsOrderedByEndDate.indexOf(configB)

            return indexA - indexB
          })

          const index = sortedRules.findIndex((sortedRule) => sortedRule.id === r.id)
          const endTime = Date.parse(cfg.end_date) - 60 * 60 * 1000
          const isExpired = this.currentTime >= endTime
          let numberVersion = ''
          if (index < 10) {
            numberVersion = 'V_0' + (index + 1)
          } else {
            numberVersion = 'V_' + (index + 1)
          }

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
              ruleDiscussion: r.description,
              isFinalized: r.is_finalized,
              result
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
        const activeConfigs = configs.filter((config) => !config.is_closed)

        let votingStatusChanged = false

        for (const config of activeConfigs) {
          const rules = await this.$services.annotationRule.list(this.projectId)
          const configRules = rules.filter((rule) => rule.voting_configuration === config.id)

          const allFinalized =
            configRules.length > 0 && configRules.every((rule) => rule.is_finalized)

          if (allFinalized) {
            if (this.isAdmin) {
              // Apenas admins podem atualizar o status
              await this.$services.votingConfiguration.update(this.projectId, config.id, {
                ...config,
                is_closed: true
              })
              console.log(`Configuração de votação ${config.id} fechada automaticamente.`)
              this.successMessage =
                'Uma votação foi fechada automaticamente porque todas as suas regras foram finalizadas.'
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
          this.activeVotingConfig = this.votingConfigs.find((config) => !config.is_closed) || null
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
    handleError(error: any) {
      if (error.response && error.response.status === 400) {
        this.errorMessage = 'Error retrieving data.'
      } else {
        this.errorMessage = 'Database is slow or unavailable. Please try again later.'
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
        this.successMessage = 'Votos submetidos com sucesso.'

        // Atualizar a lista de regras pendentes
        this.pendingRules = this.rules.filter(
          (rule) => !this.answeredRules[rule.id]
        ) as AnnotationRuleItem[]

        // Verificar se a votação pode ser fechada agora
        if (this.activeVotingConfig) {
          await this.checkAndCloseCompletedVotings()
        }
      } catch (error: any) {
        console.error('Erro ao submeter votos:', error)
        let msg = 'Erro ao submeter votos.'
        if (error.response?.data)
          msg = error.response.data.detail || JSON.stringify(error.response.data)
        else if (error.message) msg = error.message
        this.errorMessage = msg
      }
    },
    stripExtension(filename?: string): string {
      return filename ? filename.replace(/\.[^/.]+$/, '') : ''
    }
  }
})
</script>
