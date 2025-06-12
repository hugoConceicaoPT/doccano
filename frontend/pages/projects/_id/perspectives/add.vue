<template>
  <div>
    <v-alert v-if="sucessMessage" type="success" dismissible>{{ sucessMessage }}</v-alert>
    <form-create
      v-slot="slotProps"
      v-bind.sync="editedItem"
      :perspective-id="null"
      :items="items"
      @update-questions="updateQuestions"
      @update-name="updateName"
      @update-options-group="updateOptionsGroup"
    >
      <v-btn color="error" class="text-capitalize" @click="$router.back()"> Cancel </v-btn>
      <v-btn :disabled="!slotProps.valid" color="primary" class="text-capitalize" @click="save">
        Save
      </v-btn>
    </form-create>
    <v-alert v-if="errorMessage" type="error" dismissible>{{ errorMessage }}</v-alert>
  </div>
</template>

<script lang="ts">
import Vue from 'vue'
import FormCreate from '~/components/perspective/FormCreate.vue'
import { CreatePerspectiveCommand } from '~/services/application/perspective/perspectiveCommand'
import { PerspectiveDTO } from '~/services/application/perspective/perspectiveData'
import { CreateOptionsGroupCommand } from '~/services/application/perspective/question/questionCommand'
import {
  OptionsGroupDTO,
  QuestionDTO
} from '~/services/application/perspective/question/questionData'

export default Vue.extend({
  components: {
    FormCreate
  },

  layout: 'projects',

  middleware: ['check-auth', 'auth', 'setCurrentProject'],

  data() {
    return {
      editedItem: {
        id: null,
        name: '',
        project_id: 0,
        questions: [],
        members: []
      } as CreatePerspectiveCommand,

      optionsGroupItem: [
        {
          name: '',
          options_questions: []
        }
      ] as CreateOptionsGroupCommand[],



      defaultItem: {
        id: null,
        name: '',
        project_id: 0,
        questions: [],
        members: []
      } as CreatePerspectiveCommand,

      errorMessage: '',
      sucessMessage: '',
      items: [] as PerspectiveDTO[]
    }
  },

  computed: {
    projectId(): string {
      return this.$route.params.id
    },

    service(): any {
      return this.$services.perspective
    }
  },

  methods: {
    updateQuestions(questions: QuestionDTO[]) {
      this.editedItem.questions = questions
    },

    updateName(name: string) {
      this.editedItem.name = name
    },

    updateOptionsGroup(optionsGroup: OptionsGroupDTO[]) {
      this.optionsGroupItem = optionsGroup
    },

    async save() {
      try {
        this.editedItem.project_id = Number(this.projectId)
        this.editedItem.members = await this.getAnnotatorIds();
        
        // Agora todas as perguntas são "Open Questions" com answer_type
        // Não precisamos mais de lógica para QuestionType ou OptionsGroup
        
        await this.service.create(this.projectId, this.editedItem)
        this.sucessMessage = 'A perspective has been successfully added to this project and an email has been sent to all annotators of the project'
        setTimeout(() => {
          this.$router.push(`/projects/${this.projectId}/perspectives`)
        }, 1000)
      } catch (error) {
        this.handleError(error)
      }
    },
    async getAnnotatorIds(): Promise<number[]> {
      const members = await this.$repositories.member.list(this.projectId)
      return members.filter((member) => member.rolename === 'annotator').map((member) => member.id)
    },
    handleError(error: any) {
      this.editedItem = Object.assign({}, this.defaultItem)
      console.error('Error creating perspective:', error)
      if (error.response && error.response.status === 400) {
        this.errorMessage = 'Este projeto já tem uma perspectiva criada. Apenas uma perspectiva é permitida por projeto.'
      } else {
        this.errorMessage = 'Database is slow or unavailable. Please try again later.'
      }
    }
  }
})
</script>
