<template>
  <div>
    <v-alert v-if="errorMessage" type="error" dismissible @input="errorMessage = ''">
      {{ errorMessage }}
    </v-alert>
    
    <v-card elevation="2">
      <v-card-title class="primary white--text">
        <v-icon left color="white">mdi-lightbulb-on</v-icon>
        Criar Perspectiva
      </v-card-title>
      
      <v-card-text class="pa-6">
        <v-form ref="form">
          <!-- Seção de seleção de perspectiva -->
          <v-row>
            <v-col cols="12">
              <h3 class="mb-4 text--primary">
                <v-icon color="primary" class="mr-2">mdi-format-title</v-icon>
                Nome da Perspectiva
              </h3>
              
              <v-autocomplete
                v-model="selectedPerspective"
                :items="perspectiveOptions"
                item-text="display"
                item-value="value"
                label="Digite o nome da nova perspectiva ou selecione uma existente"
                outlined
                required
                :rules="[rules.required]"
                :loading="loadingPerspectives"
                :search-input.sync="searchInput"
                @change="onPerspectiveChange"
                @input="onPerspectiveInput"
                clearable
                no-filter
                prepend-inner-icon="mdi-lightbulb-on"
                :menu-props="{ maxHeight: 300 }"
                placeholder="Ex: Perspectiva de Qualidade, Usabilidade..."
              >
                <template v-slot:item="{ item }">
                  <v-list-item-avatar>
                    <v-icon :color="item.isExisting ? 'orange' : 'green'">
                      {{ item.isExisting ? 'mdi-recycle' : 'mdi-plus-circle' }}
                    </v-icon>
                  </v-list-item-avatar>
                  <v-list-item-content>
                    <v-list-item-title>{{ item.display }}</v-list-item-title>
                    <v-list-item-subtitle v-if="item.isExisting">
                      <v-icon small class="mr-1">mdi-folder</v-icon>
                      {{ item.projectName }} • Reutilizar perspectiva
                    </v-list-item-subtitle>
                    <v-list-item-subtitle v-else>
                      <v-icon small class="mr-1">mdi-plus</v-icon>
                      Criar nova perspectiva
                    </v-list-item-subtitle>
                  </v-list-item-content>
                </template>
                

              </v-autocomplete>
              


              <!-- Alerta informativo para reutilização -->
              <v-alert 
                v-if="isReusing && questionsList.length > 0" 
                type="info" 
                class="mt-3"
                border="left"
                colored-border
              >
                <div class="d-flex align-center">
                  <v-icon color="info" class="mr-3">mdi-information</v-icon>
                  <div>
                    <strong>Perspectiva reutilizada!</strong><br>
                    {{ questionsList.length }} pergunta(s) da perspectiva "{{ selectedExistingPerspectiveName }}" 
                    foram carregadas e serão copiadas para este projeto.
                  </div>
                </div>
              </v-alert>
            </v-col>
          </v-row>

          <!-- Seção de criação de perguntas (apenas para novas perspectivas) -->
          <div v-if="!isReusing">
            <v-row class="mt-4">
              <v-col cols="12">
                <h3 class="mb-4 text--primary">
                  <v-icon color="primary" class="mr-2">mdi-help-circle</v-icon>
                  Adicionar Perguntas
                </h3>
              </v-col>
            </v-row>

            <v-row>
              <v-col cols="12" md="8">
                <v-text-field
                  v-model="newQuestion"
                  label="Digite sua pergunta"
                  outlined
                  @keyup.enter="addQuestion"
                  prepend-inner-icon="mdi-comment-question"
                  hint="Pressione Enter para adicionar rapidamente"
                  persistent-hint
                />
              </v-col>
              <v-col cols="12" md="4">
                <v-select
                  v-model="answerType"
                  :items="answerTypeOptions"
                  label="Tipo de resposta"
                  outlined
                  prepend-inner-icon="mdi-format-list-bulleted-type"
                />
              </v-col>
            </v-row>

            <v-row>
              <v-col cols="12" class="text-center">
                <v-btn 
                  color="primary" 
                  @click="addQuestion"
                  :disabled="!newQuestion.trim() || !answerType"
                  class="px-6"
                >
                  <v-icon left>mdi-plus</v-icon>
                  Adicionar Pergunta
                </v-btn>
              </v-col>
            </v-row>
          </div>

          <!-- Seção de lista de perguntas -->
          <div v-if="questionsList.length" class="mt-6">
            <v-row>
              <v-col cols="12">
                <div class="d-flex justify-space-between align-center mb-4">
                  <h3 class="text--primary">
                    <v-icon color="primary" class="mr-2">mdi-format-list-numbered</v-icon>
                    Perguntas 
                    <v-chip small color="primary" class="ml-2">{{ questionsList.length }}</v-chip>
                  </h3>
                  
                  <v-btn
                    v-if="!isReusing"
                    color="error"
                    outlined
                    small
                    @click="clearAllQuestions"
                  >
                    <v-icon left small>mdi-delete-sweep</v-icon>
                    Apagar Todas
                  </v-btn>
                </div>
              </v-col>
            </v-row>

            <v-card outlined class="mb-4">
              <v-list>
                <template v-for="(question, index) in questionsList">
                  <v-list-item :key="index" class="py-3">
                    <v-list-item-avatar>
                      <v-avatar color="primary" size="32">
                        <span class="white--text font-weight-bold">{{ index + 1 }}</span>
                      </v-avatar>
                    </v-list-item-avatar>
                    
                    <v-list-item-content>
                      <v-list-item-title class="font-weight-medium">
                        {{ question.question }}
                      </v-list-item-title>
                      <v-list-item-subtitle class="mt-1">
                        <v-chip 
                          small 
                          :color="getAnswerTypeColor(question.answer_type)"
                          text-color="white"
                        >
                          <v-icon small left>{{ getAnswerTypeIcon(question.answer_type) }}</v-icon>
                          {{ getAnswerTypeLabel(question.answer_type) }}
                        </v-chip>
                      </v-list-item-subtitle>
                    </v-list-item-content>

                    <v-list-item-action>
                      <template v-if="!isReusing">
                        <v-btn 
                          icon 
                          color="error" 
                          @click="removeQuestion(index)"
                          small
                        >
                          <v-icon small>mdi-delete</v-icon>
                        </v-btn>
                      </template>
                      <template v-else>
                        <v-btn 
                          icon 
                          disabled
                          small
                        >
                          <v-icon small>mdi-lock</v-icon>
                        </v-btn>
                      </template>
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
      answerTypeOptions: [
        { text: 'Verdadeiro/Falso', value: 'boolean', icon: 'mdi-check-circle', color: 'green' },
        { text: 'Número Inteiro', value: 'int', icon: 'mdi-numeric', color: 'blue' },
        { text: 'Número Decimal', value: 'double', icon: 'mdi-decimal', color: 'purple' },
        { text: 'Texto', value: 'string', icon: 'mdi-text', color: 'orange' }
      ]
    }
  },
  computed: {
    projectId(): string {
      return this.$route.params.id
    },

    isFormValid(): boolean {
      const hasQuestions = this.questionsList.length > 0
      const hasName = this.selectedPerspective && this.selectedPerspective.trim() !== ''
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
      
      // Adicionar perspectivas existentes de outros projetos
      this.existingPerspectives.forEach(perspective => {
        options.push({
          display: perspective.name,
          value: perspective.name,
          isExisting: true,
          projectName: `Projeto ${perspective.project_id}`,
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
  methods: {
    getAnswerTypeLabel(answerType: string): string {
      const option = this.answerTypeOptions.find(opt => opt.value === answerType)
      return option ? option.text : 'Desconhecido'
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
        this.errorMessage = 'A pergunta não pode estar vazia'
        return
      }
      if (this.answerType === null) {
        this.errorMessage = 'Por favor selecione um tipo de resposta'
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
      this.questionsList.splice(index, 1)
      this.emitUpdatedQuestions()
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
        // Filtrar perspectivas que não sejam do projeto atual
        this.existingPerspectives = perspectives.filter(p => p.project_id !== Number(this.projectId))
      } catch (error) {
        console.error('Erro ao buscar perspectivas existentes:', error)
        this.errorMessage = 'Erro ao carregar perspectivas existentes'
      } finally {
        this.loadingPerspectives = false
      }
    },
    
    isExistingPerspectiveName(name: string): boolean {
      return this.existingPerspectives.some(p => p.name.toLowerCase() === name.toLowerCase())
    },
    
    onPerspectiveInput(value: string) {
      this.selectedPerspective = value
      // Se o usuário digitou algo, garantir que seja tratado como nova perspectiva
      // a menos que seja selecionado explicitamente da lista
      if (value && !this.isExistingPerspectiveName(value)) {
        this.selectedExistingPerspectiveData = null
        this.questionsList = []
        this.emitUpdatedQuestions()
      }
    },
    
    async onPerspectiveChange() {
      if (!this.selectedPerspective) {
        // Limpar tudo se não há seleção
        this.selectedExistingPerspectiveData = null
        this.questionsList = []
        this.emitUpdatedQuestions()
        return
      }
      
      // Encontrar se a perspectiva selecionada é uma perspectiva existente
      const selectedOption = this.perspectiveOptions.find(opt => opt.value === this.selectedPerspective)
      
      if (selectedOption && selectedOption.isExisting && selectedOption.perspectiveData) {
        // É uma perspectiva existente, carregar as perguntas
        this.selectedExistingPerspectiveData = selectedOption.perspectiveData
        await this.loadQuestionsFromPerspective(selectedOption.perspectiveData)
      } else {
        // É uma nova perspectiva
        this.selectedExistingPerspectiveData = null
        // Só limpar perguntas se realmente mudou de uma perspectiva existente para nova
        if (this.isReusing) {
          this.questionsList = []
        }
        this.emitUpdatedQuestions()
      }
    },
    
    async loadQuestionsFromPerspective(perspectiveData: PerspectiveDTO) {
      try {
        // Buscar detalhes da perspectiva selecionada incluindo as perguntas
        const perspectiveDetails = await this.$services.perspective.get(
          perspectiveData.project_id.toString(), 
          perspectiveData.id.toString()
        )
        
        if (perspectiveDetails && perspectiveDetails.questions && Array.isArray(perspectiveDetails.questions)) {
          // Mapear as perguntas existentes para o formato esperado
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
        console.error('Erro ao carregar perguntas da perspectiva:', error)
        this.errorMessage = 'Erro ao carregar perguntas da perspectiva selecionada'
      }
    },
    
    clearAllQuestions() {
      this.questionsList = []
      this.emitUpdatedQuestions()
    }
  },
  
  mounted() {
    this.fetchExistingPerspectives()
  }
})
</script>

<style scoped>
.v-card-title {
  font-size: 1.25rem;
  font-weight: 500;
}

.v-list-item {
  transition: background-color 0.2s ease;
}

.v-list-item:hover {
  background-color: #f5f5f5;
}

.v-chip {
  font-weight: 500;
}

h3 {
  display: flex;
  align-items: center;
}
</style>
