<template>
  <div>
    <v-alert v-if="sucessMessage" type="success" dismissible>{{ sucessMessage }}</v-alert>
    <v-alert v-if="errorMessage" type="error" dismissible>{{ errorMessage }}</v-alert>
    <v-alert v-if="hasExistingVotingConfig" type="info" dismissible>
      Configuração de Votação já definida
    </v-alert>
    <form-create 
      v-if="!hasExistingVotingConfig"
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
    <div v-else>
      <v-btn color="error" class="text-capitalize" @click="$router.back()"> Cancelar </v-btn>
    </div>
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

  middleware: ['check-auth', 'auth', 'setCurrentProject', 'isProjectAdmin'],

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
      hasExistingVotingConfig: true, // Booleano para controlar a verificação
      checkExistingConfig: true, // Booleano para ativar/desativar a verificação
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
    
    // Verificar se já existe configuração de votação
    if (this.checkExistingConfig) {
      const votingConfigs = await this.votingConfigurationService.list(this.projectId);
      this.hasExistingVotingConfig = votingConfigs && votingConfigs.length > 0;
    }
  },

  methods: {
    async save() {
      try {
        const projectId = Number(this.projectId);
        const annotationRuleTypeId = this.editedItem.annotation_rule_type;

        // 1. Save Voting Configuration
        const votingConfigPayload = {
          project: projectId,
          annotation_rule_type: annotationRuleTypeId,
          voting_threshold: this.editedItem.voting_threshold,
          created_by: null,
          begin_date: this.editedItem.begin_date,
          end_date: this.editedItem.end_date,
        };

        console.log("Enviando configuração de votação:", votingConfigPayload);

        // Criar a configuração de votação
        await this.votingConfigurationService.create(this.projectId, votingConfigPayload);

        // Buscar o ID da configuração criada
        const votingConfigs = await this.votingConfigurationService.list(this.projectId);
        if (votingConfigs && votingConfigs.length > 0) {
          this.votingConfigurationId = votingConfigs[votingConfigs.length - 1].id;
          console.log("ID da configuração de votação:", this.votingConfigurationId);
        } else {
          throw new Error('Não foi possível obter o ID da configuração de votação');
        }

        // 2. Save Annotation Rules
        for (const rule of this.annotationRulesList) {
          const rulePayload = {
            project: projectId,
            name: rule.name,
            description: rule.description,
            voting_configuration: this.votingConfigurationId,
            annotation_rule_type: annotationRuleTypeId,
          };
          console.log("Enviando regra:", rulePayload);
          await this.annotationRuleService.create(this.projectId, rulePayload);
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