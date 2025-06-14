<template>
  <div>
    <!-- Mensagem de erro movida para o topo -->
    <v-alert v-if="errorMessage" type="error" dismissible class="mb-4" outlined @input="errorMessage = ''">
      {{ errorMessage }}
    </v-alert>
    
    <v-card elevation="1" class="rounded-lg">
      <v-card-title class="primary white--text py-4">
        <v-icon left color="white">mdi-lightbulb-on</v-icon>
        <span class="text-h6">Create Perspective</span>
      </v-card-title>
      
      <v-card-text class="pa-6">
        <v-form ref="form">
          <!-- Seção de seleção de perspectiva -->
          <v-row>
            <v-col cols="12">
              <div class="mb-6">
                <h3 class="text-h6 mb-3 primary--text font-weight-medium">
                  <v-icon color="primary" class="mr-2">mdi-format-title</v-icon>
                  Perspective Name
                </h3>
                
                <v-autocomplete
                  v-model="selectedPerspective"
                  :items="perspectiveOptions"
                  item-text="display"
                  item-value="value"
                  label="Enter the name of the new perspective or select an existing one"
                  outlined
                  required
                  :rules="[rules.required]"
                  :loading="loadingPerspectives"
                  :search-input.sync="searchInput"
                  clearable
                  no-filter
                  prepend-inner-icon="mdi-lightbulb-on"
                  :menu-props="{ maxHeight: 300 }"
                  placeholder="Ex: Quality Perspective, Usability..."
                  class="mt-2"
                  @change="onPerspectiveChange"
                  @input="onPerspectiveInput"
              >
                <template #item="{ item }">
                  <v-list-item-avatar>
                    <v-icon :color="item.isExisting ? 'orange' : 'green'">
                      {{ item.isExisting ? 'mdi-recycle' : 'mdi-plus-circle' }}
                    </v-icon>
                  </v-list-item-avatar>
                  <v-list-item-content>
                    <v-list-item-title>{{ item.display }}</v-list-item-title>
                    <v-list-item-subtitle v-if="item.isExisting">
                      <v-icon small class="mr-1">mdi-folder</v-icon>
                      {{ item.projectName }} • Reuse perspective
                    </v-list-item-subtitle>
                    <v-list-item-subtitle v-else>
                      <v-icon small class="mr-1">mdi-plus</v-icon>
                                              Create new perspective
                    </v-list-item-subtitle>
                  </v-list-item-content>
                </template>
                

              </v-autocomplete>
              


                <!-- Alerta informativo para reutilização -->
                <v-alert 
                  v-if="isReusing && questionsList.length > 0" 
                  type="info" 
                  class="mt-4"
                  outlined
                  dense
                >
                  <div class="d-flex align-center">
                    <v-icon color="info" class="mr-2" small>mdi-information</v-icon>
                    <div>
                      <strong>Perspective reused!</strong>
                      {{ questionsList.length }} question(s) from perspective "{{ selectedExistingPerspectiveName }}" 
                      were loaded.
                    </div>
                  </div>
                </v-alert>
              </div>
            </v-col>
          </v-row>

          <!-- Seção de criação de perguntas (apenas para novas perspectivas) -->
          <div v-if="!isReusing">
            <v-divider class="my-6"></v-divider>
            
            <div class="mb-6">
              <h3 class="text-h6 mb-4 primary--text font-weight-medium">
                <v-icon color="primary" class="mr-2">mdi-help-circle</v-icon>
                Add Questions
              </h3>

              <v-row>
                <v-col cols="12" md="8">
                  <v-text-field
                    v-model="newQuestion"
                    label="Enter your question"
                    outlined
                    prepend-inner-icon="mdi-comment-question"
                    hint="Press Enter to add quickly"
                    persistent-hint
                    dense
                    @keyup.enter="addQuestion"
                  />
                </v-col>
                <v-col cols="12" md="4">
                  <v-select
                    v-model="answerType"
                    :items="answerTypeOptions"
                    label="Answer type"
                    outlined
                    prepend-inner-icon="mdi-format-list-bulleted-type"
                    dense
                  />
                </v-col>
              </v-row>

              <div class="text-center mt-4">
                <v-btn 
                  color="primary" 
                  :disabled="!newQuestion.trim() || !answerType"
                  class="px-6"
                  elevation="1"
                  @click="addQuestion"
                >
                  <v-icon left>mdi-plus</v-icon>
                  Add Question
                </v-btn>
              </div>
            </div>
          </div>

          <!-- Seção de lista de perguntas -->
          <div v-if="questionsList.length" class="mt-6">
            <v-divider class="mb-6"></v-divider>
            
            <div class="d-flex justify-space-between align-center mb-4">
              <h3 class="text-h6 primary--text font-weight-medium">
                <v-icon color="primary" class="mr-2">mdi-format-list-numbered</v-icon>
                Added Questions
                <v-chip small color="primary" text-color="white" class="ml-2">{{ questionsList.length }}</v-chip>
              </h3>
              
              <v-btn
                v-if="!isReusing"
                color="error"
                outlined
                small
                @click="clearAllQuestions"
              >
                <v-icon left small>mdi-delete-sweep</v-icon>
                Clear All
              </v-btn>
            </div>

            <v-card outlined elevation="0" class="mb-4">
              <v-list>
                <template v-for="(question, index) in questionsList">
                  <v-list-item :key="index" class="py-4">
                    <v-list-item-avatar>
                      <v-avatar color="primary" size="36">
                        <span class="white--text font-weight-bold">{{ index + 1 }}</span>
                      </v-avatar>
                    </v-list-item-avatar>
                    
                    <v-list-item-content>
                      <v-list-item-title class="font-weight-medium mb-2">
                        {{ question.question }}
                      </v-list-item-title>
                      <v-list-item-subtitle>
                        <v-chip 
                          small 
                          :color="getAnswerTypeColor(question.answer_type ?? '')"
                          text-color="white"
                          class="font-weight-medium"
                        >
                          <v-icon small left>{{ getAnswerTypeIcon(question.answer_type ?? '') }}</v-icon>
                          {{ getAnswerTypeLabel(question.answer_type ?? '') }}
                        </v-chip>
                      </v-list-item-subtitle>
                    </v-list-item-content>

                    <v-list-item-action class="d-flex flex-row align-center question-actions">
                      <!-- Botão de remoção elegante -->
                      <v-btn 
                        v-if="!isReusing"
                        text
                        color="primary" 
                        small
                        class="delete-btn-modern"
                        title="Remove question"
                        @click="removeQuestion(index)"
                      >
                        <v-icon small class="mr-1">mdi-minus-circle-outline</v-icon>
                        Remover
                      </v-btn>
                      
                      <!-- Chip de status quando reutilizando -->
                      <v-chip v-if="isReusing" small outlined color="orange" text-color="orange darken-2">
                        <v-icon small left>mdi-lock-outline</v-icon>
                        Reutilizada
                      </v-chip>
                    </v-list-item-action>
                  </v-list-item>
                  
                  <v-divider v-if="index < questionsList.length - 1" :key="`divider-${index}`"></v-divider>
                </template>
              </v-list>
            </v-card>
          </div>

          <!-- Slot para botões de ação -->
          <v-row class="mt-4">
            <v-col cols="12">
              <slot :valid="isFormValid" :questionsList="questionsList" />
            </v-col>
          </v-row>
        </v-form>
      </v-card-text>
    </v-card>

    <!-- Diálogo de Confirmação de Remoção -->
    <v-dialog v-model="confirmDialog" persistent max-width="500px">
      <v-card>
        <v-card-title class="primary white--text">
          <v-icon left color="white">mdi-help-circle</v-icon>
          Confirmar Remoção
        </v-card-title>
        <v-card-text class="pt-4">
          <div class="text-center">
            <v-icon size="64" color="primary" class="mb-4">mdi-help-circle-outline</v-icon>
            <p class="text-h6 mb-2">Tem certeza que deseja remover esta pergunta?</p>
            <p class="primary--text mb-2 font-weight-medium">"{{ questionToRemove?.question }}"</p>
            <p class="grey--text">Esta ação não pode ser desfeita.</p>
          </div>
        </v-card-text>
        <v-card-actions class="pa-4">
          <v-spacer />
          <v-btn color="grey" text @click="handleConfirmCancel">
            Cancelar
          </v-btn>
          <v-btn color="primary" @click="handleConfirmOk">
            <v-icon left>mdi-check</v-icon>
            Confirmar
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </div>
</template>

