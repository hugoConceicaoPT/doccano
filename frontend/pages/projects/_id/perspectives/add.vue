<template>
  <div>
    <!-- Mensagem de sucesso -->
    <v-alert 
      v-if="sucessMessage" 
      type="success" 
      dismissible
      class="mb-4"
      border="left"
      colored-border
    >
      <div class="d-flex align-center">
        <v-icon color="success" class="mr-3">mdi-check-circle</v-icon>
        <div>
          <strong>Perspectiva criada com sucesso!</strong><br>
          {{ sucessMessage }}
        </div>
      </div>
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
      <div class="d-flex justify-space-between align-center mt-4">
        <v-btn 
          color="grey darken-1" 
          @click="$router.back()"
          text
          class="text-capitalize"
        >
          <v-icon left>mdi-arrow-left</v-icon>
          Cancelar
        </v-btn>
        
        <v-btn 
          :disabled="!slotProps.valid" 
          :loading="saving"
          color="primary" 
          @click="save"
          class="text-capitalize"
        >
          <v-icon left>mdi-content-save</v-icon>
          Criar Perspectiva
        </v-btn>
      </div>
    </form-create>

    <!-- Mensagem de erro -->
    <v-alert 
      v-if="errorMessage" 
      type="error" 
      dismissible
      @input="errorMessage = ''"
      class="mt-4"
      border="left"
      colored-border
    >
      <div class="d-flex align-center">
        <v-icon color="error" class="mr-3">mdi-alert-circle</v-icon>
        <div>
          <strong>Erro ao criar perspectiva</strong><br>
          {{ errorMessage }}
        </div>
      </div>
    </v-alert>

    <!-- Loading overlay simples -->
    <v-overlay :value="saving">
      <v-progress-circular
        indeterminate
        size="64"
        color="primary"
      ></v-progress-circular>
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
        
        this.sucessMessage = 'A perspectiva foi criada com sucesso e um email foi enviado para todos os anotadores do projeto.'
        
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
            this.errorMessage = 'Erro interno do servidor. Tente novamente mais tarde.'
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
.add-perspective-page {
  min-height: 100vh;
  background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
  padding: 20px 0;
}

.action-buttons {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 16px;
  margin-top: 24px;
}

.action-btn {
  font-weight: 600;
  text-transform: none;
  letter-spacing: 0.5px;
  min-width: 140px;
}

.cancel-btn {
  border: 2px solid #757575;
}

.cancel-btn:hover {
  background-color: #f5f5f5;
}

.save-btn {
  background: linear-gradient(45deg, #1976d2 30%, #42a5f5 90%);
  color: white;
  box-shadow: 0 3px 5px 2px rgba(25, 118, 210, 0.3);
}

.save-btn:hover {
  box-shadow: 0 6px 10px 4px rgba(25, 118, 210, 0.3);
  transform: translateY(-1px);
}

.save-btn:disabled {
  background: #e0e0e0 !important;
  color: #9e9e9e !important;
  box-shadow: none !important;
  transform: none !important;
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
