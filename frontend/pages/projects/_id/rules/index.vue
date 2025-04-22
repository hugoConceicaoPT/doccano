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

        <!-- Sistema de votação para não-admins, não exibir após submissão -->
        <template v-if="!isAdmin && !submittedVotes">
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
                    <v-card-title>
                      {{ rule.name }}
                    </v-card-title>
                    <v-card-subtitle>
                      {{ rule.description }}
                    </v-card-subtitle>
                    <v-card-text>
                      Sim: {{ votesYes[rule.id] || 0 }} | Não: {{ votesNo[rule.id] || 0 }}
                    </v-card-text>
                    <v-card-actions>
                      <v-btn
                        small
                        color="success"
                        :disabled="rule.id in localVotes"
                        @click="vote(rule.id, true)"
                      >
                        Sim
                      </v-btn>
                      <v-btn
                        small
                        color="error"
                        :disabled="rule.id in localVotes"
                        @click="vote(rule.id, false)"
                      >
                        Não
                      </v-btn>
                    </v-card-actions>
                  </v-card>
                </v-col>
              </v-row>
              <!-- Botão de submissão: sempre visível, mas desabilitado até todas as regras votadas -->
              <v-row>
                <v-col cols="12" class="text-center">
                  <v-btn
                    color="primary"
                    @click="submitVotes"
                    :disabled="loading || !canSubmit"
                  >
                    Submeter Votos
                  </v-btn>
                </v-col>
              </v-row>
            </v-col>
          </v-row>
        </template>
        <!-- Mensagem após submissão de votos -->
        <template v-else-if="!isAdmin && submittedVotes">
          <v-row>
            <v-col cols="12" class="text-center">
              <p>Votação concluída com sucesso!</p>
            </v-col>
          </v-row>
        </template>
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
      // IDs das regras já respondidas (preenchidas no fetch)
      localVotes: {} as Record<number, boolean>,
      votingConfig: null as any,
      memberId: 0,
      // Lista de tipos de regra para exibir nome
      annotationRuleTypes: [] as any[],
      isAdmin: false,
      // Indica se os votos já foram submetidos
      submittedVotes: false,
    };
  },
  computed: {
    projectId(): string {
      return this.$route.params.id;
    },
    // Habilita botão submit somente quando todas as regras forem votadas
    canSubmit(): boolean {
      return Object.keys(this.localVotes).length === this.rules.length;
    }
  },
  methods: {
    goToConfig() {
      this.$router.push({ path: `/projects/${this.projectId}/rules/add` });
    },
    // Registra voto localmente (não envia ao servidor)
    vote(ruleId: number, answer: boolean) {
      // Atualiza contagem local
      this.$set(this.localVotes, ruleId, answer);
      if (answer) {
        this.$set(this.votesYes, ruleId, (this.votesYes[ruleId] || 0) + 1);
      } else {
        this.$set(this.votesNo, ruleId, (this.votesNo[ruleId] || 0) + 1);
      }
    },
    // Submete todos os votos ao servidor
    async submitVotes() {
      try {
        for (const [ruleIdStr, answer] of Object.entries(this.localVotes)) {
          const ruleId = Number(ruleIdStr);
          const payload = {
            annotation_rule: ruleId,
            member: this.memberId,
            answer,
            annotation_rule_type: this.votingConfig.annotation_rule_type,
          };
          await this.$services.annotationRuleAnswerService.create(this.projectId, payload);
        }
        this.successMessage = 'Votos submetidos com sucesso.';
        // Marca votos como submetidos
        this.submittedVotes = true;
      } catch {
        this.errorMessage = 'Erro ao submeter votos.';
      }
    },
  },
  async fetch() {
    this.loading = true;
    try {
      const projectId = this.projectId;
      // Carrega tipos de regras
      this.annotationRuleTypes = await this.$services.annotationRuleType.list(projectId);
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
      // Carrega todas as regras
      const allRules = await this.$services.annotationRule.list(projectId);
      this.rules = allRules;
      // Conta e registra votos existentes
      for (const rule of this.rules) {
        const answers = await this.$services.annotationRuleAnswerService.list(projectId, rule.id);
        this.$set(this.votesYes, rule.id, answers.filter((a: any) => a.answer).length);
        this.$set(this.votesNo, rule.id, answers.filter((a: any) => !a.answer).length);
        const my = answers.find((a: any) => a.member === this.memberId);
        if (my) {
          this.$set(this.localVotes, rule.id, my.answer);
        }
      }
      // Se já votou em todas as regras, marque como submetido para não reaparecer o UI
      if (Object.keys(this.localVotes).length === this.rules.length) {
        this.submittedVotes = true;
      }
    } catch {
      this.errorMessage = 'Erro ao carregar dados de votação.';
    } finally {
      this.loading = false;
    }
  },
});
</script>