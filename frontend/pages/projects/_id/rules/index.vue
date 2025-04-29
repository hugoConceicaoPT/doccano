<template>
  <v-card>
    <v-card-title>Votação para regras de anotações</v-card-title>
    <v-alert v-if="successMessage" type="success" dismissible @click="successMessage = ''">
      {{ successMessage }}
    </v-alert>
    <v-alert v-if="errorMessage" type="error" dismissible @click="errorMessage = ''">
      {{ errorMessage }}
    </v-alert>

    <v-card-text>
      <!-- Botão para configurar regras de anotação -->
      <v-row v-if="isAdmin" class="mb-4">
        <v-col cols="12">
          <v-btn color="primary" class="mx-4" @click="goToConfig">
            Configure
          </v-btn>
          <discussion-list :items="items" :is-loading="loading" />
        </v-col>
      </v-row>

      <!-- Votação para não-admins -->
      <div v-if="!isAdmin">
        <div v-if="pendingRules.length > 0">
          <v-row v-if="loading">
            <v-col cols="12" class="text-center">
              <v-progress-circular indeterminate color="primary" />
            </v-col>
          </v-row>
          <div v-else>
            <!-- Exibe todas as regras pendentes sem divisão por dataset -->
            <v-row class="mb-6">
              <v-col v-for="rule in pendingRules" :key="rule.id" cols="12" sm="6" md="4">
                <v-card outlined class="mb-4">
                  <v-card-title>{{ rule.name }}</v-card-title>
                  <v-card-subtitle>{{ rule.description }}</v-card-subtitle>
                  <v-card-actions>
                    <v-btn small color="success" :disabled="rule.id in localVotes"
                      @click="vote(rule.id, true)">Sim</v-btn>
                    <v-btn small color="error" :disabled="rule.id in localVotes"
                      @click="vote(rule.id, false)">Não</v-btn>
                  </v-card-actions>
                </v-card>
              </v-col>
            </v-row>
            <!-- Botão global de submissão -->
            <v-row>
              <v-col cols="12" class="text-center">
                <v-btn color="primary" :disabled="!canSubmit" @click="submitVotes">Submeter Votos</v-btn>
              </v-col>
            </v-row>
          </div>
        </div>
        <div v-else>
          <v-row>
            <v-col cols="12" class="text-center">
              <p>Não existem regras para serem votadas.</p>
            </v-col>
          </v-row>
        </div>
      </div>
      <!-- Mensagem após submissão de votos -->
    </v-card-text>
  </v-card>
</template>

<script lang="ts">
import Vue from 'vue';
import DiscussionList from '~/components/discussion/DiscussionList.vue';
import { VotingConfigurationItem } from '~/domain/models/rules/rule';
import { MemberItem } from '~/domain/models/member/member';

export type Discussion = {
  numberVersion: string;
  ruleDiscussion: string;
  isFinalized: boolean;
  result: string;
}

export type VotingAnswer = VotingConfigurationItem & {
  fileName?: string;
}

