<template>
    <v-card>
      <v-card-title>Configure Voting and Add Annotation Rules</v-card-title>
      <v-card-text>
        <v-form ref="form" v-model="valid">
          <v-text-field
            label="Vote Threshold"
            type="number"
            :value="editedItem.voting_threshold"
            :rules="[rules.required, rules.min(0)]"
            @input="$emit('update:editedItem', { ...editedItem, voting_threshold: Number($event) })"
          ></v-text-field>

          <v-text-field
            label="Percentage Threshold"
            type="number"
            step="0.01"
            min="0"
            max="100"
            :value="editedItem.percentage_threshold"
            :rules="[rules.required, rules.min(0), rules.max(100)]"
            @input="$emit('update:editedItem', { ...editedItem, percentage_threshold: Number($event) })"
          ></v-text-field>

          <v-text-field
            label="Start Date"
            type="datetime-local"
            :rules="[rules.required]"
            :value="editedItem.begin_date"
            @input="$emit('update:editedItem', { ...editedItem, begin_date: $event })"
          ></v-text-field>
          <v-text-field
            label="End Date"
            type="datetime-local"
            :rules="[rules.required, rules.isAfter(editedItem.begin_date)]"
            :value="editedItem.end_date"
            @input="$emit('update:editedItem', { ...editedItem, end_date: $event })"
          ></v-text-field>

          <v-text-field
            label="Versão"
            :value="editedItem.version"
            readonly
            disabled
            hint="A versão é determinada automaticamente pelo sistema"
            persistent-hint
          >
            <template v-slot:prepend>
              <v-tooltip bottom>
                <template v-slot:activator="{ on }">
                  <v-icon small v-on="on">mdi-information-outline</v-icon>
                </template>
                <span>A versão é incrementada automaticamente com base nas versões existentes</span>
              </v-tooltip>
            </template>
          </v-text-field>
  
          <v-divider class="my-4"></v-divider>
  
          <v-card-subtitle>Add Annotation Rules</v-card-subtitle>
  
          <v-row>
            <v-col cols="12">
              <v-text-field
                v-model="newRuleName"
                label="Rule Name"
                outlined
                :rules="[rules.requiredIfNoRules(annotationRulesList)]"
                class="mb-4"
              ></v-text-field>
            </v-col>
          </v-row>

          <v-row>
            <v-col cols="12">
              <v-btn color="primary" @click="addRule">Add Rule</v-btn>
            </v-col>
          </v-row>

          <v-row v-if="annotationRulesList.length > 0">
            <v-col cols="12">
              <v-list dense>
                <v-list-item-group>
                  <v-list-item v-for="(rule, index) in annotationRulesList" :key="index">
                    <v-list-item-content>
                      <v-list-item-title>
                        <strong>{{ rule.name }}</strong>
                      </v-list-item-title>
                    </v-list-item-content>
                    <v-list-item-action>
                      <v-btn icon color="red" @click="removeRule(index)">
                        Delete
                      </v-btn>
                    </v-list-item-action>
                  </v-list-item>
                </v-list-item-group>
              </v-list>
            </v-col>
          </v-row>
  
          <slot :valid="isFormValid" />
        </v-form>
      </v-card-text>
    </v-card>
  </template>
  
  <script lang="ts">
  import Vue from 'vue';
  import { CreateVotingConfigurationCommand, CreateAnnotationRuleCommand } from '~/services/application/rules/ruleCommand';
  
  export default Vue.extend({
    props: {
      editedItem: {
        type: Object as () => CreateVotingConfigurationCommand,
        required: true,
      },
      annotationRulesList: {
        type: Array as () => CreateAnnotationRuleCommand[],
        required: true,
      },
    },
  
    data() {
      return {
        valid: false,
        rules: {
          required: (value: any) => !!value || 'Required field.',
          requiredIf: (otherValue: any) => (value: any) => {
            if (otherValue && !value) return 'Required field when the other field is filled.';
            return true;
          },
          requiredIfNoRules: (rulesList: any[]) => (value: any) => {
            if (rulesList.length === 0 && !value) return 'Required field when there are no rules.';
            return true;
          },
          integer: (value: any) => Number.isInteger(value) || 'Must be an integer.',
          min: (min: number) => (value: number) => value >= min || `Must be greater than or equal to ${min}.`,
          max: (max: number) => (value: number) => value <= max || `Must be less than or equal to ${max}.`,
          isAfter: (startDate: any) => (endDate: any) => {
            if (!startDate || !endDate) return true;
            return new Date(endDate).getTime() > new Date(startDate).getTime() || 'End date must be after start date.';
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
        return this.valid && (this.annotationRulesList.length > 0 || this.newRuleName.trim() !== '');
      }
    },
  
    methods: {
      addRule() {
        if (this.newRuleName.trim()) {
          const newRule: CreateAnnotationRuleCommand = {
            project: this.editedItem.project,
            name: this.newRuleName.trim(),
            description: 'NULO',
            voting_configuration: 0,
            final_result: '',
            is_finalized: false
          };
          const updatedRulesList = [...this.annotationRulesList, newRule];
          this.$emit('update:annotationRulesList', updatedRulesList);
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