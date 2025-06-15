<template>
  <div>
    <!-- Mensagem de erro no topo -->
    <v-alert 
      v-if="errorMessage" 
      type="error" 
      dismissible
      @input="errorMessage = ''"
      class="mb-4"
      outlined
    >
      <strong>Erro ao criar perspectiva:</strong> {{ errorMessage }}
    </v-alert>

    <!-- Mensagem de sucesso -->
    <v-alert 
      v-if="sucessMessage" 
      type="success" 
      dismissible
      class="mb-4"
      outlined
    >
      <strong>Perspectiva criada com sucesso!</strong> {{ sucessMessage }}
    </v-alert>

    <!-- Componente principal -->
    <form-create
      v-slot="slotProps"
      v-bind.sync="editedItem"
      :perspective-id="null"
      :items="items"
      @update-questions="updateQuestions"
      @update-name="updateName"
      @update-options-group="updateOptionsGroup"
    >
      <!-- Botões de ação -->
      <div class="d-flex justify-space-between align-center mt-6">
        <v-btn 
          color="grey" 
          @click="$router.back()"
          outlined
          class="px-6"
        >
          <v-icon left>mdi-arrow-left</v-icon>
          Cancelar
        </v-btn>
        
        <v-btn 
          :disabled="!slotProps.valid" 
          :loading="saving"
          color="primary" 
          @click="save"
          class="px-6"
          elevation="2"
        >
          <v-icon left>mdi-content-save</v-icon>
          Criar Perspectiva
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
        <p class="mt-4 white--text">A criar perspectiva...</p>
      </div>
    </v-overlay>
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
      items: [] as PerspectiveDTO[],
      saving: false
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
      this.saving = true
      this.errorMessage = ''
      
      try {
        this.editedItem.project_id = Number(this.projectId)
        this.editedItem.members = await this.getAnnotatorIds()

        await this.service.create(this.projectId, this.editedItem)
        
        this.sucessMessage = 'A perspectiva foi criada com sucesso'
        
        // Aguardar um pouco para mostrar a mensagem de sucesso
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
        console.error('Erro ao buscar anotadores:', error)
        return []
      }
    },

    handleError(error: any) {
      console.error('Erro ao criar perspectiva:', error)
      
      if (error.response) {
        switch (error.response.status) {
          case 400:
            this.errorMessage = 'Este projeto já tem uma perspectiva criada. Apenas uma perspectiva é permitida por projeto.'
            break
          case 403:
            this.errorMessage = 'Você não tem permissão para criar perspectivas neste projeto.'
            break
          case 500:
            this.errorMessage = 'Database is slow or unavailable. Please try again later.'
            break
          default:
            this.errorMessage = 'Ocorreu um erro inesperado. Tente novamente.'
        }
      } else if (error.message) {
        this.errorMessage = error.message
      } else {
        this.errorMessage = 'Erro de conexão. Verifique sua internet e tente novamente.'
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
