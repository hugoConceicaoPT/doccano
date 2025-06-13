<template>
  <div>
    <v-alert v-if="errorMessage" type="error" dismissible @input="errorMessage = ''">{{ errorMessage }}</v-alert>
    <v-card>
      <v-card-title>Create Perspective</v-card-title>
      <v-card-text>
        <v-form ref="form">
          <v-row>
            <v-col cols="12">
              <v-text-field v-model="name" label="Nome da Perspectiva" outlined required :rules="[rules.required]"/>
            </v-col>
          </v-row>
          <v-row>
            <v-col cols="12">
              <v-text-field v-model="newQuestion" label="Add a Question" outlined
                @keyup.enter="addQuestion" />
            </v-col>
          </v-row>

          <v-row>
            <v-col cols="12">
              <v-radio-group v-model="answerType" row>
                <v-radio label="Verdadeiro/Falso" value="boolean"></v-radio>
                <v-radio label="Número Inteiro" value="int"></v-radio>
                <v-radio label="Número Decimal" value="double"></v-radio>
                <v-radio label="Texto" value="string"></v-radio>
              </v-radio-group>
            </v-col>
          </v-row>

          <v-row>
            <v-col cols="12">
              <v-btn color="primary" @click="addQuestion">Add Question</v-btn>
            </v-col>
          </v-row>

          <v-row v-if="questionsList.length">
            <v-col cols="12">
              <v-list dense>
                <v-list-item-group>
                  <v-list-item v-for="(question, index) in questionsList" :key="index">
                    <v-list-item-content>
                      <v-list-item-title>{{ question.question }} ({{
                        getAnswerTypeLabel(question.answer_type)
                      }})</v-list-item-title>
                    </v-list-item-content>
                    <v-list-item-action>
                      <v-btn icon color="red" @click="removeQuestion(index)">
                        <v-icon>{{ mdiDelete }}</v-icon>
                      </v-btn>
                    </v-list-item-action>
                  </v-list-item>
                </v-list-item-group>
              </v-list>
            </v-col>
          </v-row>

          <v-row>
            <v-col cols="12">
              <slot :valid="isFormValid" :questionsList="questionsList" />
            </v-col>
          </v-row>
        </v-form>
      </v-card-text>
    </v-card>
  </div>
</template>

<script lang="ts">
import Vue from 'vue'
import { mdiDelete } from '@mdi/js'
import {
  CreateQuestionCommand
} from '~/services/application/perspective/question/questionCommand'

export default Vue.extend({
  data() {
    return {
      name: '',
      newQuestion: '',
      answerType: null as string | null,
      rules: {
        required: (v: string) => !!v || 'Required',
      },
      questionsList: [] as CreateQuestionCommand[],
      errorMessage: '',
      mdiDelete
    }
  },
  computed: {
    projectId(): string {
      return this.$route.params.id
    },

    isFormValid(): boolean {
      return this.questionsList.length > 0 && this.name.trim() !== ''
    },
  },
  methods: {

    getAnswerTypeLabel(answerType: string): string {
      const types: { [key: string]: string } = {
        boolean: 'Verdadeiro/Falso',
        int: 'Número Inteiro',
        double: 'Número Decimal',
        string: 'Texto'
      }
      return types[answerType] || 'Unknown'
    },


    addQuestion() {
      this.errorMessage = ''
      if (!this.newQuestion.trim()) {
        this.errorMessage = "The question cannot be empty"
        return
      }
      if (this.answerType === null) {
        this.errorMessage = "Please select an answer type"
        return
      }
      const questionData: CreateQuestionCommand = {
        question: this.newQuestion.trim(),
        answer_type: this.answerType, // Tipo de resposta selecionado
        options_group: undefined,
        answers: []
      }

      this.questionsList.push(questionData)
      this.emitUpdatedQuestions()
      this.resetForm()
    },
    removeQuestion(index: number) {
      this.questionsList.splice(index, 1)
      this.emitUpdatedQuestions()
    },
    emitUpdatedQuestions() {
      this.$emit('update-questions', this.questionsList)
      this.$emit('update-name', this.name)
    },
    resetForm() {
      this.newQuestion = ''
      this.answerType = null
    }
  },
})
</script>
