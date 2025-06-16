<template>
  <v-card>
    <v-card-title>Configure Voting and Add Annotation Rules</v-card-title>
    <v-card-text>
      <v-form ref="form" v-model="internalValid">
        <v-text-field
          label="Maximum Number of Votes"
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
          @input="
            $emit('update:editedItem', { ...editedItem, percentage_threshold: Number($event) })
          "
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
          label="Version"
          :value="editedItem.version"
          readonly
          disabled
          hint="The version is automatically determined by the system"
          persistent-hint
        ></v-text-field>

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
                <!-- eslint-disable-next-line -->
                <v-list-item v-for="(rule, index) in annotationRulesList" :key="index">
                  <v-list-item-content>
                    <v-list-item-title>
                      <strong>{{ rule.name }}</strong>
                    </v-list-item-title>
                  </v-list-item-content>
                  <v-list-item-action>
                    <v-btn icon color="red" @click="removeRule(index)">
                      <v-icon>{{ mdiDelete }}</v-icon>
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
import Vue from 'vue'
import { mdiDelete } from '@mdi/js'

export default Vue.extend({
  props: {
    editedItem: {
      type: Object,
      required: true
    },
    annotationRulesList: {
      type: Array,
      required: true
    },
    valid: {
      type: Boolean,
      default: false
    }
  },

  data() {
    return {
      mdiDelete,
      internalValid: false,
      rules: {
        required: (value: string | number) => {
          return (value !== null && value !== undefined && value !== '') || 'Required field'
        },
        requiredIf: (otherValue: any) => (value: any) => {
          if (otherValue && !value) return 'Required field when the other field is filled.'
          return true
        },
        requiredIfNoRules: (rulesList: any[]) => (value: any) => {
          if (rulesList.length === 0 && !value) return 'Required field when there are no rules.'
          return true
        },
        integer: (value: any) => Number.isInteger(value) || 'Must be an integer.',
        min: (min: number) => (value: number) => {
          return value >= min || `Minimum value is ${min}`
        },
        max: (max: number) => (value: number) => {
          return value <= max || `Maximum value is ${max}`
        },
        isAfter: (startDate: string) => (endDate: string) => {
          if (!startDate || !endDate) return true
          return new Date(endDate) > new Date(startDate) || 'End date must be after start date'
        }
      },
      newRuleText: '',
      newRuleName: ''
    }
  },

  computed: {
    isFormValid(): boolean {
      return this.internalValid && (this.annotationRulesList.length > 0 || this.newRuleName.trim() !== '')
    }
  },

  watch: {
    editedItem: {
      handler() {
        this.validateForm()
      },
      deep: true
    }
  },

  methods: {
    validateForm() {
      this.$nextTick(() => {
        const form = this.$refs.form as any
        if (form && form.validate) {
          this.internalValid = form.validate()
        }
      })
    },
    
    addRule() {
      if (this.newRuleName.trim()) {
        const newRule = {
          project: (this.editedItem as any).project,
          name: this.newRuleName.trim(),
          voting_configuration: 0,
          final_result: '',
          is_finalized: false
        }
        const updatedRulesList = [...(this.annotationRulesList as any[]), newRule]
        this.$emit('update:annotationRulesList', updatedRulesList)
        this.newRuleName = ''
      }
    },
    removeRule(index: number) {
      const updatedRulesList = (this.annotationRulesList as any[]).filter((_, i) => i !== index)
      this.$emit('update:annotationRulesList', updatedRulesList)
    }
  }
})
</script>