<script lang="ts">
import Vue from 'vue'
import { mdiDelete } from '@mdi/js'
import { CreateQuestionCommand } from '~/services/application/perspective/question/questionCommand'
import { PerspectiveDTO } from '~/services/application/perspective/perspectiveData'

export default Vue.extend({
  data() {
    return {
      newQuestion: '',
      answerType: null as string | null,
      rules: {
        required: (v: string) => !!v || 'Campo obrigatório'
      },
      questionsList: [] as CreateQuestionCommand[],
      errorMessage: '',
      mdiDelete,
      selectedPerspective: null as string | null,
      searchInput: '',
      existingPerspectives: [] as PerspectiveDTO[],
      loadingPerspectives: false,
      selectedExistingPerspectiveData: null as PerspectiveDTO | null,
      // Controle do diálogo de confirmação
      confirmDialog: false,
      questionToRemove: null as CreateQuestionCommand | null,
      questionIndexToRemove: -1,
      answerTypeOptions: [
        { text: 'True/False', value: 'boolean', icon: 'mdi-check-circle', color: 'green' },
        { text: 'Integer Number', value: 'int', icon: 'mdi-numeric', color: 'blue' },
        { text: 'Decimal Number', value: 'double', icon: 'mdi-decimal', color: 'purple' },
        { text: 'Text', value: 'string', icon: 'mdi-text', color: 'orange' }
      ]
    }
  },
  computed: {
    projectId(): string {
      return this.$route.params.id
    },

    isFormValid(): boolean {
      const hasQuestions = this.questionsList.length > 0
      const hasName = typeof this.selectedPerspective === 'string' && this.selectedPerspective.trim() !== ''
      return hasQuestions && hasName
    },
    
    finalName(): string {
      return this.selectedPerspective || ''
    },
    
    isReusing(): boolean {
      return this.selectedExistingPerspectiveData !== null
    },
    
    selectedExistingPerspectiveName(): string {
      return this.selectedExistingPerspectiveData?.name || ''
    },
    
    perspectiveOptions(): Array<{display: string, value: string, isExisting: boolean, projectName?: string, perspectiveData?: PerspectiveDTO}> {
      const options: Array<{display: string, value: string, isExisting: boolean, projectName?: string, perspectiveData?: PerspectiveDTO}> = []
      
      // Add existing perspectives from other projects
      this.existingPerspectives.forEach(perspective => {
        options.push({
          display: perspective.name,
          value: perspective.name,
          isExisting: true,
          projectName: `Project ${perspective.project_id}`,
          perspectiveData: perspective
        })
      })
      
      // Se há texto digitado, sempre adicionar como opção de nova perspectiva
      // (mesmo que corresponda a uma existente, para dar flexibilidade)
      if (this.searchInput && this.searchInput.trim()) {
        const existingMatch = options.find(opt => opt.value.toLowerCase() === this.searchInput.toLowerCase())
        
        if (!existingMatch) {
          // Não existe perspectiva com esse nome, adicionar como nova
          options.unshift({
            display: this.searchInput,
            value: this.searchInput,
            isExisting: false
          })
        }
      }
      

      
      return options
    }
  },
  mounted() {
    this.fetchExistingPerspectives()
  },
  methods: {
    getAnswerTypeLabel(answerType: string): string {
      const option = this.answerTypeOptions.find(opt => opt.value === answerType)
      return option ? option.text : 'Unknown'
    },

    getAnswerTypeIcon(answerType: string): string {
      const option = this.answerTypeOptions.find(opt => opt.value === answerType)
      return option ? option.icon : 'mdi-help'
    },

    getAnswerTypeColor(answerType: string): string {
      const option = this.answerTypeOptions.find(opt => opt.value === answerType)
      return option ? option.color : 'grey'
    },

    addQuestion() {
      this.errorMessage = ''
      if (!this.newQuestion.trim()) {
        this.errorMessage = 'The question cannot be empty'
        return
      }
      if (this.answerType === null) {
        this.errorMessage = 'Please select an answer type'
        return
      }
      const questionData: CreateQuestionCommand = {
        question: this.newQuestion.trim(),
        answer_type: this.answerType,
        answers: []
      }

      this.questionsList.push(questionData)
      this.emitUpdatedQuestions()
      this.resetForm()
    },
    
    removeQuestion(index: number) {
      this.questionToRemove = this.questionsList[index]
      this.questionIndexToRemove = index
      this.confirmDialog = true
    },

    handleConfirmOk() {
      if (this.questionIndexToRemove >= 0) {
        this.questionsList.splice(this.questionIndexToRemove, 1)
        this.emitUpdatedQuestions()
      }
      this.handleConfirmCancel()
    },

    handleConfirmCancel() {
      this.confirmDialog = false
      this.questionToRemove = null
      this.questionIndexToRemove = -1
    },
    
    emitUpdatedQuestions() {
      this.$emit('update-questions', this.questionsList)
      this.$emit('update-name', this.finalName)
    },
    
    resetForm() {
      this.newQuestion = ''
      this.answerType = null
    },
    
    async fetchExistingPerspectives() {
      this.loadingPerspectives = true
      try {
        const perspectives = await this.$services.perspective.listAll()
        // Filter perspectives that are not from the current project
        this.existingPerspectives = perspectives.filter(p => p.project_id !== Number(this.projectId))
      } catch (error) {
        console.error('Error fetching existing perspectives:', error)
                  this.errorMessage = 'Error loading existing perspectives'
      } finally {
        this.loadingPerspectives = false
      }
    },
    
    isExistingPerspectiveName(name: string): boolean {
      return this.existingPerspectives.some(p => p.name.toLowerCase() === name.toLowerCase())
    },
    
    onPerspectiveInput(value: string) {
      this.selectedPerspective = value
      // If the user typed something, ensure it's treated as a new perspective
      // unless explicitly selected from the list
      if (value && !this.isExistingPerspectiveName(value)) {
        this.selectedExistingPerspectiveData = null
        this.questionsList = []
        this.emitUpdatedQuestions()
      }
    },
    
    async onPerspectiveChange() {
      if (!this.selectedPerspective) {
        // Clear everything if there's no selection
        this.selectedExistingPerspectiveData = null
        this.questionsList = []
        this.emitUpdatedQuestions()
        return
      }
      
      // Find if the selected perspective is an existing perspective
      const selectedOption = this.perspectiveOptions.find(opt => opt.value === this.selectedPerspective)
      
      if (selectedOption && selectedOption.isExisting && selectedOption.perspectiveData) {
        // It's an existing perspective, load the questions
        this.selectedExistingPerspectiveData = selectedOption.perspectiveData
        await this.loadQuestionsFromPerspective(selectedOption.perspectiveData)
      } else {
        // It's a new perspective
        this.selectedExistingPerspectiveData = null
        // Only clear questions if it really changed from an existing perspective to a new one
        if (this.isReusing) {
          this.questionsList = []
        }
        this.emitUpdatedQuestions()
      }
    },
    
    async loadQuestionsFromPerspective(perspectiveData: PerspectiveDTO) {
      try {
        // Fetch details of the selected perspective including the questions
        const perspectiveDetails = await this.$services.perspective.get(
          perspectiveData.project_id.toString(), 
          perspectiveData.id.toString()
        )
        
        if (perspectiveDetails && perspectiveDetails.questions && Array.isArray(perspectiveDetails.questions)) {
          // Map existing questions to the expected format
          this.questionsList = perspectiveDetails.questions.map(q => ({
            question: q.question,
            answer_type: q.answer_type || 'string',
            answers: []
          }))
          
          this.emitUpdatedQuestions()
        } else {
          this.questionsList = []
          this.emitUpdatedQuestions()
        }
      } catch (error) {
        console.error('Error loading perspective questions:', error)
                  this.errorMessage = 'Error loading questions from selected perspective'
      }
    },
    
    clearAllQuestions() {
      this.questionsList = []
      this.emitUpdatedQuestions()
    }
  }
})
</script>

