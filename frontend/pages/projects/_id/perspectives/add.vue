<template>
  <form-create
    v-slot="slotProps"
    v-bind.sync="editedItem"
    :perspective-id="null"
    :items="items"
    @update-questions="updateQuestions"
  >
    <v-btn :disabled="!slotProps.valid" color="primary" class="text-capitalize" @click="save">
      Save
    </v-btn>

    <v-btn
      :disabled="!slotProps.valid"
      color="primary"
      style="text-transform: none"
      outlined
      @click="saveAndAnother"
    >
      Save and add another
    </v-btn>
  </form-create>
</template>

<script lang="ts">
import Vue from 'vue'
import FormCreate from '~/components/perspective/FormCreate.vue'
import { CreatePerspectiveCommand } from '~/services/application/perspective/perspectiveCommand'
import { PerspectiveDTO } from '~/services/application/perspective/perspectiveData'
import { QuestionDTO } from '~/services/application/perspective/question/questionData'

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
        project_id: 0,
        questions: [],
        members: []
      } as CreatePerspectiveCommand,

      defaultItem: {
        id: null,
        project_id: 0,
        questions: [],
        members: []
      } as CreatePerspectiveCommand,

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
    async save() {
      this.editedItem.project_id = Number(this.projectId)
      this.editedItem.members = await this.getAnnotatorIds()
      await this.service.create(this.projectId, this.editedItem)
      this.$router.push(`/projects/${this.projectId}/perspectives`)
    },

    async saveAndAnother() {
      this.editedItem.project_id = Number(this.projectId)
      await this.service.create(this.projectId, this.editedItem)
      this.editedItem = Object.assign({}, this.defaultItem)
      this.items = await this.service.list()
    },
    async getAnnotatorIds(): Promise<number[]> {
      const members = await this.$repositories.member.list(this.projectId)
      return members.filter((member) => member.rolename === 'annotator').map((member) => member.id)
    }
  }
})
</script>
