<template>
  <v-card v-if="questionsList.length == 0">
    <v-card-title> Não foram encontradas questões na perspectiva</v-card-title>
  </v-card>
  <v-card v-else>
    <v-card-title>Definir Perspectiva Pessoal</v-card-title>
    <v-card-text>
      <v-form ref="form">
        <v-row v-for="question in questionsList" :key="question.id">
          <v-col cols="12">
            <!-- Exibir o texto da pergunta -->
            <v-list-item>
              <v-list-item-content>
                <v-list-item-title>{{ question.question }}</v-list-item-title>
              </v-list-item-content>
            </v-list-item>
            <!-- Se a pergunta tiver opções, exibe um grupo de rádio -->
            <div v-if="question.options_group !== null">
              <v-radio-group v-model="answers[question.id]" row>
                <v-radio
                  v-for="(option) in getOptionsForQuestion(question.options_group)"
                  :key="option.id"
                  :label="option.option"
                  :value="option.id"
                />
              </v-radio-group>
            </div>
            <!-- Caso contrário, exibe uma caixa de texto -->
            <div v-else>
              <v-text-field
                v-model="answers[question.id]"
                label="Resposta"
                outlined
                required
              />
            </div>
          </v-col>
        </v-row>
        <v-row class="d-flex align-center">
          <v-col cols="12" class="d-flex justify-end">
            <v-btn :disabled="!isFormValid" color="primary" @click="openConfirmDialog">
              Submeter Respostas
            </v-btn>
            <v-btn color="warning" @click="clearAnswers" class="ml-2">
              Limpar Respostas
            </v-btn>
          </v-col>
        </v-row>
      </v-form>
    </v-card-text>

    <!-- Janela de Confirmação -->
    <v-dialog v-model="confirmDialog" persistent max-width="500px">
      <confirm-form
        title="Confirmar Submissão"
        message="Tem certeza que deseja submeter as respostas?"
        buttonTrueText="Sim"
        buttonFalseText="Cancelar"
        @ok="handleConfirmOk"
        @cancel="handleConfirmCancel"
      />
    </v-dialog>
  </v-card>
</template>

<script lang="ts">
import Vue from "vue";
import { OptionsQuestionItem, QuestionItem } from "~/domain/models/perspective/question/question";
import ConfirmForm from '@/components/utils/ConfirmForm.vue'

export default Vue.extend({
  components: {
    ConfirmForm
  },
  props: {
    questionsList: {
      type: Array as () => QuestionItem[],
      required: true,
    },
    optionsList: {
      type: Array as () => OptionsQuestionItem[],
      default: () => [],
    },
  },
  data() {
    return {
      // Armazena as respostas associadas ao ID da questão.
      // Para perguntas de texto, será uma string; para escolha múltipla, um número.
      answers: {} as Record<number, any>,
      // Controle da janela de confirmação
      confirmDialog: false,
    };
  },
  computed: {
    isFormValid(): boolean {
      return this.questionsList.every((question) => {
        const answer = this.answers[question.id];
        // Para perguntas de escolha múltipla (options_group !== null), verifica se o valor não é undefined ou null
        if (question.options_group !== null) {
          return answer !== undefined && answer !== null;
        } else {
          // Para perguntas de texto, verifica se há valor não vazio
          return typeof answer === "string" && answer.trim().length > 0;
        }
      });
    },
  },
  methods: {
    getOptionsForQuestion(optionsGroup: number) {
      // Filtra as opções cujo options_group corresponde
      return this.optionsList.filter(option => option.options_group === optionsGroup);
    },
    openConfirmDialog() {
      this.confirmDialog = true;
    },
    handleConfirmOk() {
      // Fecha a janela de confirmação e submete as respostas
      this.confirmDialog = false;
      this.submit();
    },
    handleConfirmCancel() {
      // Fecha a janela de confirmação sem submeter
      this.confirmDialog = false;
    },
    submit() {
      const formattedAnswers = this.questionsList.map((question) => ({
        questionId: question.id,
        answer: this.answers[question.id],
        questionType: question.type, // assume que question.type é informado
      }));
      this.$emit("submit-answers", formattedAnswers);
      console.log("Respostas enviadas:", formattedAnswers);
    },
    clearAnswers() {
      // Reinicia o objeto answers
      this.answers = {} as Record<number, any>;
      console.log("Respostas limpas.");
    },
  },
});
</script>

<style scoped>
::v-deep .v-dialog {
  width: 800px;
}
</style>