export default Vue.extend({
  components: {
    DiscussionList,
  },
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
      timerId: 0 as number
    };
  },
  async fetch() {
    this.loading = true;
    try {
      const projectId = this.projectId;
      // buscar todos os membros e filtrar apenas anotadores
      const members: MemberItem[] = await this.$repositories.member.list(projectId);
      const annotatorIds: number[] = members.filter(m => m.isAnnotator).map(m => m.id);
      // tipos e membro
      this.annotationRuleTypes = await this.$services.annotationRuleType.list(projectId);
      const member = await this.$repositories.member.fetchMyRole(projectId);
      this.memberId = member.id;
      this.isAdmin = member.isProjectAdmin;
      // configs e regras
      this.votingConfigs = await this.$services.votingConfiguration.list(projectId);
      this.rules = await this.$services.annotationRule.list(projectId);
      // inicializa agrupamentos e estados
      this.groupedRules = {};
      this.answeredRules = {};
      this.finalizedRules = {};
      // processa todas as configurações
      this.votingConfigs.forEach(async (cfg) => {
        try {
          const list = this.rules.filter(r => r.voting_configuration === cfg.id)
          this.groupedRules[cfg.id] = list

          for (const r of list) {
            const ans = await this.$services.annotationRuleAnswerService.list(projectId, r.id);
            const rulesFilteredByName = this.rules.filter(rule => rule.name === r.name);
            const votingConfigsOrderedByEndDate = this.votingConfigs.sort((a, b) => new Date(a.end_date).getTime() - new Date(b.end_date).getTime());

            const sortedRules = rulesFilteredByName.sort((ruleA, ruleB) => {
              const configA = this.votingConfigs.find(cfg => cfg.id === ruleA.voting_configuration);
              const configB = this.votingConfigs.find(cfg => cfg.id === ruleB.voting_configuration);
              if (!configA || !configB) return 0;

              const indexA = votingConfigsOrderedByEndDate.indexOf(configA);
              const indexB = votingConfigsOrderedByEndDate.indexOf(configB);

              return indexA - indexB;
            });

            const index = sortedRules.findIndex(sortedRule => sortedRule.id === r.id)
            const endTime = Date.parse(cfg.end_date) - 60 * 60 * 1000
            const isExpired = this.currentTime > endTime
            let numberVersion = '';
            if (index < 10) {
              numberVersion = 'V_0' + (index + 1);
            } else {
              numberVersion = 'V_' + (index + 1);
            }

            this.$set(this.votesYes, r.id, ans.filter(a => a.answer).length);
            this.$set(this.votesNo, r.id, ans.filter(a => !a.answer).length);

            const yes = this.votesYes[r.id] || 0;
            const no = this.votesNo[r.id] || 0;
            const total = yes + no;

            // marca finalizada quando todos os anotadores votaram
            const votesFromAnnotators = ans.filter(a => annotatorIds.includes(a.member)).length;
            if (votesFromAnnotators >= annotatorIds.length || isExpired) {
              this.$set(this.finalizedRules, r.id, true);
            }

            const percentageFavor = total ? Math.round((yes / total) * 100) : 0;
            const percentageAgainst = total ? Math.round((no / total) * 100) : 0;

            let result = '';
            if (percentageAgainst >= cfg.percentage_threshold) {
              result = 'Rejected';
            } else if (percentageFavor >= cfg.percentage_threshold) {
              result = 'Approved';
            } else {
              result = 'Needs Discussion';
            }

            // persiste finalização e resultado no backend
            if (votesFromAnnotators >= annotatorIds.length || isExpired) {
              try {
                await this.$services.annotationRule.update(projectId, r.id, {
                  is_finalized: true,
                  final_result: result,
                });
              } catch (error) {
                console.error('Erro ao finalizar regra:', error);
              }
            }

            if (r.is_finalized === true) {
              this.items.push({
                numberVersion,
                ruleDiscussion: r.description,
                isFinalized: r.is_finalized,
                result
              });
            }
            if (ans.some(a => a.member === this.memberId)) {
              this.$set(this.answeredRules, r.id, true);
            }
          }
        } catch (error) {
          console.error(error);
        }
      });
    } catch {
      this.errorMessage = 'Erro ao carregar dados de votação.';
    } finally {
      this.loading = false;
    }
  },
  mounted() {
    // atualiza currentTime a cada minuto para reavaliar expiração de regras
    this.timerId = window.setInterval(() => { this.currentTime = Date.now(); }, 60000);
  },
  beforeDestroy() {
    window.clearInterval(this.timerId);
  },
  computed: {
    projectId(): string {
      return this.$route.params.id;
    },
    // regras que ainda precisam de voto (não votadas, não finalizadas e dentro do prazo)
    pendingRules(): any[] {
      const now = this.currentTime;
      return this.rules.filter(r => {
        if (r.id in this.answeredRules) return false;
        if (r.id in this.finalizedRules) return false;
        const cfg = this.votingConfigs.find(c => c.id === r.voting_configuration);
        if (!cfg) return false;
        const endTime = new Date(cfg.end_date).getTime();
        if (isNaN(endTime) || now > endTime) return false;
        return true;
      });
    },
    // habilita submit quando cada pendente tiver voto local
    canSubmit(): boolean {
      return this.pendingRules.length > 0 &&
        this.pendingRules.every(r => r.id in this.localVotes);
    },
    // configurações com regras pendentes
    availableConfigs(): any[] {
      return this.votingConfigs.filter(cfg =>
        (this.groupedRules[cfg.id] || []).some(r => !(r.id in this.answeredRules))
      );
    }
  },
  methods: {
    goToConfig() {
      this.$router.push({ path: `/projects/${this.projectId}/rules/add` });
    },
    vote(ruleId: number, answer: boolean) {
      this.$set(this.localVotes, ruleId, answer);
      if (answer) this.$set(this.votesYes, ruleId, (this.votesYes[ruleId] || 0) + 1);
      else this.$set(this.votesNo, ruleId, (this.votesNo[ruleId] || 0) + 1);
    },
    async submitVotes() {
      try {
        for (const [ruleIdStr, answer] of Object.entries(this.localVotes)) {
          const ruleId = Number(ruleIdStr);
          const rule = this.rules.find(r => r.id === ruleId)!;
          const cfg = this.votingConfigs.find(c => c.id === rule.voting_configuration)!;
          await this.$services.annotationRuleAnswerService.create(this.projectId, {
            annotation_rule: ruleId,
            member: this.memberId,
            answer,
            annotation_rule_type: cfg.annotation_rule_type,
          });
          this.$set(this.answeredRules, ruleId, true);
        }
        this.localVotes = {};
        this.successMessage = 'Votos submetidos com sucesso.';
      } catch (error: any) {
        console.error('Erro ao submeter votos:', error);
        let msg = 'Erro ao submeter votos.';
        if (error.response?.data) msg = error.response.data.detail || JSON.stringify(error.response.data);
        else if (error.message) msg = error.message;
        this.errorMessage = msg;
      }
    },
    getRuleTypeName(typeId: number): string {
      const t = this.annotationRuleTypes.find(t => t.id === typeId);
      return t ? t.annotation_rule_type : '';
    },
    stripExtension(filename?: string): string {
      return filename ? filename.replace(/\.[^/.]+$/, '') : '';
    }
  },
});
</script>