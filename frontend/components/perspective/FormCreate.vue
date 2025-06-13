<template>
  <div>
    <v-alert v-if="errorMessage" type="error" dismissible @input="errorMessage = ''">{{
      errorMessage
    }}</v-alert>
    <v-card>
      <v-card-title>Create Perspective</v-card-title>
      <v-card-text>
        <v-form ref="form">
          <v-row>
            <v-col cols="12">
              <v-autocomplete
                v-model="selectedPerspective"
                :items="perspectiveOptions"
                item-text="display"
                item-value="value"
                label="Nome da Perspectiva"
                outlined
                required
                :rules="[rules.required]"
                :loading="loadingPerspectives"
                :search-input.sync="searchInput"
                @change="onPerspectiveChange"
                @input="onPerspectiveInput"
                clearable
                no-filter
              >
                <template v-slot:item="{ item }">
                  <v-list-item-content>
                    <v-list-item-title>{{ item.display }}</v-list-item-title>
                    <v-list-item-subtitle v-if="item.isExisting">
                      Projeto: {{ item.projectName }} (reutilizar)
                    </v-list-item-subtitle>
                  </v-list-item-content>
                </template>
              </v-autocomplete>
              <v-alert v-if="isReusing && questionsList.length > 0" type="info" class="mt-2">
                As perguntas da perspectiva "{{ selectedExistingPerspectiveName }}" foram carregadas automaticamente e serão copiadas para este projeto.
              </v-alert>
            </v-col>
          </v-row>
          <v-row v-if="!isReusing">
            <v-col cols="12">
              <v-text-field
                v-model="newQuestion"
                label="Add a Question"
                outlined
                @keyup.enter="addQuestion"
              />
            </v-col>
          </v-row>

          <v-row v-if="!isReusing">
            <v-col cols="12">
              <v-radio-group v-model="answerType" row>
                <v-radio label="Verdadeiro/Falso" value="boolean"></v-radio>
                <v-radio label="Número Inteiro" value="int"></v-radio>
                <v-radio label="Número Decimal" value="double"></v-radio>
                <v-radio label="Texto" value="string"></v-radio>
              </v-radio-group>
            </v-col>
          </v-row>

          <v-row v-if="!isReusing">
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
                      <v-list-item-title
                        >{{ question.question }} ({{
                          getAnswerTypeLabel(question.answer_type)
                        }})</v-list-item-title
                      >
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
import { CreateQuestionCommand } from '~/services/application/perspective/question/questionCommand'
import { PerspectiveDTO } from '~/services/application/perspective/perspectiveData'

export default Vue.extend({
  data() {
    return {
      newQuestion: '',
      answerType: null as string | null,
      rules: {
        required: (v: string) => !!v || 'Required'
      },
      questionsList: [] as CreateQuestionCommand[],
      errorMessage: '',
      mdiDelete,
      selectedPerspective: null as string | null,
      searchInput: '',
      existingPerspectives: [] as PerspectiveDTO[],
      loadingPerspectives: false,
      selectedExistingPerspectiveData: null as PerspectiveDTO | null
    }
  },
  computed: {
    projectId(): string {
      return this.$route.params.id
    },

    isFormValid(): boolean {
      const hasQuestions = this.questionsList.length > 0
      const hasName = this.selectedPerspective && this.selectedPerspective.trim() !== ''
      console.log('Validação do formulário:', { hasQuestions, hasName, questionsList: this.questionsList, selectedPerspective: this.selectedPerspective })
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
      
      // Se há texto digitado que não corresponde a nenhuma perspectiva existente, 
      // adicionar como opção de nova perspectiva
      if (this.searchInput && !options.some(opt => opt.value === this.searchInput)) {
        options.unshift({
          display: this.searchInput,
          value: this.searchInput,
          isExisting: false
        })
      }
      
      return options
    }
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
        this.errorMessage = 'The question cannot be empty'
        return
      }
      if (this.answerType === null) {
        this.errorMessage = 'Please select an answer type'
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
    
    onPerspectiveInput(value: string) {
      console.log('Input mudou para:', value)
      this.selectedPerspective = value
    },
    
    async onPerspectiveChange() {
      console.log('Change triggered com valor:', this.selectedPerspective)
      // Encontrar se a perspectiva selecionada é uma perspectiva existente
      const selectedOption = this.perspectiveOptions.find(opt => opt.value === this.selectedPerspective)
      console.log('Opção encontrada:', selectedOption)
      
      if (selectedOption && selectedOption.isExisting && selectedOption.perspectiveData) {
        // É uma perspectiva existente, carregar as perguntas
        console.log('Definindo selectedExistingPerspectiveData para:', selectedOption.perspectiveData)
        this.selectedExistingPerspectiveData = selectedOption.perspectiveData
        console.log('Chamando loadQuestionsFromPerspective...')
        await this.loadQuestionsFromPerspective(selectedOption.perspectiveData)
        console.log('loadQuestionsFromPerspective completado')
      } else {
        // É uma nova perspectiva
        console.log('Nova perspectiva, limpando dados existentes')
        this.selectedExistingPerspectiveData = null
        this.questionsList = []
        this.emitUpdatedQuestions()
      }
    },
    
    async loadQuestionsFromPerspective(perspectiveData: PerspectiveDTO) {
      try {
        console.log('Iniciando carregamento de perguntas para:', perspectiveData)
        
        // Buscar detalhes da perspectiva selecionada incluindo as perguntas
        const perspectiveDetails = await this.$services.perspective.get(
          perspectiveData.project_id.toString(), 
          perspectiveData.id.toString()
        )
        
        console.log('Detalhes recebidos da API:', perspectiveDetails)
        console.log('Perguntas encontradas:', perspectiveDetails?.questions)
        
        if (perspectiveDetails && perspectiveDetails.questions && Array.isArray(perspectiveDetails.questions)) {
          console.log('Mapeando', perspectiveDetails.questions.length, 'perguntas')
          // Mapear as perguntas existentes para o formato esperado
          this.questionsList = perspectiveDetails.questions.map(q => ({
            question: q.question,
            answer_type: q.answer_type || 'string',
            options_group: q.options_group,
            answers: []
          }))
          
          console.log('Lista de perguntas após mapeamento:', this.questionsList)
          this.emitUpdatedQuestions()
        } else {
          console.log('Nenhuma pergunta válida encontrada, definindo lista vazia')
          this.questionsList = []
          this.emitUpdatedQuestions()
        }
      } catch (error) {
        console.error('Erro ao carregar perguntas da perspectiva:', error)
        this.errorMessage = 'Erro ao carregar perguntas da perspectiva selecionada'
      }
    }
  },
  
  mounted() {
    this.fetchExistingPerspectives()
  }
})
</script>
