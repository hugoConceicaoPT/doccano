<template>
  <v-card>
    <v-card-title>Define Perspective</v-card-title>
    <v-card-text>
      <v-form ref="form">
        <v-row>
          <v-col cols="12">
            <v-text-field
              v-model="newQuestion"
              label="Add a Question"
              outlined
              required
              :rules="[rules.required]"
              @keyup.enter="addQuestion"
            />
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
                    <v-list-item-title>{{ question.question }}</v-list-item-title>
                  </v-list-item-content>
                  <v-list-item-action>
                    <v-btn icon color="red" @click="removeQuestion(index)">
                      <v-icon> {{ mdiDelete }}</v-icon>
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
</template>

<script lang="ts">
import Vue from 'vue'
import { mdiDelete } from '@mdi/js'
import { CreateQuestionCommand } from '~/services/application/perspective/question/questionCommand'

export default Vue.extend({
  data() {
    return {
      newQuestion: '',
      questionsList: [] as CreateQuestionCommand[], // Lista para armazenar as perguntas
      rules: {
        required: (v: string) => !!v || 'Required'
      },
      mdiDelete
    }
  },
  computed: {
    isFormValid(): boolean {
      return this.questionsList.length > 0
    }
  },

  methods: {
    addQuestion() {
      if (this.newQuestion.trim()) {
        this.questionsList.push({
          question: this.newQuestion.trim(),
          answers: []
        })
        this.emitUpdatedQuestions()
        this.newQuestion = '' // Limpa o campo após adicionar
      }
    },
    removeQuestion(index: number) {
      this.questionsList.splice(index, 1) // Remove a pergunta pelo índice
      this.emitUpdatedQuestions()
    },

    emitUpdatedQuestions() {
      const formattedQuestions = this.questionsList.map((question, index) => ({
        id: index,
        question: question.question,
        answers: []
      }))

      this.$emit('update-questions', formattedQuestions)
    }
  }
})
</script>
