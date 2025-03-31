<template>
  <v-card>
    <v-card-title>Responder Perspectiva</v-card-title>
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
                  v-for="(option) in getOptionsForQuestion(question.options_group ?? -1)"
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
        <v-row>
          <v-col cols="12">
            <v-btn :disabled="!isFormValid" color="primary" @click="submit">
              Submeter Respostas
            </v-btn>
          </v-col>
        </v-row>
      </v-form>
    </v-card-text>
  </v-card>
</template>

<script lang="ts">
import Vue from "vue";
import { OptionsQuestionItem, QuestionItem } from "~/domain/models/perspective/question/question";

export default Vue.extend({
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
    submit() {
      const formattedAnswers = this.questionsList.map((question) => ({
        questionId: question.id,
        answer: this.answers[question.id],
        questionType: question.type, // assume que question.type é informado
      }));
      this.$emit("submit-answers", formattedAnswers);
      console.log("Respostas enviadas:", formattedAnswers);
    },
  },
});
</script>
