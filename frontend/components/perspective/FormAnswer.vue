<template>
  <v-card v-if="questionsList.length == 0" elevation="1" class="ma-4">
    <v-card-title class="text-h6 grey--text">
      <v-icon left color="grey">mdi-help-circle-outline</v-icon>
      Não foram encontradas questões na perspectiva
    </v-card-title>
  </v-card>
  
  <v-card v-else elevation="2" class="ma-4">
    <v-card-title class="primary white--text">
      <v-icon left color="white">mdi-clipboard-text</v-icon>
      Definir Perspectiva Pessoal
      <v-spacer />
      <v-chip color="white" text-color="primary" small>
        {{ questionsList.length }} pergunta{{ questionsList.length > 1 ? 's' : '' }}
      </v-chip>
    </v-card-title>
    
    <v-card-text class="pa-4">
      <v-form ref="form">
        <div v-for="(question, index) in questionsList" :key="question.id" class="question-container mb-6">
          <!-- Card individual para cada pergunta -->
          <v-card outlined class="question-card">
            <v-card-subtitle class="pb-2 pt-3">
              <div class="d-flex align-center">
                <v-chip 
                  small 
                  :color="getAnswerTypeColor(question.answer_type)" 
                  text-color="white" 
                  class="mr-3"
                >
                  <v-icon small left>{{ getAnswerTypeIcon(question.answer_type) }}</v-icon>
                  {{ getAnswerTypeLabel(question.answer_type) }}
                </v-chip>
                <span class="grey--text text-caption">Pergunta {{ index + 1 }}</span>
              </div>
            </v-card-subtitle>
            
            <v-card-text class="pt-2">
              <!-- Pergunta -->
              <div class="question-text mb-3">
                <h3 class="text-subtitle-1 primary--text mb-2">{{ question.question }}</h3>
              </div>
              
              <!-- Campo de resposta baseado no tipo -->
              <div class="answer-field">
                <!-- Boolean: Radio buttons -->
                <div v-if="question.answer_type === 'boolean'" class="answer-boolean">
                  <v-radio-group 
                    v-model="answers[question.id]" 
                    row 
                    class="mt-1"
                    :rules="[v => v !== undefined && v !== null || 'Selecione uma opção']"
                  >
                    <v-radio 
                      label="Sim" 
                      :value="true" 
                      color="success"
                      class="mr-4"
                    />
                    <v-radio 
                      label="Não" 
                      :value="false" 
                      color="error"
                    />
                  </v-radio-group>
                </div>
                
                <!-- Integer: Number input -->
                <div v-else-if="question.answer_type === 'int'" class="answer-number">
                  <v-text-field 
                    v-model.number="answers[question.id]" 
                    label="Digite um número inteiro" 
                    type="number"
                    step="1"
                    outlined 
                    dense
                    prepend-inner-icon="mdi-numeric"
                    :rules="[
                      v => v !== undefined && v !== null && v !== '' || 'Campo obrigatório',
                      v => Number.isInteger(Number(v)) || 'Deve ser um número inteiro'
                    ]"
                    hint="Ex: 42, -10, 0"
                    persistent-hint
                    class="answer-input"
                  />
                </div>
                
                <!-- Double: Decimal input -->
                <div v-else-if="question.answer_type === 'double'" class="answer-number">
                  <v-text-field 
                    v-model.number="answers[question.id]" 
                    label="Digite um número decimal" 
                    type="number"
                    step="0.01"
                    outlined 
                    dense
                    prepend-inner-icon="mdi-decimal"
                    :rules="[
                      v => v !== undefined && v !== null && v !== '' || 'Campo obrigatório',
                      v => !isNaN(Number(v)) || 'Deve ser um número válido'
                    ]"
                    hint="Ex: 3.14, -2.5, 0.0"
                    persistent-hint
                    class="answer-input"
                  />
                </div>
                
                <!-- String: Text input -->
                <div v-else class="answer-text">
                  <v-textarea 
                    v-model="answers[question.id]" 
                    label="Digite sua resposta" 
                    outlined 
                    dense
                    auto-grow
                    rows="2"
                    prepend-inner-icon="mdi-text"
                    :rules="[
                      v => v && v.trim().length > 0 || 'Campo obrigatório'
                    ]"
                    hint="Digite sua resposta em texto livre"
                    persistent-hint
                    class="answer-input"
                  />
                </div>
              </div>
            </v-card-text>
          </v-card>
        </div>
        
        <!-- Ações -->
        <v-card flat class="actions-card mt-4">
          <v-card-text class="d-flex justify-center align-center pa-3">
            <v-btn 
              :disabled="!isFormValid" 
              color="primary" 
              class="mr-4"
              @click="openConfirmDialog"
            >
              <v-icon left>mdi-check-circle</v-icon>
              Submit Answers
            </v-btn>
            
            <v-btn 
              color="grey" 
              outlined
              @click="clearAnswers"
            >
              <v-icon left>mdi-refresh</v-icon>
              Clear Answers
            </v-btn>
          </v-card-text>
        </v-card>
      </v-form>
    </v-card-text>

    <!-- Janela de Confirmação -->
    <v-dialog v-model="confirmDialog" persistent max-width="500px">
      <v-card>
        <v-card-title class="primary white--text">
          <v-icon left color="white">mdi-help-circle</v-icon>
          Confirm Submission
        </v-card-title>
        <v-card-text class="pt-4">
          <div class="text-center">
            <v-icon size="64" color="primary" class="mb-4">mdi-clipboard-check</v-icon>
            <p class="text-h6 mb-2">Are you sure you want to submit the answers?</p>
            <p class="grey--text">This action cannot be undone.</p>
          </div>
        </v-card-text>
        <v-card-actions class="pa-4">
          <v-spacer />
          <v-btn color="grey" text @click="handleConfirmCancel">
            Cancel
          </v-btn>
          <v-btn color="primary" @click="handleConfirmOk">
            <v-icon left>mdi-check</v-icon>
            Confirm
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </v-card>
</template>

