<template>
  <div>
    <v-alert v-if="sucessMessage" type="success" dismissible>{{ sucessMessage }}</v-alert>
    <v-alert v-if="errorMessage" type="error" dismissible>{{ errorMessage }}</v-alert>
    <form-create
      v-slot="slotProps"
      :edited-item.sync="editedItem"
      :annotation-rules-list.sync="annotationRulesList"
    >
      <v-btn color="error" class="text-capitalize" @click="$router.back()"> Cancel </v-btn>
      <v-btn :disabled="!slotProps.valid" color="primary" class="text-capitalize" @click="save">
        Save
      </v-btn>
    </form-create>
  </div>
</template>

<script lang="ts">
import Vue from 'vue'
import {
  CreateVotingConfigurationCommand,
  CreateAnnotationRuleCommand
} from '~/services/application/rules/ruleCommand'
import FormCreate from '~/components/rules/FormCreate.vue'

export default Vue.extend({
  components: {
    FormCreate
  },

  layout: 'projects',

  middleware: ['check-auth', 'auth', 'setCurrentProject', 'isProjectAdmin'],

  data() {
    return {
      sucessMessage: '',
      errorMessage: '',
      editedItem: {
        project: 0,
        description: '',
        voting_configuration: 0,
        example: 0,
        voting_threshold: 0,
        percentage_threshold: 0.0,
        boolean_threshold: false,
        created_by: 0,
        begin_date: '',
        end_date: '',
        is_closed: false,
        version: 1
      } as CreateVotingConfigurationCommand,
      annotationRulesList: [] as CreateAnnotationRuleCommand[],
      votingConfigurationId: 0
    }
  },

  computed: {
    projectId(): string {
      return this.$route.params.id
    },
    annotationRuleService(): any {
      return this.$services.annotationRule
    },
    votingConfigurationService(): any {
      return this.$services.votingConfiguration
    }
  },

  async mounted() {
    await this.checkActiveVotingConfiguration()
    await this.determineNextVersion()
  },

  methods: {
    async checkActiveVotingConfiguration() {
      try {
        const existingConfigs = await this.votingConfigurationService.list(this.projectId)

        const activeConfigs = existingConfigs.filter(
          (config: { is_closed: boolean }) => !config.is_closed
        )

        if (activeConfigs.length > 0) {
          for (const activeConfig of activeConfigs) {
            const rules = await this.annotationRuleService.list(this.projectId)
            const configRules = rules.filter(
              (rule: { voting_configuration: number }) =>
                rule.voting_configuration === activeConfig.id
            )

            const allRulesFinalized =
              configRules.length === 0 ||
              configRules.every((rule: { is_finalized: boolean }) => rule.is_finalized)

            if (allRulesFinalized) {
              await this.votingConfigurationService.update(this.projectId, activeConfig.id, {
                ...activeConfig,
                is_closed: true
              })
              console.log(`Configuração de votação ${activeConfig.id} fechada automaticamente.`)
            } else {
              this.errorMessage =
                'Não é possível configurar uma nova votação pois existe uma votação ativa com regras não finalizadas.'
              setTimeout(() => {
                this.$router.push(`/projects/${this.projectId}/rules`)
              }, 3000)
              return
            }
          }
        }
      } catch (error) {
        console.error('Erro ao verificar configurações de votação ativas:', error)
        this.errorMessage = 'Erro ao verificar configurações de votação ativas.'
      }
    },

    async determineNextVersion() {
      try {
        const existingConfigs = await this.votingConfigurationService.list(this.projectId)
        let nextVersion = 1

        if (existingConfigs && existingConfigs.length > 0) {
          const existingVersions = existingConfigs
            .map((config: { version: number }) => config.version)
            .sort((a: number, b: number) => a - b)

          const uniqueVersions = [...new Set(existingVersions)]
          if (uniqueVersions.length !== existingVersions.length) {
            console.warn(
              'Atenção: Foram detectadas versões duplicadas nas configurações de votação.'
            )
          }

          const maxVersion = Math.max(...(uniqueVersions as number[]))
          nextVersion = maxVersion + 1

          console.log(
            `Versões existentes: ${uniqueVersions.join(', ')}. Próxima versão: ${nextVersion}`
          )
        }

        this.editedItem.version = nextVersion
      } catch (error) {
        console.error('Erro ao determinar a próxima versão:', error)
        this.errorMessage = 'Erro ao determinar a próxima versão da votação.'
      }
    },

    async save() {
      try {
        const projectId = Number(this.projectId)

        await this.determineNextVersion()

        const votingConfigPayload = {
          project: projectId,
          voting_threshold: this.editedItem.voting_threshold,
          percentage_threshold: this.editedItem.percentage_threshold,
          created_by: null,
          begin_date: this.editedItem.begin_date,
          end_date: this.editedItem.end_date,
          is_closed: false,
          version: this.editedItem.version
        }

        console.log('Enviando configuração de votação:', votingConfigPayload)

        await this.votingConfigurationService.create(this.projectId, votingConfigPayload)

        const votingConfigs = await this.votingConfigurationService.list(this.projectId)
        if (votingConfigs && votingConfigs.length > 0) {
          this.votingConfigurationId = votingConfigs[votingConfigs.length - 1].id
          console.log('ID da configuração de votação:', this.votingConfigurationId)
        } else {
          throw new Error('Não foi possível obter o ID da configuração de votação')
        }

        for (const rule of this.annotationRulesList) {
          const rulePayload = {
            project: projectId,
            name: rule.name,
            description: rule.description,
            voting_configuration: this.votingConfigurationId,
            is_finalized: false,
            final_result: ''
          }
          console.log('Enviando regra:', rulePayload)
          await this.annotationRuleService.create(this.projectId, rulePayload)
        }

        this.sucessMessage = 'Annotation rules saved successfully.'
        setTimeout(() => {
          this.$router.push(`/projects/${this.projectId}/rules`)
        }, 1000)
      } catch (error) {
        this.handleError(error)
      }
    },
    handleError(error: any) {
      if (error.response && error.response.status === 400) {
        this.errorMessage = 'Error saving annotation rules.'
      } else {
        this.errorMessage = 'The database is slow or unavailable. Please try again later.'
      }
    }
  }
})
</script>
