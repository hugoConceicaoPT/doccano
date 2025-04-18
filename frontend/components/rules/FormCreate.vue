<template>
    <v-card>
      <v-card-title>Configurar Votação e Adicionar Regras de Anotação</v-card-title>
      <v-card-text>
        <v-form ref="form" v-model="valid">
          <v-select
            :items="annotationRuleTypes"
            item-text="annotation_rule_type"
            item-value="id"
            label="Tipo de Regra de Anotação"
            :rules="[rules.required]"
            :disabled="annotationRuleTypes.length === 0"
            :value="editedItem.annotation_rule_type"
            @input="$emit('update:editedItem', { ...editedItem, annotation_rule_type: Number($event) })"
          ></v-select>
          <v-text-field
            label="Limite de Votos"
            type="number"
            :value="editedItem.voting_threshold"
            @input="$emit('update:editedItem', { ...editedItem, voting_threshold: Number($event) })"
          ></v-text-field>
          <v-text-field
            label="Data de Início"
            type="datetime-local"
            :rules="[rules.required]"
            :value="editedItem.begin_date"
            @input="$emit('update:editedItem', { ...editedItem, begin_date: $event })"
          ></v-text-field>
          <v-text-field
            label="Data de Fim"
            type="datetime-local"
            :rules="[rules.required, rules.isAfter(editedItem.begin_date)]"
            :value="editedItem.end_date"
            @input="$emit('update:editedItem', { ...editedItem, end_date: $event })"
          ></v-text-field>
  
          <v-divider class="my-4"></v-divider>
  
          <v-card-subtitle>Regras de Anotação</v-card-subtitle>
  
          <v-textarea
            v-if="ruleInputType === 'multiple'"
            :value="globalRulesText"
            label="Regras de Anotação (uma por linha)"
            outlined
            @input="$emit('update-global-rules', $event)"
          ></v-textarea>
          <v-text-field
            v-else
            :value="uniqueRules[0]"
            label="Regra de Anotação Única"
            outlined
            @input="$emit('update-unique-rules', { index: 0, value: $event })"
          ></v-text-field>
  
          <v-list dense v-if="ruleInputType === 'multiple' && globalRulesArray.length">
             <v-subheader>Regras Adicionadas:</v-subheader>
             <v-list-item v-for="(rule, index) in globalRulesArray" :key="index">
                <v-list-item-content>
                   <v-list-item-title>{{ rule }}</v-list-item-title>
                </v-list-item-content>
             </v-list-item>
          </v-list>
  
  
          <slot :valid="valid && isRuleInputValid" />
        </v-form>
      </v-card-text>
    </v-card>
  </template>
  
  <script lang="ts">
  import Vue from 'vue';
  import { CreateVotingConfigurationCommand } from '~/services/application/rules/ruleCommand';
  import { AnnotationRuleTypeDTO } from '~/services/application/rules/ruleData';
  
  export default Vue.extend({
    props: {
      editedItem: {
        type: Object as () => CreateVotingConfigurationCommand,
        required: true,
      },
      annotationRuleTypes: {
        type: Array as () => AnnotationRuleTypeDTO[],
        required: true,
      },
      globalRulesText: {
        type: String,
        default: '',
      },
      uniqueRules: {
        type: Array as () => string[],
        default: () => [''],
      },
    },
  
    data() {
      return {
        valid: false,
        rules: {
          required: (value: any) => !!value || 'Campo obrigatório.',
          integer: (value: any) => Number.isInteger(value) || 'Deve ser um número inteiro.',
          min: (min: number) => (value: number) => value >= min || `Deve ser maior ou igual a ${min}.`,
          isAfter: (startDate: any) => (endDate: any) => {
            if (!startDate || !endDate) return true;
            return new Date(endDate).getTime() > new Date(startDate).getTime() || 'A data de fim deve ser posterior à data de início.';
          },
        },
        ruleInputType: 'unique', // Default value for rule input
      };
    },
  
    computed: {
      isRuleInputValid(): boolean {
        if (this.ruleInputType === 'multiple') {
           // Check if globalRulesText is not empty and contains at least one non-empty line
          return this.globalRulesText.trim().split('\n').some(line => line.trim().length > 0);
        } else { // unique
          return this.uniqueRules[0].trim().length > 0;
        }
      },
       globalRulesArray(): string[] {
         if (this.ruleInputType === 'multiple' && this.globalRulesText) {
           return this.globalRulesText.split('\n').map(line => line.trim()).filter(line => line.length > 0);
         }
         return [];
       }
    },
  
    watch: {
      'editedItem.annotation_rule_type': {
        handler(newVal) {
          // Logic to determine rule input type based on selected annotation_rule_type
          // You need to adjust this based on your specific annotation rule types
          // Example: Assuming annotation_rule_type with ID 1 means Multiple rules
          if (newVal === 1) {
            this.ruleInputType = 'multiple';
          } else { // Default to unique input for other types
            this.ruleInputType = 'unique';
          }
          // Reset rule input fields when type changes
          this.$emit('update-global-rules', '');
          this.$emit('update-unique-rules', ['']);
        },
        immediate: true, // Run the handler immediately on component creation
      },
    },
  
    methods: {
      handleAnnotationRuleTypeChange(event: number) {
        this.$emit('update:editedItem', { ...this.editedItem, annotation_rule_type: Number(event) });
         // Watcher for editedItem.annotation_rule_type will handle ruleInputType update and reset
      },
    },
  });
  </script>