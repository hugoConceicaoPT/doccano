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

          <v-select
            :items="examples"
            item-text="text"
            item-value="id"
            label="Exemplo"
            :rules="[rules.required]"
            :loading="loadingExamples"
            :disabled="loadingExamples"
            :value="editedItem.example"
            @input="$emit('update:editedItem', { ...editedItem, example: Number($event) })"
          ></v-select>

          <v-text-field
            label="Limite de Votos"
            type="number"
            :value="editedItem.voting_threshold"
            :rules="[rules.required, rules.min(0)]"
            @input="$emit('update:editedItem', { ...editedItem, voting_threshold: Number($event) })"
          ></v-text-field>

          <v-text-field
            label="Limite de Percentagem"
            type="number"
            step="0.01"
            min="0"
            max="100"
            :value="editedItem.percentage_threshold"
            :rules="[rules.required, rules.min(0), rules.max(100)]"
            @input="$emit('update:editedItem', { ...editedItem, percentage_threshold: Number($event) })"
          ></v-text-field>

          <v-select
            :items="[
              { text: 'Verdadeiro', value: true },
              { text: 'Falso', value: false }
            ]"
            label="Limite Booleano"
            :value="editedItem.boolean_threshold"
            @input="$emit('update:editedItem', { ...editedItem, boolean_threshold: $event })"
          ></v-select>

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
  
          <v-card-subtitle>Adicionar Regras de Anotação</v-card-subtitle>
  
          <!-- Campo único para tipo 1 -->
          <v-row v-if="editedItem.annotation_rule_type === 1">
            <v-col cols="12">
              <v-text-field
                v-model="newRuleName"
                label="Nome da Regra"
                outlined
                :rules="[rules.requiredIf(newRuleText)]"
                class="mb-4"
              ></v-text-field>
              <v-text-field
                v-model="newRuleText"
                label="Regra de Anotação"
                outlined
                :rules="[rules.requiredIf(newRuleName)]"
                @input="handleSingleRuleInput"
              ></v-text-field>
            </v-col>
          </v-row>
  
          <!-- Múltiplos campos para tipo 2 -->
          <template v-else-if="editedItem.annotation_rule_type === 2">
            <v-row>
              <v-col cols="12">
                <v-text-field
                  v-model="newRuleName"
                  label="Nome da Regra"
                  outlined
                  :rules="[rules.requiredIf(newRuleText)]"
                  class="mb-4"
                ></v-text-field>
                <v-text-field
                  v-model="newRuleText"
                  label="Nova Regra de Anotação"
                  outlined
                  :rules="[rules.requiredIf(newRuleName)]"
                  @keyup.enter="addRule"
                ></v-text-field>
              </v-col>
            </v-row>
  
            <v-row>
              <v-col cols="12">
                <v-btn color="primary" @click="addRule">Adicionar Regra</v-btn>
              </v-col>
            </v-row>
  
            <v-row v-if="annotationRulesList.length">
              <v-col cols="12">
                <v-list dense>
                  <v-list-item-group>
                    <v-list-item v-for="(rule, index) in annotationRulesList" :key="index">
                      <v-list-item-content>
                        <v-list-item-title>
                          <strong>{{ rule.name }}</strong>
                        </v-list-item-title>
                        <v-list-item-subtitle>
                          {{ rule.description }}
                        </v-list-item-subtitle>
                      </v-list-item-content>
                      <v-list-item-action>
                        <v-btn icon color="red" @click="removeRule(index)">
                          <v-icon>mdi-delete</v-icon>
                        </v-btn>
                      </v-list-item-action>
                    </v-list-item>
                  </v-list-item-group>
                </v-list>
              </v-col>
            </v-row>
          </template>
  
          <slot :valid="isFormValid" />
        </v-form>
      </v-card-text>
    </v-card>
  </template>
  
  <script lang="ts">
  import Vue from 'vue';
  import { CreateVotingConfigurationCommand, CreateAnnotationRuleCommand } from '~/services/application/rules/ruleCommand';
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
      annotationRulesList: {
        type: Array as () => CreateAnnotationRuleCommand[],
        required: true,
      },
      examples: {
        type: Array as () => any[],
        required: true,
      },
      loadingExamples: {
        type: Boolean,
        required: true,
      },
    },
  
    data() {
      return {
        valid: false,
        rules: {
          required: (value: any) => !!value || 'Campo obrigatório.',
          requiredIf: (otherValue: any) => (value: any) => {
            if (otherValue && !value) return 'Campo obrigatório quando o outro campo está preenchido.';
            return true;
          },
          integer: (value: any) => Number.isInteger(value) || 'Deve ser um número inteiro.',
          min: (min: number) => (value: number) => value >= min || `Deve ser maior ou igual a ${min}.`,
          max: (max: number) => (value: number) => value <= max || `Deve ser menor ou igual a ${max}.`,
          isAfter: (startDate: any) => (endDate: any) => {
            if (!startDate || !endDate) return true;
            return new Date(endDate).getTime() > new Date(startDate).getTime() || 'A data de fim deve ser posterior à data de início.';
          },
        },
        newRuleText: '',
        newRuleName: '',
      };
    },
  
    watch: {
      editedItem: {
        handler() {
          (this.$refs.form as Vue & { validate: () => boolean })?.validate();
        },
        deep: true,
      },
    },
  
    computed: {
      isFormValid(): boolean {
        if (this.editedItem.annotation_rule_type === 1) {
          return this.valid && this.newRuleText.trim() !== '';
        } else {
          return this.valid && this.annotationRulesList.length > 0;
        }
      }
    },
  
    methods: {
      handleSingleRuleInput(value: string) {
        if (value.trim() && this.newRuleName.trim()) {
          const newRule: CreateAnnotationRuleCommand = {
            project: this.editedItem.project,
            name: this.newRuleName.trim(),
            description: value.trim(),
            voting_configuration: 0,
            annotation_rule_type: this.editedItem.annotation_rule_type,
          };
          this.$emit('update:annotationRulesList', [newRule]);
        } else {
          this.$emit('update:annotationRulesList', []);
        }
      },
  
      addRule() {
        if (this.newRuleText.trim() && this.newRuleName.trim()) {
          const newRule: CreateAnnotationRuleCommand = {
            project: this.editedItem.project,
            name: this.newRuleName.trim(),
            description: this.newRuleText.trim(),
            voting_configuration: 0,
            annotation_rule_type: this.editedItem.annotation_rule_type,
          };
          const updatedRulesList = [...this.annotationRulesList, newRule];
          this.$emit('update:annotationRulesList', updatedRulesList);
          this.newRuleText = '';
          this.newRuleName = '';
        }
      },
      removeRule(index: number) {
        const updatedRulesList = this.annotationRulesList.filter((_, i) => i !== index);
        this.$emit('update:annotationRulesList', updatedRulesList);
      },
    },
  });
  </script>