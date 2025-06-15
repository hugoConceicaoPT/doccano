<template>
  <v-card class="rules-card">
    <!-- Título apenas para administradores -->
    <div>
      <v-card-title class="d-flex align-center py-4">
        <span class="text-h5 font-weight-medium">
          <v-icon left class="mr-2 primary--text">{{ mdiGavel }}</v-icon>
          Annotation Rules
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

    <v-card-text class="pa-4">
      <v-alert v-if="successMessage" type="success" dismissible class="mb-4">
        <v-icon left>{{ mdiCheckCircle }}</v-icon>
        {{ successMessage }}
      </v-alert>
      <v-alert v-if="errorMessage" type="error" dismissible class="mb-4">
        <v-icon left>{{ mdiAlertCircle }}</v-icon>
        {{ errorMessage }}
      </v-alert>

      <v-alert v-if="hasActiveVoting" type="info" class="mb-4">
        There is an active voting (Version {{ activeVotingConfig?.version }}).
        It is not possible to create a new voting until all rules of the current voting are finalized.
      </v-alert>

      <v-alert v-if="!hasActiveVoting" type="success" class="mb-4">
        There is no active voting. You can configure a new voting.
      </v-alert>

      <div v-if="loading" class="text-center my-8">
        <v-progress-circular
          indeterminate
          color="primary"
          size="64"
        ></v-progress-circular>
      </div>

      <!-- Botão voltar apenas para administradores -->
      <v-row v-if="!loading" class="mb-4">
        <v-col cols="12">
          <v-btn
            color="secondary"
            outlined
            @click="$router.push(localePath(`/projects/${projectId}`))"
          >
            <v-icon left>{{ mdiHome }}</v-icon>
            Back to Home
          </v-btn>
        </v-col>
      </v-row>

      <!-- Histórico de regras - apenas para administradores -->
      <div>
        <rule-list v-if="!loading && items.length > 0" :items="items" :is-loading="loading" />

        <div v-if="!loading && items.length === 0" class="text-center my-8">
          <v-icon size="64" color="grey lighten-1" class="mb-4">{{ mdiFileDocumentOutline }}</v-icon>
          <p class="text-h6 grey--text">No annotation rules found.</p>
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
  mdiFileDocumentOutline
} from '@mdi/js'
import { AnnotationRuleItem } from '~/domain/models/rules/rule'
import RuleList from '~/components/rules/RuleList.vue'

export default Vue.extend({
  components: {
    RuleList
  },
  layout: 'project',
  middleware: ['check-auth', 'auth', 'project-closed'],
  data() {
    return {
      successMessage: '',
      errorMessage: '',
      loading: true,
      rules: [] as AnnotationRuleItem[],
      isAdmin: false,
      items: [] as any[],
      mdiHome,
      mdiGavel,
      mdiCog,
      mdiCheckCircle,
      mdiAlertCircle,
      mdiInformation,
      mdiFileDocumentOutline,
      activeVotingConfig: null as any
    }
  },
  computed: {
    ...mapGetters('projects', ['project']),
    projectId() {
      return this.$route.params.id
    },
    hasActiveVoting() {
      return this.activeVotingConfig !== null
    }
  },
  async fetch() {
    this.loading = true
    try {
      const projectId = this.projectId
      const member = await this.$repositories.member.fetchMyRole(projectId)
      this.isAdmin = member.isProjectAdmin

      if (!this.isAdmin) {
        this.loading = false
        return
      }

      this.rules = await this.$services.annotationRule.list(projectId)
      const votingConfigs = await this.$services.votingConfiguration.list(projectId)
      const filteredConfigs = votingConfigs.filter(
        (config) => config.project === Number(projectId)
      )

      this.activeVotingConfig = filteredConfigs.find((config) => !config.is_closed) || null

      const items = []
      for (const cfg of filteredConfigs) {
        const list = this.rules.filter((r) => r.voting_configuration === cfg.id)
        const numberVersion = 'V_' + String(cfg.version).padStart(2, '0')

        for (const r of list) {
          const rulesAnswer = await this.$services.annotationRuleAnswerService.list(projectId, r.id)
          let votesFor = 0
          let votesAgainst = 0
          for(const ruleAnswer of rulesAnswer) {
            if(ruleAnswer.answer)
              votesFor++
            else
              votesAgainst++
          }
          if (r.is_finalized) {
            items.push({
              numberVersion,
              ruleDiscussion: r.name,
              isFinalized: r.is_finalized,
              result: r.final_result,
              votesFor,
              votesAgainst
            })
          }
        }
      }

      this.items = items
    } catch (error) {
      this.handleError(error)
    } finally {
      this.loading = false
    }
  },
  methods: {
    goToConfig() {
      this.$router.push({ path: `/projects/${this.projectId}/rules/add` })
    },
    handleError(error: any) {
      if (error.response && error.response.status === 400) {
        this.errorMessage = 'Error retrieving data.'
      } else {
        this.errorMessage = 'Database is slow or unavailable. Please try again later.'
      }
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
