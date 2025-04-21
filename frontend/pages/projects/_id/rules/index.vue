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
        <!-- Botão para configurar regras de anotação -->
        <v-row class="mb-4" v-if="isAdmin">
          <v-col cols="12">
            <v-btn color="primary" @click="goToConfig">
              Configurar
            </v-btn>
          </v-col>
        </v-row>

        <!-- Indicador de carregamento -->
        <v-row v-if="loading">
          <v-col cols="12" class="text-center">
            <v-progress-circular indeterminate color="primary" />
          </v-col>
        </v-row>

        <!-- Lista de regras com votação -->
        <v-row v-else>
          <v-col cols="12" v-if="!rules.length">
            <p>Nenhuma regra disponível para votação.</p>
          </v-col>
          <v-col cols="12" v-else>
            <v-row>
              <v-col
                v-for="rule in rules"
                :key="rule.id"
                cols="12"
                sm="6"
                md="4"
              >
                <v-card outlined class="mb-4">
                  <v-card-title>{{ rule.description }}</v-card-title>
                  <v-card-text>
                    Sim: {{ votesYes[rule.id] || 0 }} | Não: {{ votesNo[rule.id] || 0 }}
                  </v-card-text>
                  <v-card-actions>
                    <v-btn
                      small
                      color="success"
                      :disabled="votedRules.includes(rule.id)"
                      @click="vote(rule.id, true)"
                    >
                      Sim
                    </v-btn>
                    <v-btn
                      small
                      color="error"
                      :disabled="votedRules.includes(rule.id)"
                      @click="vote(rule.id, false)"
                    >
                      Não
                    </v-btn>
                  </v-card-actions>
                </v-card>
              </v-col>
            </v-row>
          </v-col>
        </v-row>
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
      votedRules: [] as number[],
      votingConfig: null as any,
      memberId: 0,
      isAdmin: false,
    };
  },
  computed: {
    projectId(): string {
      return this.$route.params.id;
    },
  },
  methods: {
    goToConfig() {
      this.$router.push({ path: `/projects/${this.projectId}/rules/add` });
    },
    async vote(ruleId: number, answer: boolean) {
      try {
        const payload = {
          annotation_rule: ruleId,
          member: this.memberId,
          answer,
          annotation_rule_type: this.votingConfig.annotation_rule_type,
        };
        await this.$services.annotationRuleAnswerService.create(this.projectId, payload);
        if (answer) {
          this.$set(this.votesYes, ruleId, (this.votesYes[ruleId] || 0) + 1);
        } else {
          this.$set(this.votesNo, ruleId, (this.votesNo[ruleId] || 0) + 1);
        }
        this.votedRules.push(ruleId);
        this.rules = this.rules.filter((r: any) => r.id !== ruleId);
        this.successMessage = 'Voto registrado com sucesso.';
      } catch {
        this.errorMessage = 'Erro ao registrar voto.';
      }
    },
  },
  async fetch() {
    this.loading = true;
    try {
      const projectId = this.projectId;
      // Obtém o membro atual
      const member = await this.$repositories.member.fetchMyRole(projectId);
      this.memberId = member.id;
      this.isAdmin = member.isProjectAdmin;
      // Carrega configurações de votação
      const configs = await this.$services.votingConfiguration.list(projectId);
      if (!configs.length) {
        return;
      }
      this.votingConfig = configs[configs.length - 1];
      // Carrega regras associadas à configuração atual
      const allRules = await this.$services.annotationRule.list(projectId);
      this.rules = allRules;
      // Conta votos existentes
      for (const rule of this.rules) {
        const answers = await this.$services.annotationRuleAnswerService.list(projectId, rule.id);
        this.$set(this.votesYes, rule.id, answers.filter((a: any) => a.answer).length);
        this.$set(this.votesNo, rule.id, answers.filter((a: any) => !a.answer).length);
        if (answers.some((a: any) => a.member === this.memberId)) {
          this.votedRules.push(rule.id);
        }
      }
      // Exibe apenas regras ainda não votadas
      this.rules = this.rules.filter((r: any) => !this.votedRules.includes(r.id));
    } catch {
      this.errorMessage = 'Erro ao carregar dados de votação.';
    } finally {
      this.loading = false;
    }
  },
});
</script>