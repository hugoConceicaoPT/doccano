<template>
  <div>
    <v-alert v-if="errorMessage" type="error" dismissible @input="errorMessage = ''">{{ errorMessage }}</v-alert>
    <v-card>
      <v-card-title>Create Perspective</v-card-title>
      <v-card-text>
        <v-form ref="form">
          <v-row>
            <v-col cols="12">
              <v-text-field v-model="name" label="Add a Name" outlined required :rules="[rules.required]"/>
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
              <v-radio-group v-model="questionType.id" row>
                <v-radio label="Open Question" :value="1"></v-radio>
                <v-radio label="Multiple Choice Question" :value="2"></v-radio>
              </v-radio-group>
            </v-col>
          </v-row>

          <v-row v-if="questionType.id === 2">
            <v-col cols="12">
              <v-combobox v-model="optionGroupName" :items="optionGroupNames" label="Option Group Name" outlined
                @input="loadOptionsFromGroup"></v-combobox>
            </v-col>
            <v-col cols="12">
              <v-text-field v-model="newOption" label="Add an Option" outlined @keyup.enter="addOption" />
              <v-btn color="primary" @click="addOption">Add Option</v-btn>
            </v-col>
            <v-col cols="12">
              <v-list dense>
                <v-list-item v-for="(option, index) in optionsQuestionList" :key="index">
                  <v-list-item-content>
                    <v-list-item-title>{{ option.option }}</v-list-item-title>
                  </v-list-item-content>
                  <v-list-item-action>
                    <v-btn icon color="red" @click="removeOption(index)">
                      <v-icon>{{ mdiDelete }}</v-icon>
                    </v-btn>
                  </v-list-item-action>
                </v-list-item>
              </v-list>
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
                        getQuestionType(question.type)
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
  CreateQuestionCommand,
  CreateOptionsGroupCommand,
  CreateOptionsQuestionCommand
} from '~/services/application/perspective/question/questionCommand'

interface QuestionType {
  id: number
  question_type: string
}

export default Vue.extend({
  data() {
    return {
      name:'',
      newQuestion: '',
      questionType: { id: 1, question_type: 'Open Question' } as QuestionType,
      optionGroupName: '',
      optionGroupNames: [] as string[],
      newOption: '',
      rules: {
        required: (v: string) => !!v || 'Required',
      },
      questionsList: [] as CreateQuestionCommand[],
      optionsGroupList: [] as CreateOptionsGroupCommand[],
      optionsQuestionList: [] as CreateOptionsQuestionCommand[],
      errorMessage: '',
      mdiDelete
    }
  },
  computed: {
    projectId(): string {
      return this.$route.params.id
    },

    isFormValid(): boolean {
      return this.questionsList.length > 0
    },
  },
  mounted() {
    this.fetchOptionGroupName()
  },
  methods: {

    async fetchOptionGroupName() {
      const optionsGroup = await this.$services.optionsGroup.list(this.projectId)
      this.optionGroupNames = optionsGroup.map(optionsGroup => optionsGroup.name)
    },

    async loadOptionsFromGroup() {
      if (this.optionGroupName && this.optionGroupName.trim()) {
        const groupOptions = await this.$services.optionsGroup.findByName(this.projectId, this.optionGroupName)
        if (!groupOptions) return 
        const optionsQuestions = await this.$services.optionsQuestion.list(this.projectId)
        this.optionsQuestionList = optionsQuestions.filter(optionQuestion => optionQuestion.options_group === groupOptions.id)
      }
    },

    getQuestionType(type: number): string {
      const types: { [key: number]: string } = {
        1: 'Open Question',
        2: 'Multiple Choice Question'
      }
      return types[type] || 'Unknown'
    },

    addOption() {
      if (this.newOption.trim()) {
        const newOptionObject: CreateOptionsQuestionCommand = {
          option: this.newOption.trim()
        }
        this.optionsQuestionList.push(newOptionObject)
        this.newOption = ''
      }
    },
    removeOption(index: number) {
      this.optionsQuestionList.splice(index, 1)
    },
    addQuestion() {
      this.errorMessage = ''
      if (!this.newQuestion.trim()) {
        this.errorMessage = "The question cannot be empty"
        return
      }
      const questionData: CreateQuestionCommand = {
        question: this.newQuestion.trim(),
        type: this.questionType.id,
        options_group: undefined,
        answers: []
      }
      let optionsGroupData: CreateOptionsGroupCommand = { name: '', options_questions: [] }

      if (this.questionType.id === 2) {
        if (!this.optionGroupName || !this.optionGroupName.trim()) {
          this.errorMessage = "The option group name is required for multiple choice questions."
          return
        }
        if (this.optionsQuestionList.length === 0) {
          this.errorMessage = "Please add at least one option for the multiple choice question."
          return
        }
        optionsGroupData = {
          name: this.optionGroupName,
          options_questions: this.optionsQuestionList
        }
        this.optionsGroupList.push(optionsGroupData)
        this.emitUpdatedOptionsGroup()
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
    },
    emitUpdatedOptionsGroup() {
      this.$emit('update-options-group', this.optionsGroupList)
    },
    resetForm() {
      this.newQuestion = ''
      this.questionType = { id: 1, question_type: 'Open Question' }
      this.optionGroupName = ''
      this.newOption = ''
      this.optionsGroupList = []
      this.optionsQuestionList = []
    }
  },
})
</script>
