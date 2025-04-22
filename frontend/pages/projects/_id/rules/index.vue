<template>
  <v-card>
    <v-alert v-if="successMessage" type="success" dismissible @click="successMessage = ''">
      {{ successMessage }}
    </v-alert>
    <v-alert v-if="errorMessage" type="error" dismissible @click="errorMessage = ''">
      {{ errorMessage }}
    </v-alert>

    <v-card-title>Voting de Regras de Anotação</v-card-title>
    <v-card-text>
      <v-container>
        <!-- Configuração (admins) -->
        <v-row class="mb-4" v-if="isAdmin">
          <v-col cols="12">
            <v-btn color="primary" @click="goToConfig">Configurar</v-btn>
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
              <!-- Exibe apenas datasets com regras pendentes -->
              <div v-for="cfg in availableConfigs" :key="cfg.id" class="mb-6">
                <v-subheader>Dataset: {{ stripExtension(cfg.filename) }}</v-subheader>
                <v-row>
                  <v-col
                    v-for="rule in pendingRules.filter(r => r.voting_configuration === cfg.id)"
                    :key="rule.id"
                    cols="12" sm="6" md="4"
                  >
                    <v-card outlined class="mb-4">
                      <v-card-title>{{ rule.name }}</v-card-title>
                      <v-card-subtitle>{{ rule.description }}</v-card-subtitle>
                      <v-card-actions>
                        <v-btn small color="success" :disabled="rule.id in localVotes" @click="vote(rule.id, true)">Sim</v-btn>
                        <v-btn small color="error" :disabled="rule.id in localVotes" @click="vote(rule.id, false)">Não</v-btn>
                      </v-card-actions>
                    </v-card>
                  </v-col>
                </v-row>
              </div>
              <!-- Botão global de submissão -->
              <v-row>
                <v-col cols="12" class="text-center">
                  <v-btn color="primary" @click="submitVotes" :disabled="!canSubmit">Submeter Votos</v-btn>
                </v-col>
              </v-row>
            </div>
          </div>
          <div v-else>
            <v-row>
              <v-col cols="12" class="text-center">
                <p>Votação concluída com sucesso!</p>
              </v-col>
            </v-row>
          </div>
        </div>
      </v-container>
    </v-card-text>
  </v-card>
</template>

<script lang="ts">
import Vue from 'vue';

export default Vue.extend({
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
      // votos locais antes de enviar
      localVotes: {} as Record<number, boolean>,
      votingConfigs: [] as any[],
      groupedRules: {} as Record<number, any[]>,
      memberId: 0,
      annotationRuleTypes: [] as any[],
      isAdmin: false,
    };
  },
  computed: {
    projectId(): string {
      return this.$route.params.id;
    },
    // regras ainda não votadas
    pendingRules(): any[] {
      return this.rules.filter(r => !(r.id in this.answeredRules));
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
    stripExtension(filename: string): string {
      return filename.replace(/\.[^/.]+$/, '');
    }
  },
  async fetch() {
    this.loading = true;
    try {
      const projectId = this.projectId;
      // tipos e membro
      this.annotationRuleTypes = await this.$services.annotationRuleType.list(projectId);
      const member = await this.$repositories.member.fetchMyRole(projectId);
      this.memberId = member.id;
      this.isAdmin = member.isProjectAdmin;
      // configs e regras
      this.votingConfigs = await this.$services.votingConfiguration.list(projectId);
      this.rules = await this.$services.annotationRule.list(projectId);
      // agrupa e inicializa answeredRules
      this.groupedRules = {};
      this.answeredRules = {};
      for (const cfg of this.votingConfigs) {
        try {
          const ex = await this.$services.example.findById(projectId, cfg.example);
          (cfg as any).filename = ex.filename;
        } catch {
          (cfg as any).filename = String(cfg.example);
        }
        const list = this.rules.filter(r => r.voting_configuration === cfg.id);
        this.groupedRules[cfg.id] = list;
        for (const r of list) {
          const ans = await this.$services.annotationRuleAnswerService.list(projectId, r.id);
          this.$set(this.votesYes, r.id, ans.filter(a => a.answer).length);
          this.$set(this.votesNo, r.id, ans.filter(a => !a.answer).length);
          if (ans.some(a => a.member === this.memberId)) this.$set(this.answeredRules, r.id, true);
        }
      }
    } catch {
      this.errorMessage = 'Erro ao carregar dados de votação.';
    } finally {
      this.loading = false;
    }
  },
});
</script>