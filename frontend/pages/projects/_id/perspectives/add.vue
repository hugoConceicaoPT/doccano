<template>
  <div>
    <!-- Mensagem de erro no topo -->
    <v-alert 
      v-if="errorMessage" 
      type="error" 
      dismissible
      class="mb-4"
      outlined
      @input="errorMessage = ''"
    >
      <strong>Error creating perspective:</strong> {{ errorMessage }}
    </v-alert>

    <!-- Mensagem de sucesso -->
    <v-alert 
      v-if="sucessMessage" 
      type="success" 
      dismissible
      class="mb-4"
      outlined
    >
      <strong>Perspective created successfully!</strong> {{ sucessMessage }}
    </v-alert>

    <!-- Componente principal -->
    <form-create
      v-slot="slotProps"
      v-bind.sync="editedItem"
      :perspective-id="null"
      :items="items"
      @update-questions="updateQuestions"
      @update-name="updateName"
    >
      <!-- Botões de ação -->
      <div class="d-flex justify-space-between align-center mt-6">
        <v-btn 
          color="grey" 
          outlined
          class="px-6"
          @click="$router.back()"
        >
          <v-icon left>mdi-arrow-left</v-icon>
          Cancel
        </v-btn>
        
        <v-btn 
          :disabled="!slotProps.valid" 
          :loading="saving"
          color="primary" 
          class="px-6"
          elevation="2"
          @click="save"
        >
          <v-icon left>mdi-content-save</v-icon>
          Create Perspective
        </v-btn>
      </div>
    </form-create>

    <!-- Loading overlay -->
    <v-overlay :value="saving">
      <div class="text-center">
        <v-progress-circular
          indeterminate
          size="64"
          color="primary"
          width="4"
        ></v-progress-circular>
        <p class="mt-4 white--text">Creating perspective...</p>
      </div>
    </v-overlay>
  </div>
</template>

<script lang="ts">
// @ts-nocheck
import Vue from 'vue'
import FormCreate from '~/components/perspective/FormCreate.vue'
import { CreatePerspectiveCommand } from '~/services/application/perspective/perspectiveCommand'
import { PerspectiveDTO } from '~/services/application/perspective/perspectiveData'
import {
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


      defaultItem: {
        id: null,
        name: '',
        project_id: 0,
        questions: [],
        members: []
      } as CreatePerspectiveCommand,

      errorMessage: '',
      sucessMessage: '',
      items: [] as PerspectiveDTO[],
      saving: false
    }
  },

  head() {
    return {
      title: 'Create Perspective'
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

    async save() {
      this.saving = true
      this.errorMessage = ''
      
      try {
        this.editedItem.project_id = Number(this.projectId)
        this.editedItem.members = await this.getAnnotatorIds()

        await this.service.create(this.projectId, this.editedItem)
        
        this.sucessMessage = 'The perspective was created successfully'
        
        // Wait a bit to show the success message
        setTimeout(() => {
          this.$router.push(`/projects/${this.projectId}/perspectives`)
        }, 2000)
        
      } catch (error) {
        this.handleError(error)
      } finally {
        this.saving = false
      }
    },

    async getAnnotatorIds(): Promise<number[]> {
      try {
        const members = await this.$repositories.member.list(this.projectId)
        return members.filter((member) => member.rolename === 'annotator').map((member) => member.id)
      } catch (error) {
        console.error('Error fetching annotators:', error)
        return []
      }
    },

    handleError(error: any) {
              console.error('Error creating perspective:', error)
      
      if (error.response) {
        switch (error.response.status) {
          case 400:
            this.errorMessage = 'This project already has a perspective created. Only one perspective is allowed per project.'
            break
          case 403:
            this.errorMessage = 'You do not have permission to create perspectives in this project.'
            break
          case 500:
            this.errorMessage = 'Database is slow or unavailable. Please try again later.'
            break
          default:
            this.errorMessage = 'An unexpected error occurred. Please try again.'
        }
      } else if (error.message) {
        this.errorMessage = error.message
      } else {
        this.errorMessage = 'Connection error. Check your internet and try again.'
      }
    }
  }
})
</script>

<style scoped>
.v-btn {
  text-transform: none;
  font-weight: 500;
  border-radius: 8px;
}

.v-alert {
  border-radius: 8px;
}

/* Responsividade */
@media (max-width: 768px) {
  .add-perspective-page {
    padding: 16px 0;
  }
  
  .action-buttons {
    flex-direction: column-reverse;
    gap: 12px;
  }
  
  .action-btn {
    width: 100%;
    min-width: unset;
  }
}

/* Animações */
.action-btn {
  transition: all 0.3s ease;
}

.v-alert {
  animation: slideInDown 0.5s ease-out;
}

@keyframes slideInDown {
  from {
    opacity: 0;
    transform: translateY(-20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}
</style>
