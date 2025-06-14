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
              console.log(`Voting configuration ${activeConfig.id} automatically closed.`)
            } else {
              this.errorMessage =
                'Cannot configure a new voting because there is an active voting with unfinalized rules.'
              setTimeout(() => {
                this.$router.push(`/projects/${this.projectId}/rules`)
              }, 3000)
              return
            }
          }
        }
      } catch (error) {
                  console.error('Error checking active voting configurations:', error)
          this.errorMessage = 'Error checking active voting configurations.'
      }
    },

    async determineNextVersion() {
      try {
        const existingConfigs = await this.votingConfigurationService.list(this.projectId)
        let nextVersion = 1

        if (existingConfigs && existingConfigs.length > 0) {
          const projectConfigs = existingConfigs.filter(
            (config: { project: number }) => config.project === Number(this.projectId)
          )

          if (projectConfigs.length > 0) {
            const existingVersions = projectConfigs
              .map((config: { version: number }) => config.version)
              .sort((a: number, b: number) => a - b)

            const uniqueVersions = [...new Set(existingVersions)]
            if (uniqueVersions.length !== existingVersions.length) {
              console.warn(
                'Warning: Duplicate versions were detected in voting configurations.'
              )
            }

            const maxVersion = Math.max(...(uniqueVersions as number[]))
            nextVersion = maxVersion + 1

            console.log(
              `Existing versions in project ${this.projectId}: ${uniqueVersions.join(', ')}. Next version: ${nextVersion}`
            )
          } else {
            console.log(`No voting configuration found for project ${this.projectId}. Starting with version 1.`)
          }
        }

        this.editedItem.version = nextVersion
      } catch (error) {
                  console.error('Error determining next version:', error)
          this.errorMessage = 'Error determining the next voting version.'
      }
    },

    async save() {
      try {
        const projectId = Number(this.projectId)

        await this.determineNextVersion()

        // Check version uniqueness for this project
        const existingConfigs = await this.votingConfigurationService.list(this.projectId)
        const projectConfigs = existingConfigs.filter(
          (config: { project: number }) => config.project === projectId
        )

        const versionExists = projectConfigs.some(
          (config: { version: number }) => config.version === this.editedItem.version
        )

        if (versionExists) {
          this.errorMessage = `Version ${this.editedItem.version} already exists for this project. Trying the next version...`
          this.editedItem.version += 1
          console.log(`Updating to the next available version: ${this.editedItem.version}`)
        }

        // Process dates to ensure correct format
        // The datetime-local field sends dates without timezone, we assume they are local (Lisbon)
        let processedBeginDate = this.editedItem.begin_date
        let processedEndDate = this.editedItem.end_date
        
        // If dates don't have timezone, add information that they are local
        if (processedBeginDate && !processedBeginDate.includes('T')) {
          // If it doesn't have 'T', add time format
          processedBeginDate += 'T00:00'
        }
        if (processedEndDate && !processedEndDate.includes('T')) {
          // If it doesn't have 'T', add time format
          processedEndDate += 'T23:59'
        }

        const votingConfigPayload = {
          project: projectId,
          voting_threshold: this.editedItem.voting_threshold,
          percentage_threshold: this.editedItem.percentage_threshold,
          created_by: null,
          begin_date: processedBeginDate,
          end_date: processedEndDate,
          is_closed: false,
          version: this.editedItem.version
        }

        console.log('Sending voting configuration:', votingConfigPayload)

        await this.votingConfigurationService.create(this.projectId, votingConfigPayload)

        const votingConfigs = await this.votingConfigurationService.list(this.projectId)
        if (votingConfigs && votingConfigs.length > 0) {
          // Sort by ID to get the most recent
          const sortedConfigs = [...votingConfigs].sort((a, b) => b.id - a.id)
          this.votingConfigurationId = sortedConfigs[0].id
          console.log('Voting configuration ID:', this.votingConfigurationId)
        } else {
          throw new Error('Unable to get voting configuration ID')
        }

        for (const rule of this.annotationRulesList) {
          const rulePayload = {
            project: projectId,
            name: rule.name,
            voting_configuration: this.votingConfigurationId,
            is_finalized: false,
            final_result: ''
          }
          console.log('Sending rule:', rulePayload)
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
        this.errorMessage = 'Database is slow or unavailable. Please try again later.'
      }
    }
  }
})
</script>