<style scoped>
.v-card {
  border-radius: 12px !important;
}

.v-card-title {
  font-size: 1.25rem;
  font-weight: 500;
  border-radius: 12px 12px 0 0 !important;
}

.v-list-item {
  transition: background-color 0.2s ease;
  border-radius: 8px;
  margin: 2px 8px;
}

.v-list-item:hover {
  background-color: #f8f9fa;
}

.v-chip {
  font-weight: 500;
}

h3 {
  display: flex;
  align-items: center;
}

.v-text-field.v-text-field--outlined,
.v-select.v-select--outlined {
  border-radius: 8px;
}

.v-btn {
  text-transform: none;
  font-weight: 500;
}

.v-alert {
  border-radius: 8px;
}

.v-divider {
  margin: 0 16px;
}

.v-list-item-action .v-btn {
  transition: all 0.2s ease;
}

.v-list-item-action .v-btn:hover {
  transform: scale(1.1);
}

.v-list-item:hover .v-list-item-action .v-btn {
  opacity: 1;
}

.v-list-item-action .v-btn {
  opacity: 1 !important;
}

.question-actions {
  opacity: 0.6;
  transition: all 0.3s ease;
}

.v-list-item:hover .question-actions {
  opacity: 1;
}

.delete-btn-modern {
  border-radius: 16px !important;
  text-transform: none !important;
  font-weight: 500 !important;
  transition: all 0.3s ease !important;
  background-color: rgba(25, 118, 210, 0.05) !important;
  border: 1px solid rgba(25, 118, 210, 0.2) !important;
}

.delete-btn-modern:hover {
  background-color: rgba(25, 118, 210, 0.1) !important;
  border-color: #1976d2 !important;
  transform: translateY(-1px) !important;
  box-shadow: 0 2px 8px rgba(25, 118, 210, 0.2) !important;
}

.delete-btn-modern .v-icon {
  transition: transform 0.2s ease;
}

.delete-btn-modern:hover .v-icon {
  transform: scale(1.1);
}

.v-list-item-action {
  min-width: auto !important;
  flex: none !important;
}
</style>