<script lang="ts">
import Vue from 'vue'
import { QuestionItem } from '~/domain/models/perspective/question/question'

export default Vue.extend({
  props: {
    questionsList: {
      type: Array as () => QuestionItem[],
      required: true
    }
  },
  data() {
    return {
      // Armazena as respostas associadas ao ID da questão.
      answers: {} as Record<number, any>,
      // Controle da janela de confirmação
      confirmDialog: false
    }
  },
  computed: {
    isFormValid(): boolean {
      return this.questionsList.every((question) => {
        const answer = this.answers[question.id]
        
        // Verificar baseado no tipo de resposta
        if (question.answer_type === 'boolean') {
          return answer === true || answer === false
        } else if (question.answer_type === 'int') {
          return answer !== undefined && answer !== null && Number.isInteger(Number(answer))
        } else if (question.answer_type === 'double') {
          return answer !== undefined && answer !== null && !isNaN(Number(answer))
        } else {
          // Para string ou padrão
          return typeof answer === 'string' && answer.trim().length > 0
        }
      })
    }
  },
  methods: {
    getAnswerTypeLabel(answerType: string | undefined): string {
      const labels: {[key: string]: string} = {
        'boolean': 'Yes/No',
        'int': 'Integer Number', 
        'double': 'Decimal Number',
        'string': 'Text'
      }
      return labels[answerType || 'string'] || 'Text'
    },
    
    getAnswerTypeColor(answerType: string | undefined): string {
      const colors: {[key: string]: string} = {
        'boolean': 'blue',
        'int': 'green',
        'double': 'orange',
        'string': 'purple'
      }
      return colors[answerType || 'string'] || 'grey'
    },
    
    getAnswerTypeIcon(answerType: string | undefined): string {
      const icons: {[key: string]: string} = {
        'boolean': 'mdi-toggle-switch',
        'int': 'mdi-numeric',
        'double': 'mdi-decimal',
        'string': 'mdi-text'
      }
      return icons[answerType || 'string'] || 'mdi-text'
    },
    
    openConfirmDialog() {
      this.confirmDialog = true
    },
    
    handleConfirmOk() {
      // Fecha a janela de confirmação e submete as respostas
      this.confirmDialog = false
      this.submit()
    },
    
    handleConfirmCancel() {
      // Fecha a janela de confirmação sem submeter
      this.confirmDialog = false
    },
    
    submit() {
      const formattedAnswers = this.questionsList.map((question) => {
        let answerValue = this.answers[question.id]
        
        // Converter valor baseado no tipo
        if (question.answer_type === 'boolean') {
          answerValue = answerValue ? 'true' : 'false'
        } else if (question.answer_type === 'int' || question.answer_type === 'double') {
          answerValue = answerValue.toString()
        }
        
        return {
          questionId: question.id,
          answer: answerValue,
          answerType: question.answer_type || 'string'
        }
      })
      
      this.$emit('submit-answers', formattedAnswers)
      console.log('Respostas enviadas:', formattedAnswers)
    },
    
    clearAnswers() {
      // Reinicia o objeto answers
      this.answers = {} as Record<number, any>
      console.log('Respostas limpas.')
    }
  }
})
</script>

<style scoped>
.question-container {
  margin-bottom: 24px;
}

.question-card {
  border-radius: 8px !important;
  border: 1px solid #e0e0e0;
}

.question-text h3 {
  line-height: 1.4;
  font-weight: 500;
}

.answer-field {
  margin-top: 12px;
}

.answer-input {
  max-width: 350px;
}

.answer-boolean .v-radio {
  margin-right: 20px;
}

.actions-card {
  background-color: #fafafa;
  border-radius: 8px !important;
}

.v-card-title.primary {
  background-color: #1976d2;
}

.v-chip {
  font-weight: 500;
}

/* Espaçamento dos radio buttons */
::v-deep .v-radio-group .v-input--radio-group__input {
  margin-bottom: 6px;
}

/* Estilo para campos de input */
::v-deep .v-text-field.answer-input .v-input__control {
  min-height: 44px;
}

::v-deep .v-textarea.answer-input .v-input__control {
  min-height: 60px;
}

/* Responsividade */
@media (max-width: 960px) {
  .answer-input {
    max-width: 100%;
  }
  
  .actions-card .v-card-text {
    flex-direction: column;
  }
  
  .actions-card .v-btn {
    margin: 6px 0 !important;
    width: 100%;
  }
}
</style>
