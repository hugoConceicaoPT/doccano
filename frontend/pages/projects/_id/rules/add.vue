<template>
  <div>
    <v-alert v-if="sucessMessage" type="success" dismissible>{{ sucessMessage }}</v-alert>
    <v-alert v-if="errorMessage" type="error" dismissible>{{ errorMessage }}</v-alert>
    <form-create 
      v-slot="slotProps" 
      :editedItem.sync="editedItem" 
      :annotationRuleTypes="annotationRuleTypes"
      :annotationRulesList.sync="annotationRulesList"
      :examples="filteredExamples"
      :loadingExamples="loadingExamples"
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

  middleware: ['check-auth', 'auth', 'setCurrentProject', 'isProjectAdmin'],

  data() {
    return {
      sucessMessage: '',
      errorMessage: '',
      editedItem: {
        project: 0,
        description: '',
        voting_configuration: 0,
        annotation_rule_type: 0,
        example: 0,
        voting_threshold: 0,
        percentage_threshold: 0.0,
        boolean_threshold: false,
        created_by: 0,
        begin_date: '',
        end_date: '',
      } as CreateVotingConfigurationCommand,
      annotationRuleTypes: [] as AnnotationRuleTypeDTO[],
      annotationRulesList: [] as CreateAnnotationRuleCommand[],
      votingConfigurationId: 0,
      usedExamples: [] as number[],
      examples: [] as any[],
      loadingExamples: false,
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
    filteredExamples(): any[] {
      return this.examples.filter(example => !this.usedExamples.includes(example.id));
    },
  },

  async fetch() {
    this.annotationRuleTypes = await this.$repositories.annotationRuleType.list(this.projectId);
    
    // Buscar exemplos já utilizados em configurações de votação
    const votingConfigs = await this.votingConfigurationService.list(this.projectId);
    this.usedExamples = votingConfigs.map((config: { example: number | null }) => config.example).filter((example: number | null) => example !== null);

    // Carregar exemplos
    await this.loadExamples();
  },

  methods: {
    async loadExamples() {
      try {
        this.loadingExamples = true;
        const response = await this.$repositories.example.list(this.projectId, {
          limit: '100',
          offset: '0',
          q: '',
          isChecked: '',
          ordering: ''
        });
        this.examples = response.items;
      } catch (error) {
        console.error('Erro ao carregar exemplos:', error);
      } finally {
        this.loadingExamples = false;
      }
    },
    async save() {
      try {
        const projectId = Number(this.projectId);
        const annotationRuleTypeId = this.editedItem.annotation_rule_type;

        // 1. Save Voting Configuration
        const votingConfigPayload = {
          project: projectId,
          annotation_rule_type: annotationRuleTypeId,
          example: this.editedItem.example,
          voting_threshold: this.editedItem.voting_threshold,
          percentage_threshold: this.editedItem.percentage_threshold,
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