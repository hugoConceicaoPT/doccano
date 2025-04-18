<template>
  <div>
    <v-alert v-if="sucessMessage" type="success" dismissible>{{ sucessMessage }}</v-alert>
    <v-alert v-if="errorMessage" type="error" dismissible>{{ errorMessage }}</v-alert>
    <form-create
      v-slot="slotProps"
      :editedItem.sync="editedItem"
      :annotationRuleTypes="annotationRuleTypes"
      :annotationRulesList.sync="annotationRulesList"
    >
      <v-btn color="error" class="text-capitalize" @click="$router.back()"> Cancelar </v-btn>
      <v-btn :disabled="!slotProps.valid" color="primary" class="text-capitalize" @click="save">
        Guardar
      </v-btn>
    </form-create>
  </div>
</template>

<script lang="ts">
import Vue from 'vue';
import { CreateVotingConfigurationCommand, CreateAnnotationRuleCommand } from '~/services/application/rules/ruleCommand';
import { AnnotationRuleTypeDTO } from '~/services/application/rules/ruleData';
import FormCreate from '~/components/rules/FormCreate.vue';

export default Vue.extend({
  components: {
    FormCreate,
  },

  layout: 'projects',

  middleware: ['check-auth', 'auth', 'setCurrentProject'],

  data() {
    return {
      sucessMessage: '',
      errorMessage: '',
      editedItem: {
        project: 0,
        description: '', // This description is for the voting configuration if needed
        voting_configuration: 0,
        annotation_rule_type: 0,
        voting_threshold: 0, // Default value for voting threshold
        created_by: 0, // Default value for created_by
        begin_date: '', // Default value for begin_date
        end_date: '', // Default value for end_date
      } as CreateVotingConfigurationCommand,
      annotationRuleTypes: [] as AnnotationRuleTypeDTO[],
      annotationRulesList: [] as CreateAnnotationRuleCommand[], // Array to hold rules added in FormCreate
      votingConfigurationId: 0,
    };
  },

  computed: {
    projectId(): string {
      return this.$route.params.id;
    },
    annotationRuleTypeService(): any {
      return this.$repositories.annotationRuleType;
    },
    annotationRuleService(): any {
      return this.$services.annotationRule;
    },
    votingConfigurationService(): any {
      return this.$services.votingConfiguration;
    },
  },

  async fetch() {
    this.annotationRuleTypes = await this.$repositories.annotationRuleType.list(this.projectId);
    const votingConfigs = await this.votingConfigurationService.list(this.projectId);
    if (votingConfigs.length > 0) {
      this.votingConfigurationId = votingConfigs[0].id; // Assuming only one voting config per project for now
    }
  },

  methods: {
    async save() {
      try {
        const projectId = Number(this.projectId);
        const annotationRuleTypeId = this.editedItem.annotation_rule_type;

        // 1. Save Voting Configuration
        // Ensure the editedItem has all necessary voting config fields filled from FormCreate
        const votingConfigPayload = {
            project: projectId,
            annotation_rule_type: annotationRuleTypeId,
            voting_threshold: this.editedItem.voting_threshold,
            begin_date: this.editedItem.begin_date,
            end_date: this.editedItem.end_date,
        };

        // You might need to create the voting configuration first if it doesn't exist
        // For simplicity here, we assume it might be created or updated via a single endpoint
        // based on your backend implementation. If not, adjust this part.
        // A more robust approach would check if a config exists and either create or update.

        // Assuming votingConfigId is fetched in fetch() or create a new one if needed
        if (this.votingConfigurationId === 0) {
             const newVotingConfig = await this.votingConfigurationService.create(this.projectId, votingConfigPayload);
             this.votingConfigurationId = newVotingConfig.id;
        } else {
            // If updating existing config, you might need an update method in your service/repository
             // await this.votingConfigurationService.update(this.projectId, this.votingConfigurationId, votingConfigPayload);
             // For now, we proceed assuming either a new one is created or the ID is valid.
        }


        // 2. Save Annotation Rules
        for (const rule of this.annotationRulesList) {
          await this.annotationRuleService.create(this.projectId, {
            project: projectId,
            description: rule.description, // Description from the rule object
            voting_configuration: this.votingConfigurationId, // Link to the saved voting config
            annotation_rule_type: annotationRuleTypeId, // Link to the selected rule type
          });
        }

        this.sucessMessage = 'Regras de anotação guardadas com sucesso.';
        setTimeout(() => {
          this.$router.push(`/projects/${this.projectId}/rules`);
        }, 1000);
      } catch (error) {
        this.handleError(error);
      }
    },
    handleError(error: any) {
      if (error.response && error.response.status === 400) {
        this.errorMessage = 'Erro ao guardar as regras de anotação.';
      } else {
        this.errorMessage = 'A base de dados está lenta ou indisponível. Por favor, tente novamente mais tarde.';
      }
    },
  },
});
</script>