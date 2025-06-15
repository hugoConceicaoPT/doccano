<template>
  <v-container fluid>
    <v-row>
      <v-col cols="12">
        <v-card>
          <v-tabs v-model="activeTab" background-color="primary" dark grow>
            <v-tab key="annotators">Relatórios sobre Anotadores</v-tab>
            <v-tab key="annotations">Relatórios sobre Anotações</v-tab>
          </v-tabs>

          <v-tabs-items v-model="activeTab">
            <!-- Aba de Relatórios sobre Anotadores -->
            <v-tab-item key="annotators">
          <v-card-title class="primary white--text">
            <v-icon left color="white">{{ mdiFileDocumentOutline }}</v-icon>
            Relatórios sobre Anotadores
            <v-spacer />
            <v-btn color="white" text :loading="isGenerating" @click="generateAndExportReport">
              <v-icon left>{{ mdiRefresh }}</v-icon>
              {{ filters.export_formats.length > 0 ? 'Gerar e Exportar Relatório' : 'Gerar Relatório' }}
            </v-btn>
          </v-card-title>

          <v-card-text class="pa-0">
            <!-- Filtros Melhorados -->
            <v-card flat class="ma-4 elevation-2">
              <v-card-title class="pb-2">
                <v-icon left color="primary">{{ mdiFilter }}</v-icon>
                <span class="text-h6">Filtros de Pesquisa</span>
                <v-spacer />
                <v-btn small text color="primary" @click="clearFilters">
                  <v-icon small left>{{ mdiFilterRemove }}</v-icon>
                  Limpar Filtros
                </v-btn>
              </v-card-title>

              <v-card-text>
                <v-row>
                  <!-- Filtro de Utilizadores -->
                  <v-col cols="12" md="6">
                    <v-autocomplete
                      v-model="filters.users"
                      :items="availableUsers"
                      item-text="username"
                      item-value="id"
                      label="Anotadores"
                      multiple
                      chips
                      deletable-chips
                      clearable
                      outlined
                      dense
                      :prepend-inner-icon="mdiAccount"
                      hint="Selecione os anotadores específicos ou deixe vazio para todos"
                      persistent-hint
                    >
                      <template #selection="{ item, index }">
                        <v-chip
                          v-if="index < 2"
                          small
                          close
                          color="primary"
                          text-color="white"
                          @click:close="removeUser(item)"
                        >
                          {{ getSelectedUserText(item) }}
                        </v-chip>
                        <span v-if="index === 2" class="grey--text text-caption">
                          (+{{ filters.users.length - 2 }} outros)
                        </span>
                      </template>
                      <template #item="{ item }">
                        <v-list-item-avatar>
                          <v-icon color="primary">{{ mdiAccount }}</v-icon>
                        </v-list-item-avatar>
                        <v-list-item-content>
                          <v-list-item-title>{{ item.username }}</v-list-item-title>
                        </v-list-item-content>
                      </template>
                    </v-autocomplete>
                  </v-col>

                  <!-- Filtro de Labels -->
                  <v-col cols="12" md="6">
                    <v-autocomplete
                      v-model="filters.labels"
                      :items="availableLabels"
                      item-text="text"
                      item-value="id"
                      label="Labels"
                      multiple
                      chips
                      deletable-chips
                      clearable
                      outlined
                      dense
                      :prepend-inner-icon="mdiTag"
                      hint="Selecione labels específicos ou deixe vazio para todos"
                      persistent-hint
                    >
                      <template #selection="{ item, index }">
                        <v-chip
                          v-if="index < 2"
                          small
                          close
                          :color="getLabelTypeColor(getSelectedLabelType(item))"
                          text-color="white"
                          @click:close="removeLabel(item)"
                        >
                          {{ getSelectedLabelText(item) }}
                        </v-chip>
                        <span v-if="index === 2" class="grey--text text-caption">
                          (+{{ filters.labels.length - 2 }} outros)
                        </span>
                      </template>
                      <template #item="{ item }">
                        <v-list-item-avatar>
                          <v-icon :color="getLabelTypeColor(item.type)">{{ mdiTag }}</v-icon>
                        </v-list-item-avatar>
                        <v-list-item-content>
                          <v-list-item-title>{{ item.text }}</v-list-item-title>
                        </v-list-item-content>
                      </template>
                    </v-autocomplete>
                  </v-col>



                  <!-- Filtro de Datasets -->
                  <v-col cols="12" md="6">
                    <v-autocomplete
                      v-model="filters.datasets"
                      :items="availableDatasets"
                      item-text="name"
                      item-value="name"
                      label="Datasets"
                      multiple
                      chips
                      deletable-chips
                      clearable
                      outlined
                      dense
                      :prepend-inner-icon="mdiDatabase"
                      hint="Selecione datasets específicos ou deixe vazio para todos"
                      persistent-hint
                    >
                      <template #selection="{ index }">
                        <v-chip
                          v-if="index < 2"
                          small
                          close
                          color="teal"
                          text-color="white"
                          @click:close="removeDataset(filters.datasets[index])"
                        >
                          <v-icon small left>{{ mdiDatabase }}</v-icon>
                          {{ filters.datasets[index] }}
                        </v-chip>
                        <span v-if="index === 2" class="grey--text text-caption">
                          (+{{ filters.datasets.length - 2 }} outros)
                        </span>
                      </template>
                      <template #item="{ item }">
                        <v-list-item-avatar>
                          <v-icon color="teal">{{ mdiDatabase }}</v-icon>
                        </v-list-item-avatar>
                        <v-list-item-content>
                          <v-list-item-title>{{ item.name }}</v-list-item-title>
                        </v-list-item-content>
                      </template>
                    </v-autocomplete>
                  </v-col>

                  <!-- Filtro de Perguntas da Perspectiva -->
                  <v-col cols="12" md="6">
                    <v-autocomplete
                      v-model="filters.perspective_questions"
                      :items="availablePerspectiveQuestions"
                      item-text="text"
                      item-value="id"
                      label="Perguntas da Perspectiva"
                      multiple
                      chips
                      deletable-chips
                      clearable
                      outlined
                      dense
                      :prepend-inner-icon="mdiHelpCircle"
                      hint="Selecione perguntas específicas ou deixe vazio para todas"
                      persistent-hint
                    >
                      <template #selection="{ item, index }">
                        <v-chip
                          v-if="index < 2"
                          small
                          close
                          color="indigo"
                          text-color="white"
                          @click:close="removePerspectiveQuestion(item)"
                        >
                          <v-icon small left>{{ mdiHelpCircle }}</v-icon>
                          {{ getSelectedPerspectiveQuestionText(item) }}
                        </v-chip>
                        <span v-if="index === 2" class="grey--text text-caption">
                          (+{{ filters.perspective_questions.length - 2 }} outras)
                        </span>
                      </template>
                      <template #item="{ item }">
                        <v-list-item-avatar>
                          <v-icon color="indigo">{{ mdiHelpCircle }}</v-icon>
                        </v-list-item-avatar>
                        <v-list-item-content>
                          <v-list-item-title>{{ item.text }}</v-list-item-title>
                        </v-list-item-content>
                      </template>
                    </v-autocomplete>
                  </v-col>

                  <!-- Filtro de Respostas da Perspectiva (só aparece quando há perguntas selecionadas) -->
                  <v-col v-if="filters.perspective_questions.length > 0" cols="12" md="6">
                    <v-autocomplete
                      v-model="filters.perspective_answers"
                      :items="filteredAnswersForSelectedQuestions"
                      item-text="text"
                      item-value="id"
                      label="Respostas da Perspectiva"
                      multiple
                      chips
                      deletable-chips
                      clearable
                      outlined
                      dense
                      :prepend-inner-icon="mdiCommentCheck"
                      hint="Selecione respostas específicas ou deixe vazio para todas"
                      persistent-hint
                    >
                      <template #selection="{ item, index }">
                        <v-chip
                          v-if="index < 2"
                          small
                          close
                          color="amber"
                          text-color="black"
                          @click:close="removePerspectiveAnswer(item)"
                        >
                          <v-icon small left>{{ mdiCommentCheck }}</v-icon>
                          {{ getSelectedPerspectiveAnswerText(item) }}
                        </v-chip>
                        <span v-if="index === 2" class="grey--text text-caption">
                          (+{{ filters.perspective_answers.length - 2 }} outras)
                        </span>
                      </template>
                      <template #item="{ item }">
                        <v-list-item-avatar>
                          <v-icon color="amber">{{ mdiCommentCheck }}</v-icon>
                        </v-list-item-avatar>
                        <v-list-item-content>
                          <v-list-item-title>{{ item.text }}</v-list-item-title>
                        </v-list-item-content>
                      </template>
                    </v-autocomplete>
                  </v-col>

                  <!-- Filtro de Opções de Exportação -->
                  <v-col cols="12">
                    <v-select
                      v-model="filters.export_formats"
                      :items="exportFormatOptions"
                      item-text="text"
                      item-value="value"
                      label="Formatos de Exportação"
                      multiple
                      chips
                      deletable-chips
                      clearable
                      outlined
                      dense
                      :prepend-inner-icon="mdiDownload"
                      hint="Selecione os formatos de exportação desejados (PDF, CSV ou ambos)"
                      persistent-hint
                    >
                      <template #selection="{ item, index }">
                        <v-chip
                          v-if="index < 2"
                          small
                          close
                          :color="getExportFormatColor(item.value)"
                          text-color="white"
                          @click:close="removeExportFormat(item.value)"
                        >
                          <v-icon small left>{{ item.icon }}</v-icon>
                          {{ item.value.toUpperCase() }}
                        </v-chip>
                        <span v-if="index === 2" class="grey--text text-caption">
                          (+{{ filters.export_formats.length - 2 }} outros)
                        </span>
                      </template>
                      <template #item="{ item }">
                        <v-list-item-avatar>
                          <v-icon :color="getExportFormatColor(item.value)">{{ item.icon }}</v-icon>
                        </v-list-item-avatar>
                        <v-list-item-content>
                          <v-list-item-title>{{ item.text }}</v-list-item-title>
                          <v-list-item-subtitle class="text-caption">{{
                            item.description
                          }}</v-list-item-subtitle>
                        </v-list-item-content>
                      </template>
                    </v-select>
                  </v-col>
                </v-row>

                <!-- Resumo dos Filtros Ativos -->
                <v-row v-if="hasActiveFilters" class="mt-2">
                  <v-col cols="12">
                    <v-divider class="mb-3" />
                    <div class="d-flex align-center">
                      <v-icon small color="primary" class="mr-2">{{ mdiInformation }}</v-icon>
                      <span class="text-caption font-weight-medium">Filtros ativos:</span>
                      <v-spacer />
                      <span class="text-caption grey--text"
                        >{{ getActiveFiltersCount }} filtro(s) aplicado(s)</span
                      >
                    </div>
                  </v-col>
                </v-row>
              </v-card-text>
            </v-card>

            <!-- Tabela de Resultados -->
            <div class="ma-4">
              <!-- Resumo do Relatório de Anotadores -->
              <v-card v-if="reportData && reportData.length > 0" flat class="ma-4">
                <v-card-title class="subtitle-1">
                  <v-icon left color="info">{{ mdiInformationOutline }}</v-icon>
                  Resumo do Relatório
                </v-card-title>
                <v-card-text>
                  <v-row>
                    <v-col cols="12" sm="6" md="4">
                      <v-card outlined class="text-center pa-3">
                        <div class="text-h5 primary--text">{{ reportData.length }}</div>
                        <div class="caption">Total de Anotadores</div>
                      </v-card>
                    </v-col>
                    <v-col cols="12" sm="6" md="4">
                      <v-card outlined class="text-center pa-3">
                        <div class="text-h5 primary--text">{{ getTotalAnnotations() }}</div>
                        <div class="caption">Total de Anotações</div>
                      </v-card>
                    </v-col>
                    <v-col cols="12" sm="6" md="4">
                      <v-card outlined class="text-center pa-3">
                        <div class="text-h5 primary--text">{{ getUniqueLabelsCount() }}</div>
                        <div class="caption">Labels Diferentes</div>
                      </v-card>
                    </v-col>
                  </v-row>
                </v-card-text>
              </v-card>

              <!-- Tabela de Anotadores -->
              <v-card v-if="reportData && reportData.length > 0" flat class="ma-4">
                <v-card-title>
                  <v-icon left color="primary">{{ mdiTable }}</v-icon>
                  Detalhes dos Anotadores
                  <v-spacer></v-spacer>
                  <v-btn
                    color="primary"
                    outlined
                    small
                    @click="generateAndExportReport"
                    :loading="isGenerating"
                    class="mr-2"
                  >
                    <v-icon left small>{{ mdiRefresh }}</v-icon>
                    Atualizar
                  </v-btn>
                </v-card-title>
                <v-data-table
                  :headers="tableHeaders"
                  :items="reportData"
                  :loading="isGenerating"
                  class="elevation-1"
                  :items-per-page="15"
                  :footer-props="{
                    'items-per-page-options': [10, 15, 25, 50, -1],
                    'items-per-page-text': 'Itens por página:',
                    showFirstLastPage: true
                  }"
                  loading-text="Carregando dados..."
                  no-data-text="Nenhum dado disponível"
                >
                  <!-- Template para nome de utilizador -->
                  <template #[`item.annotator_username`]="{ item }">
                    <div class="d-flex align-center">
                      <v-avatar size="32" color="primary" class="mr-3">
                        <span class="white--text text-subtitle-2">{{ item.annotator_username.charAt(0).toUpperCase() }}</span>
                      </v-avatar>
                      <div>
                        <div class="font-weight-medium">{{ item.annotator_username }}</div>
                        <div class="text-caption grey--text">{{ item.annotator_name }}</div>
                      </div>
                    </div>
                  </template>

                  <!-- Template para Labels -->
                  <template #[`item.label_breakdown`]="{ item }">
                    <div class="labels-container">
                      <div v-if="Object.keys(item.label_breakdown).length > 0">
                        <v-chip
                          v-for="(count, label) in item.label_breakdown"
                          :key="label"
                          small
                          color="primary"
                          outlined
                          class="ma-1"
                        >
                          {{ label }}: {{ count }}
                        </v-chip>
                      </div>
                      <span v-else class="grey--text text-caption">
                        <v-icon small color="grey">{{ mdiInformationOutline }}</v-icon>
                        Sem labels
                      </span>
                    </div>
                  </template>

                  <!-- Template para Datasets -->
                  <template #[`item.dataset_label_breakdown`]="{ item }">
                    <div class="datasets-breakdown-modern">
                      <div
                        v-for="(labels, dataset) in item.dataset_label_breakdown"
                        :key="dataset"
                        class="dataset-section-modern mb-3"
                      >
                        <div class="dataset-header-modern">
                          <v-icon small color="teal" class="mr-2">{{ mdiDatabase }}</v-icon>
                          <span class="font-weight-medium text-body-2">{{ dataset }}</span>
                        </div>
                        <div class="dataset-labels-modern">
                          <v-chip
                            v-for="(count, label) in labels"
                            :key="`${dataset}-${label}`"
                            x-small
                            class="ma-1"
                            color="teal"
                            text-color="white"
                          >
                            {{ label }}: {{ count }}
                          </v-chip>
                        </div>
                      </div>
                      <div
                        v-if="!item.dataset_label_breakdown || Object.keys(item.dataset_label_breakdown).length === 0"
                        class="no-data-modern"
                      >
                        <v-icon small color="grey">{{ mdiInformationOutline }}</v-icon>
                        <span class="text-caption grey--text ml-1">Nenhuma anotação</span>
                      </div>
                    </div>
                  </template>

                  <!-- Template para Perguntas e Respostas -->
                  <template #[`item.perspective_questions_answers`]="{ item }">
                    <div class="qa-breakdown-modern">
                      <div
                        v-if="item.perspective_questions_answers && item.perspective_questions_answers.answers && item.perspective_questions_answers.answers.length > 0"
                      >
                        <div
                          v-for="question in getQuestionsWithAnswers(item.perspective_questions_answers)"
                          :key="question.question_id"
                          class="question-section-modern mb-3"
                        >
                          <div class="question-header-modern">
                            <v-icon small color="indigo" class="mr-2">{{ mdiHelpCircle }}</v-icon>
                            <span class="font-weight-medium text-body-2">{{ question.question_text }}</span>
                          </div>
                          <div class="question-answers-modern">
                            <v-chip
                              v-for="answer in question.answers"
                              :key="answer.answer_id"
                              x-small
                              class="ma-1"
                              color="indigo"
                              text-color="white"
                            >
                              <v-icon left x-small>{{ mdiCommentCheck }}</v-icon>
                              {{ answer.answer_text }}
                            </v-chip>
                          </div>
                        </div>
                      </div>
                      <div v-else class="no-data-modern">
                        <v-icon small color="grey">{{ mdiInformationOutline }}</v-icon>
                        <span class="text-caption grey--text ml-1">Nenhuma pergunta/resposta</span>
                      </div>
                    </div>
                  </template>
                </v-data-table>
              </v-card>

              <!-- Estado vazio -->
              <v-card v-else-if="!isGenerating" flat class="text-center pa-12 elevation-2">
                <v-icon size="80" color="grey lighten-2">{{ mdiFileDocumentOutline }}</v-icon>
                <h3 class="grey--text mt-6 mb-2">Nenhum relatório gerado</h3>
                <p class="grey--text mb-6">
                  Configure os filtros desejados e clique em "Gerar Relatório" para visualizar os
                  dados dos anotadores
                </p>
                <v-btn color="primary" large @click="generateAndExportReport">
                  <v-icon left>{{ mdiRefresh }}</v-icon>
                  Gerar Primeiro Relatório
                </v-btn>
              </v-card>

              <!-- Loading -->
              <v-card v-else flat class="text-center pa-12 elevation-2">
                <v-progress-circular indeterminate color="primary" size="80" width="6" />
                <h3 class="mt-6 mb-2">Gerando relatório...</h3>
                <p class="grey--text">
                  Por favor aguarde enquanto processamos os dados dos anotadores
                </p>
              </v-card>
            </div>
              </v-card-text>
            </v-tab-item>
            
            <!-- Nova aba de Relatórios sobre Anotações -->
            <v-tab-item key="annotations">
              <v-card-title class="primary white--text">
                <v-icon left color="white">{{ mdiFileDocumentOutline }}</v-icon>
                Relatórios sobre Anotações
                <v-spacer />
                <v-btn 
                  color="white" 
                  text 
                  :loading="isGeneratingAnnotations || isExportingAnnotation" 
                  @click="generateAndExportAnnotationReport"
                >
                  <v-icon left>{{ annotationExportFormats.length > 0 ? mdiDownload : mdiEye }}</v-icon>
                  {{ annotationExportFormats.length > 0 ? 'Gerar e Exportar Relatório' : 'Gerar Relatório' }}
                </v-btn>
              </v-card-title>

              <v-card-text class="pa-0">
                <!-- Filtros para Relatório de Anotações -->
                <v-card flat class="ma-4 elevation-2">
                  <v-card-title class="pb-2">
                    <v-icon left color="primary">{{ mdiFilter }}</v-icon>
                    <span class="text-h6">Filtros de Pesquisa</span>
                    <v-spacer />
                    <v-btn small text color="primary" @click="clearAnnotationFilters">
                      <v-icon small left>{{ mdiFilterRemove }}</v-icon>
                      Limpar Filtros
                    </v-btn>
                  </v-card-title>

                  <v-card-text>
                    <v-row>
                      <!-- Filtro de Utilizadores -->
                      <v-col cols="12" md="6">
                        <v-autocomplete
                          v-model="annotationFilters.users"
                          :items="availableUsers"
                          item-text="username"
                          item-value="id"
                          label="Anotadores"
                          multiple
                          chips
                          deletable-chips
                          clearable
                          outlined
                          dense
                          :prepend-inner-icon="mdiAccount"
                          hint="Selecione os anotadores específicos ou deixe vazio para todos"
                          persistent-hint
                        />
                      </v-col>

                      <!-- Filtro de Labels -->
                      <v-col cols="12" md="6">
                        <v-autocomplete
                          v-model="annotationFilters.labels"
                          :items="availableLabels"
                          item-text="text"
                          item-value="id"
                          label="Labels"
                          multiple
                          chips
                          deletable-chips
                          clearable
                          outlined
                          dense
                          :prepend-inner-icon="mdiTag"
                          hint="Selecione labels específicos ou deixe vazio para todos"
                          persistent-hint
                        />
                      </v-col>

                      <!-- Filtro de Exemplos -->
                      <v-col cols="12" md="6">
                        <v-autocomplete
                          v-model="annotationFilters.examples"
                          :items="availableExamples"
                          item-text="text"
                          item-value="id"
                          label="Exemplos"
                          multiple
                          chips
                          deletable-chips
                          clearable
                          outlined
                          dense
                          :prepend-inner-icon="mdiFileDocumentOutline"
                          hint="Selecione exemplos específicos ou deixe vazio para todos"
                          persistent-hint
                        />
                      </v-col>
                      
                      <!-- Filtro de Discrepâncias -->
                      <v-col cols="12" md="6">
                        <v-select
                          v-model="annotationFilters.discrepancy_filter"
                          :items="discrepancyOptions"
                          item-text="text"
                          item-value="value"
                          label="Filtro de Discrepâncias"
                          outlined
                          dense
                          clearable
                          :prepend-inner-icon="mdiAlertCircle"
                          hint="Filtre por anotações com ou sem discrepâncias"
                          persistent-hint
                        >
                          <template #selection="{ item }">
                            <v-chip small :color="getDiscrepancyColor(item.value)" text-color="white">
                              <v-icon small left>{{ getDiscrepancyIcon(item.value) }}</v-icon>
                              {{ item.text }}
                            </v-chip>
                          </template>
                        </v-select>
                      </v-col>

                      <!-- Filtro de Perguntas da Perspectiva -->
                      <v-col cols="12" md="6">
                        <v-autocomplete
                          v-model="annotationFilters.perspective_questions"
                          :items="availablePerspectiveQuestions"
                          item-text="text"
                          item-value="id"
                          label="Perguntas da Perspectiva"
                          multiple
                          chips
                          deletable-chips
                          clearable
                          outlined
                          dense
                          :prepend-inner-icon="mdiHelpCircle"
                          hint="Selecione perguntas específicas da perspectiva"
                          persistent-hint
                          @input="onPerspectiveQuestionsChange"
                        />
                      </v-col>

                      <!-- Filtro de Respostas da Perspectiva -->
                      <v-col cols="12" md="6" v-if="annotationFilters.perspective_questions && annotationFilters.perspective_questions.length > 0">
                        <v-autocomplete
                          v-model="annotationFilters.perspective_answers"
                          :items="filteredPerspectiveAnswers"
                          item-text="text"
                          item-value="id"
                          label="Respostas da Perspectiva"
                          multiple
                          chips
                          deletable-chips
                          clearable
                          outlined
                          dense
                          :prepend-inner-icon="mdiCommentCheck"
                          hint="Selecione respostas específicas das perguntas selecionadas"
                          persistent-hint
                        >
                          <template #selection="{ item, index }">
                            <v-chip
                              v-if="index < 2"
                              small
                              close
                              color="purple"
                              text-color="white"
                              @click:close="removePerspectiveAnswer(item)"
                            >
                              {{ getSelectedAnswerText(item) }}
                            </v-chip>
                            <span v-if="index === 2" class="grey--text text-caption">
                              (+{{ annotationFilters.perspective_answers.length - 2 }} outras)
                            </span>
                          </template>
                        </v-autocomplete>
                      </v-col>

                      <!-- Formato de Exportação -->
                      <v-col cols="12" md="6">
                        <v-select
                          v-model="annotationExportFormats"
                          :items="exportFormatOptions"
                          item-text="text"
                          item-value="value"
                          label="Formatos de Exportação"
                          multiple
                          chips
                          deletable-chips
                          clearable
                          outlined
                          dense
                          :prepend-inner-icon="mdiFileDelimited"
                          hint="Selecione os formatos para exportar (deixe vazio para apenas visualizar)"
                          persistent-hint
                        >
                          <template #selection="{ item, index }">
                            <v-chip
                              v-if="index < 2"
                              small
                              close
                              :color="getExportFormatColor(item.value)"
                              text-color="white"
                              @click:close="removeAnnotationExportFormat(item.value)"
                            >
                              <v-icon small left>{{ item.icon }}</v-icon>
                              {{ item.value.toUpperCase() }}
                            </v-chip>
                            <span v-if="index === 2" class="grey--text text-caption">
                              (+{{ annotationExportFormats.length - 2 }} outros)
                            </span>
                          </template>
                          <template #item="{ item }">
                            <v-list-item-avatar>
                              <v-icon :color="getExportFormatColor(item.value)">{{ item.icon }}</v-icon>
                            </v-list-item-avatar>
                            <v-list-item-content>
                              <v-list-item-title>{{ item.text }}</v-list-item-title>
                              <v-list-item-subtitle class="text-caption">{{ item.description }}</v-list-item-subtitle>
                            </v-list-item-content>
                          </template>
                        </v-select>
                      </v-col>
                    </v-row>
                  </v-card-text>
                </v-card>

                <!-- Resultados do Relatório de Anotações -->
                <div v-if="isGeneratingAnnotations" class="text-center py-5">
                  <v-progress-circular indeterminate color="primary" size="64" width="5" />
                  <div class="mt-3">Gerando relatório...</div>
                </div>
                
                <div v-else-if="annotationReportError" class="text-center py-5 error--text">
                  <v-icon color="error" large>{{ mdiAlertCircle }}</v-icon>
                  <div class="mt-2">{{ annotationReportError }}</div>
                  <v-btn color="error" text class="mt-2" @click="annotationReportError = null">
                    <v-icon left>{{ mdiRefresh }}</v-icon>
                    Tentar novamente
                  </v-btn>
                </div>
                
                <div v-else-if="!annotationReportData" class="text-center py-5">
                  <v-icon color="grey" size="64">{{ mdiFileDocumentOutline }}</v-icon>
                  <div class="mt-3 grey--text">
                    Configure os filtros acima e clique em "Gerar Relatório" para começar.
                  </div>
                </div>
                
                <div v-else>
                  <!-- Resumo do relatório -->
                  <v-card flat class="ma-4">
                    <v-card-title class="subtitle-1">
                      <v-icon left color="info">{{ mdiInformationOutline }}</v-icon>
                      Resumo do Relatório
                    </v-card-title>
                    <v-card-text>
                      <v-row>
                        <v-col cols="12" sm="6" md="4">
                          <v-card outlined class="text-center pa-3">
                            <div class="text-h5 primary--text">{{ annotationReportData.summary.total_annotations }}</div>
                            <div class="caption">Total de Anotações</div>
                          </v-card>
                        </v-col>
                        <v-col cols="12" sm="6" md="4">
                          <v-card outlined class="text-center pa-3">
                            <div class="text-h5 primary--text">{{ annotationReportData.summary.total_examples }}</div>
                            <div class="caption">Total de Exemplos</div>
                          </v-card>
                        </v-col>
                        <v-col cols="12" sm="6" md="4">
                          <v-card outlined class="text-center pa-3">
                            <div class="text-h5 primary--text">{{ annotationReportData.summary.total_annotators }}</div>
                            <div class="caption">Total de Anotadores</div>
                          </v-card>
                        </v-col>
                      </v-row>
                    </v-card-text>
                  </v-card>
                  
                  <!-- Tabela de anotações -->
                  <v-card flat class="ma-4">
                    <v-card-title>
                      <v-icon left color="primary">{{ mdiTable }}</v-icon>
                      Detalhes das Anotações
                      <v-spacer></v-spacer>
                      <v-text-field
                        v-model="annotationSearch"
                        append-icon="mdi-magnify"
                        label="Pesquisar"
                        single-line
                        hide-details
                        dense
                        outlined
                        class="mr-2"
                        style="max-width: 300px"
                      ></v-text-field>
                    </v-card-title>
                    <v-data-table
                      :headers="annotationHeaders"
                      :items="annotationReportData.data"
                      :items-per-page="10"
                      :search="annotationSearch"
                      :server-items-length="annotationReportData.total_pages * 10"
                      :footer-props="{
                        'items-per-page-options': [10, 25, 50],
                        showFirstLastPage: true
                      }"
                      class="elevation-1"
                      :page.sync="annotationPage"
                      @update:page="loadAnnotationPage"
                    >
                      <template #[`item.created_at`]="{ item }">
                        {{ new Date(item.created_at).toLocaleString('pt-BR') }}
                      </template>
                      
                      <template #[`item.label_text`]="{ item }">
                        <div class="labels-container">
                          <v-chip
                            v-if="item.label_text && item.label_text !== 'Sem labels'"
                            small
                            color="primary"
                            outlined
                            class="ma-1"
                          >
                            {{ item.label_text }}
                          </v-chip>
                          <span v-else class="grey--text text-caption">
                            <v-icon small color="grey">{{ mdiInformationOutline }}</v-icon>
                            Sem labels
                          </span>
                        </div>
                      </template>
                    </v-data-table>
                  </v-card>
                </div>
              </v-card-text>
            </v-tab-item>
          </v-tabs-items>
        </v-card>
      </v-col>
    </v-row>


  </v-container>
  </template>

<script lang="ts">
import Vue from 'vue'
import {
  mdiFileDocumentOutline,
  mdiRefresh,
  mdiDownload,
  mdiFilter,
  mdiFilterRemove,
  mdiAccount,
  mdiTag,
  mdiCalendarStart,
  mdiCalendarEnd,
  mdiInformation,
  mdiAlertCircle,
  mdiInformationOutline,
  mdiClose,
  mdiTable,
  mdiFileDelimited,
  mdiFilePdfBox,
  mdiEye,
  mdiDatabase,
  mdiHelpCircle,
  mdiCommentCheck,
  mdiCheckCircle,
  mdiCloseCircle
} from '@mdi/js'

declare module 'vue/types/vue' {
  interface Vue {
    $axios: any
  }
}

export default Vue.extend({

  layout: 'project',

  middleware: ['check-auth', 'auth', 'setCurrentProject', 'isProjectAdmin'],

  data(): {
    mdiFileDocumentOutline: string;
    mdiRefresh: string;
    mdiDownload: string;
    mdiFilter: string;
    mdiFilterRemove: string;
    mdiAccount: string;
    mdiTag: string;
    mdiCalendarStart: string;
    mdiCalendarEnd: string;

    mdiInformation: string;
    mdiTable: string;
    mdiFileDelimited: string;
    mdiFilePdfBox: string;
    mdiInformationOutline: string;
    mdiAlertCircle: string;
    mdiClose: string;
    mdiEye: string;
    mdiDatabase: string;
    mdiHelpCircle: string;
    mdiCommentCheck: string;
    mdiCheckCircle: string;
    mdiCloseCircle: string;
    isGenerating: boolean;
    dateFromMenu: boolean;
    dateToMenu: boolean;
    filters: {
      users: number[];
      date_from: string | null;
      date_to: string | null;
      labels: number[];
      export_formats: string[];
      datasets: string[];
      perspective_questions: number[];
      perspective_answers: number[];
    };
    availableUsers: Array<{id: number; username: string}>;
    availableLabels: Array<{id: number; text: string; type: string}>;

    reportData: any[];
    tableHeaders: Array<{text: string; value: string; sortable?: boolean; width?: string}>;

    
    isExporting: boolean;
    activeTab: string;
    annotationFilters: {
      users: number[];
      labels: number[];
      examples: number[];
      discrepancy_filter: string | null;
      perspective_questions: number[];
      perspective_answers: number[];
    };
    isGeneratingAnnotations: boolean;
    annotationReportData: any;
    annotationReportError: string | null;
    annotationSearch: string;
    annotationHeaders: Array<{text: string; value: string; width?: string; sortable?: boolean}>;
    annotationPage: number;
    annotationExportFormats: string[];
    annotationExportMaxResults: number;
    isExportingAnnotation: boolean;
    availableExamples: Array<{id: number; text: string}>;
    exportFormatOptions: Array<{value: string; text: string; icon: string; description: string}>;

    availableDatasets: Array<{name: string; count: number}>;
    discrepancyOptions: Array<{value: string; text: string; description: string}>;
    availablePerspectiveQuestions: Array<{id: number; text: string}>;
    availablePerspectiveAnswers: Array<{id: number; text: string; question_id: number}>;
    filteredPerspectiveAnswers: Array<{id: number; text: string; question_id: number; ids?: number[]}>;
  } {
    return {
      mdiFileDocumentOutline,
      mdiRefresh,
      mdiDownload,
      mdiFilter,
      mdiFilterRemove,
      mdiAccount,
      mdiTag,
      mdiCalendarStart,
      mdiCalendarEnd,
      mdiInformation,
      mdiTable,
      mdiFileDelimited,
      mdiFilePdfBox,
      mdiInformationOutline,
      mdiAlertCircle,
      mdiClose,
      mdiEye,
      mdiDatabase,
      mdiHelpCircle,
      mdiCommentCheck,
      mdiCheckCircle,
      mdiCloseCircle,

      isGenerating: false,
      dateFromMenu: false,
      dateToMenu: false,

      filters: {
        users: [] as number[],
        date_from: null as string | null,
        date_to: null as string | null,
        labels: [] as number[],
        export_formats: [] as string[],
        datasets: [] as string[],
        perspective_questions: [] as number[],
        perspective_answers: [] as number[]
      },

      availableUsers: [] as Array<{id: number; username: string}>,
      availableLabels: [] as Array<{id: number; text: string; type: string}>,

      reportData: [] as any[],

      tableHeaders: [
        { 
          text: 'Utilizador', 
          value: 'annotator_username', 
          sortable: true, 
          width: '200px'
        },
        { 
          text: 'Perguntas e Respostas', 
          value: 'perspective_questions_answers', 
          sortable: false, 
          width: '300px'
        },
        { 
          text: 'Labels', 
          value: 'label_breakdown', 
          sortable: false, 
          width: '250px'
        },
        { 
          text: 'Datasets', 
          value: 'dataset_label_breakdown', 
          sortable: false, 
          width: '400px'
        }
      ],

      isExporting: false,

      activeTab: 'annotators',
      
      // Dados para relatório de anotações
      annotationFilters: {
        users: [] as number[],
        labels: [] as number[],
        examples: [] as number[],
        discrepancy_filter: null as string | null,
        perspective_questions: [] as number[],
        perspective_answers: [] as number[]
      },
      isGeneratingAnnotations: false,
      annotationReportData: null as any,
      annotationReportError: null as string | null,
      annotationSearch: '',
      annotationHeaders: [
        { text: 'Exemplo', value: 'example_name', width: '200px' },
        { text: 'Utilizador', value: 'username', width: '130px' },
        { text: 'Labels Utilizadas', value: 'label_text', width: '300px' },
        { text: 'Data', value: 'created_at', width: '180px' }
      ],
      annotationPage: 1,
      annotationExportFormats: [],
      annotationExportMaxResults: 1000000,
      isExportingAnnotation: false,
      availableExamples: [] as Array<{id: number; text: string}>,
      exportFormatOptions: [
        { value: 'csv', text: 'CSV (Comma Separated Values)', icon: mdiFileDelimited, description: 'Ideal para Excel e análise de dados' },
        { value: 'pdf', text: 'PDF (Portable Document Format)', icon: mdiFilePdfBox, description: 'Documento formatado para visualização e impressão' }
      ],

      availableDatasets: [] as Array<{name: string; count: number}>,
      discrepancyOptions: [
        { value: 'all', text: 'Todas', description: 'Incluir todas as anotações' },
        { value: 'with_discrepancy', text: 'Com Discrepância', description: 'Apenas anotações com discrepâncias' },
        { value: 'without_discrepancy', text: 'Sem Discrepância', description: 'Apenas anotações sem discrepâncias' }
      ] as Array<{value: string; text: string; description: string}>,
      availablePerspectiveQuestions: [] as Array<{id: number; text: string}>,
      availablePerspectiveAnswers: [] as Array<{id: number; text: string; question_id: number}>,
      filteredPerspectiveAnswers: [] as Array<{id: number; text: string; question_id: number; ids?: number[]}>
    }
  },

  computed: {
    projectId(): string {
      return this.$route.params.id
    },

    hasActiveFilters() {
      return (
        this.filters.users.length > 0 ||
        this.filters.labels.length > 0 ||
        this.filters.export_formats.length > 0 ||
        this.filters.date_from ||
        this.filters.date_to ||
        this.filters.datasets.length > 0 ||
        this.filters.perspective_questions.length > 0 ||
        this.filters.perspective_answers.length > 0
      )
    },

    getActiveFiltersCount() {
      let count = 0
      if (this.filters.users.length > 0) count++
      if (this.filters.labels.length > 0) count++
      if (this.filters.export_formats.length > 0) count++
      if (this.filters.date_from) count++
      if (this.filters.date_to) count++
      if (this.filters.datasets.length > 0) count++
      if (this.filters.perspective_questions.length > 0) count++
      if (this.filters.perspective_answers.length > 0) count++
      return count
    },

    hasActiveAnnotationFilters() {
      return (
        this.annotationFilters.users.length > 0 ||
        this.annotationFilters.labels.length > 0 ||
        this.annotationFilters.examples.length > 0 ||
        this.annotationFilters.discrepancy_filter ||
        this.annotationFilters.perspective_questions.length > 0 ||
        this.annotationFilters.perspective_answers.length > 0
      )
    },

    // Filtrar respostas baseadas nas perguntas selecionadas
    filteredAnswersForSelectedQuestions() {
      if (this.filters.perspective_questions.length === 0) {
        return []
      }
      
      return this.availablePerspectiveAnswers.filter(answer =>
        this.filters.perspective_questions.includes(answer.question_id)
      )
    }
  },

  watch: {
    // Limpar respostas selecionadas quando as perguntas mudarem
    'filters.perspective_questions'() {
      // Se as perguntas mudaram, limpar as respostas que não pertencem às novas perguntas
      if (this.filters.perspective_answers.length > 0) {
        const validAnswerIds = this.filteredAnswersForSelectedQuestions.map(answer => answer.id)
        this.filters.perspective_answers = this.filters.perspective_answers.filter(answerId =>
          validAnswerIds.includes(answerId)
        )
      }
    }
  },

  async created() {
    await this.loadFilterOptions()
  },

  methods: {
    async loadFilterOptions() {
      try {
        // Carregar utilizadores do projeto (apenas anotadores)
        const members = await this.$repositories.member.list(this.projectId)
        this.availableUsers = members
          .filter((member: any) => member.rolename === 'annotator')
          .map((member: any) => ({
            id: member.user,
            username: member.username
          }))

        // Carregar projeto atual para verificar tipos disponíveis
        const currentProject = await this.$repositories.project.findById(this.projectId)

        // Carregar labels disponíveis baseado no tipo de projeto
        if (currentProject.canDefineCategory) {
          const categoryTypes = await this.$services.categoryType.list(this.projectId)
          this.availableLabels.push(
            ...categoryTypes.map((label: any) => ({
              id: label.id,
              text: label.text,
              type: 'category'
            }))
          )
        }

        if (currentProject.canDefineSpan) {
          const spanTypes = await this.$services.spanType.list(this.projectId)
          this.availableLabels.push(
            ...spanTypes.map((label: any) => ({
              id: label.id,
              text: label.text,
              type: 'span'
            }))
          )
        }

        if (currentProject.canDefineRelation) {
          const relationTypes = await this.$services.relationType.list(this.projectId)
          this.availableLabels.push(
            ...relationTypes.map((label: any) => ({
              id: label.id,
              text: label.text,
              type: 'relation'
            }))
          )
        }



        // Carregar exemplos para filtro
        try {
          const examples = await this.$repositories.example.list(this.projectId, {offset: '0', limit: '1000'})
          this.availableExamples = examples.items.map((example: any) => ({
            id: example.id,
            text: example.filename || example.text?.substring(0, 30) || `Exemplo #${example.id}`
          }))
        } catch (error) {
          console.error('Erro ao carregar exemplos:', error)
        }

        // Carregar perguntas e respostas da perspectiva
        try {
          const currentPerspective = await this.$repositories.perspective.list(this.projectId)
          if (currentPerspective) {
            const perspectiveId = currentPerspective.id
            
            // Carregar perguntas da perspectiva usando o endpoint correto
            const perspectiveQuestions = await this.$axios.get(`/v1/projects/${this.projectId}/perspectives/${perspectiveId}/questions`)
            if (perspectiveQuestions.data && Array.isArray(perspectiveQuestions.data)) {
              this.availablePerspectiveQuestions = perspectiveQuestions.data.map((question: any) => ({
                id: question.id,
                text: question.question || `Pergunta #${question.id}`
              }))
            }

            // Carregar todas as respostas disponíveis
            const allAnswers = await this.$axios.get(`/v1/answers`)
            if (allAnswers.data && Array.isArray(allAnswers.data)) {
              // Filtrar respostas que pertencem às perguntas desta perspectiva
              const questionIds = this.availablePerspectiveQuestions.map(q => q.id)
              const filteredAnswers = allAnswers.data.filter((answer: any) => 
                questionIds.includes(answer.question)
              )
              
              this.availablePerspectiveAnswers = filteredAnswers.map((answer: any) => ({
                id: answer.id,
                text: answer.answer_text || answer.answer_option || `Resposta #${answer.id}`,
                question_id: answer.question
              }))
            }
            }
        } catch (error) {
          console.error('Erro ao carregar perguntas e respostas da perspectiva:', error)
          // Não mostrar erro ao usuário pois este é um recurso opcional
          this.availablePerspectiveQuestions = []
          this.availablePerspectiveAnswers = []
        }

        // Carregar datasets disponíveis (filenames únicos)
        try {
          const examples = await this.$repositories.example.list(this.projectId, {offset: '0', limit: '10000'})
          const datasetMap = new Map()
          
          console.log('[DEBUG] Total de exemplos:', examples.items.length)
          console.log('[DEBUG] Primeiro exemplo completo:', examples.items[0])
          
          examples.items.forEach((example: any, index: number) => {
            if (index < 3) { // Debug apenas os primeiros 3
              console.log(`[DEBUG] Exemplo ${index}:`, {
                id: example.id,
                filename: example.filename,
                uploadName: example.uploadName,
                upload_name: example.upload_name
              })
            }
            
            // Lógica robusta para obter o nome completo do dataset
            let datasetName = ''
            
            // 1. Priorizar uploadName (camelCase) com extensão
            if (example.uploadName && typeof example.uploadName === 'string' && example.uploadName.includes('.')) {
              datasetName = example.uploadName
            }
            // 2. Tentar upload_name (snake_case) com extensão
            else if (example.upload_name && typeof example.upload_name === 'string' && example.upload_name.includes('.')) {
              datasetName = example.upload_name
            }
            // 3. Filename com extensão
            else if (example.filename && typeof example.filename === 'string' && example.filename.includes('.')) {
              datasetName = example.filename
            }
            // 4. Fallback para uploadName sem extensão
            else if (example.uploadName && typeof example.uploadName === 'string') {
              datasetName = example.uploadName
            }
            // 5. Fallback para upload_name sem extensão
            else if (example.upload_name && typeof example.upload_name === 'string') {
              datasetName = example.upload_name
            }
            // 6. Último recurso: filename
            else if (example.filename && typeof example.filename === 'string') {
              datasetName = example.filename
            }
            
            if (index < 3) {
              console.log(`[DEBUG] Dataset name final para exemplo ${index}:`, datasetName)
            }
            
            if (datasetName && datasetName.trim()) {
              const trimmedName = datasetName.trim()
              if (datasetMap.has(trimmedName)) {
                datasetMap.set(trimmedName, datasetMap.get(trimmedName) + 1)
              } else {
                datasetMap.set(trimmedName, 1)
              }
            }
          })
          
          this.availableDatasets = Array.from(datasetMap.entries()).map(([name, count]) => ({
            name,
            count
          }))
          
          console.log('[DEBUG] Datasets finais:', this.availableDatasets)
          console.log('[DEBUG] Primeiro dataset:', this.availableDatasets[0])
          console.log('[DEBUG] Tipos dos nomes:', this.availableDatasets.map(d => typeof d.name))
        } catch (error) {
          console.error('Erro ao carregar datasets:', error)
        }
      } catch (error) {
        console.error('Erro ao carregar opções de filtro:', error)
        this.showError('Erro ao carregar opções de filtro')
      }
    },

    async generateAndExportReport() {
      this.isGenerating = true
      try {
        // Primeiro gerar o relatório
        await this.generateReport()
        
        // Se há formatos de exportação selecionados e o relatório foi gerado com sucesso, exportar automaticamente
        if (this.filters.export_formats.length > 0 && this.reportData && this.reportData.length > 0) {
          await this.exportReport()
        }
      } catch (error) {
        console.error('Erro ao gerar e exportar relatório:', error)
        this.showError('Erro ao gerar e exportar relatório')
      } finally {
        this.isGenerating = false
      }
    },

    async generateReport() {
      try {
        // Preparar parâmetros de filtro com nomes corretos para a API
        const params = new URLSearchParams()

        // project_ids é obrigatório - usar sempre o projeto atual
        params.append('project_ids', this.projectId)

        if (this.filters.users.length > 0) {
          params.append('user_ids', this.filters.users.join(','))
        }

        if (this.filters.date_from) {
          params.append('date_from', this.filters.date_from)
        }

        if (this.filters.date_to) {
          params.append('date_to', this.filters.date_to)
        }

        if (this.filters.labels.length > 0) {
          params.append('label_ids', this.filters.labels.join(','))
        }

        if (this.filters.datasets.length > 0) {
          params.append('dataset_names', this.filters.datasets.join(','))
        }

        if (this.filters.perspective_questions.length > 0) {
          params.append('perspective_question_ids', this.filters.perspective_questions.join(','))
        }

        if (this.filters.perspective_answers.length > 0) {
          params.append('perspective_answer_ids', this.filters.perspective_answers.join(','))
        }

        console.log('[FRONTEND DEBUG] Parâmetros enviados:', params.toString())
        console.log(
          '[FRONTEND DEBUG] URL completa:',
          `/v1/reports/annotators/?${params.toString()}`
        )

        // Fazer chamada para a API
        const response = await this.$axios.get(`/v1/reports/annotators/?${params.toString()}`)
        console.log('[FRONTEND DEBUG] Resposta da API:', response)
        console.log('[FRONTEND DEBUG] Status:', response.status)
        console.log('[FRONTEND DEBUG] Data:', response.data)

        if (response.data && response.data.data) {
          this.reportData = response.data.data
          console.log(
            '[FRONTEND DEBUG] Dados do relatório definidos:',
            this.reportData.length,
            'anotadores'
          )
        } else {
          console.warn('[FRONTEND DEBUG] Estrutura de resposta inesperada:', response.data)
          this.reportData = []
        }

        // Só mostrar mensagem de sucesso se não há exportação automática
        if (this.filters.export_formats.length === 0) {
          this.showSuccess(
            `Relatório gerado com sucesso! ${this.reportData.length} anotador(es) encontrado(s).`
          )
        }
      } catch (error: any) {
        console.error('[FRONTEND DEBUG] Erro completo:', error)
        console.error('[FRONTEND DEBUG] Erro response:', error.response)
        console.error('[FRONTEND DEBUG] Erro message:', error.message)

        let errorMessage = 'Erro ao gerar relatório'
        if (error.response) {
          console.error('[FRONTEND DEBUG] Status do erro:', error.response.status)
          console.error('[FRONTEND DEBUG] Data do erro:', error.response.data)

          if (error.response.data) {
            if (error.response.data.detail) {
              errorMessage = error.response.data.detail
            } else if (error.response.data.errors) {
              errorMessage = 'Parâmetros inválidos: ' + JSON.stringify(error.response.data.errors)
            }
          }
        } else if (error.request) {
          errorMessage = 'Erro de rede - servidor não respondeu'
          console.error('[FRONTEND DEBUG] Erro de request:', error.request)
        }

        throw new Error(errorMessage)
      }
    },

    async exportReport() {
      this.isExporting = true
      try {
        // Preparar parâmetros de filtro com nomes corretos para a API
        const params = new URLSearchParams()

        // project_ids é obrigatório - usar sempre o projeto atual
        params.append('project_ids', this.projectId)

        if (this.filters.users.length > 0) {
          params.append('user_ids', this.filters.users.join(','))
        }

        if (this.filters.date_from) {
          params.append('date_from', this.filters.date_from)
        }

        if (this.filters.date_to) {
          params.append('date_to', this.filters.date_to)
        }

        if (this.filters.labels.length > 0) {
          params.append('label_ids', this.filters.labels.join(','))
        }

        if (this.filters.datasets.length > 0) {
          params.append('dataset_names', this.filters.datasets.join(','))
        }

        if (this.filters.perspective_questions.length > 0) {
          params.append('perspective_question_ids', this.filters.perspective_questions.join(','))
        }

        if (this.filters.perspective_answers.length > 0) {
          params.append('perspective_answer_ids', this.filters.perspective_answers.join(','))
        }

        // Usar os formatos selecionados nos filtros
        const exportFormats = this.filters.export_formats
        if (exportFormats.length === 0) {
          // Se nenhum formato foi selecionado, não exportar
          return
        }
        
        console.log('[EXPORT DEBUG] Formatos selecionados:', exportFormats)
        console.log('[EXPORT DEBUG] Parâmetros base:', params.toString())

        // Fazer download para cada formato selecionado
        for (const format of exportFormats) {
          const exportParams = new URLSearchParams(params)
          exportParams.append('export_format', format)
          
          console.log('[EXPORT DEBUG] Exportando formato:', format)
          
          const response = await this.$axios.get(
            `/v1/reports/annotators/export/?${exportParams.toString()}`,
            {
              responseType: 'blob'
            }
          )

          // Determinar nome do arquivo e tipo MIME baseado no formato
          let filename, mimeType
          switch (format) {
            case 'csv':
              filename = `relatorio_anotadores_${new Date().toISOString().split('T')[0]}.csv`
              mimeType = 'text/csv'
              break
            case 'pdf':
              filename = `relatorio_anotadores_${new Date().toISOString().split('T')[0]}.pdf`
              mimeType = 'application/pdf'
              break
            default:
              filename = `relatorio_anotadores_${new Date().toISOString().split('T')[0]}.${format}`
              mimeType = 'application/octet-stream'
          }

          // Criar link de download
          const blob = new Blob([response.data], { type: mimeType })
          const url = window.URL.createObjectURL(blob)
          const link = document.createElement('a')
          link.href = url
          link.download = filename
          document.body.appendChild(link)
          link.click()
          document.body.removeChild(link)
          window.URL.revokeObjectURL(url)
        }

        // Mostrar mensagem de sucesso
        let message = `Relatório gerado e exportado com sucesso!`
        if (exportFormats.length === 1) {
          message = `Relatório gerado e exportado em ${exportFormats[0].toUpperCase()} com sucesso!`
        } else {
          message = `Relatório gerado e exportado em ${exportFormats.length} formatos com sucesso!`
        }
        this.showSuccess(message)
      } catch (error: any) {
        console.error('[EXPORT DEBUG] Erro ao exportar:', error)
        this.showError('Erro ao exportar relatório')
      } finally {
        this.isExporting = false
      }
    },

    clearFilters() {
      this.filters = {
        users: [],
        date_from: null,
        date_to: null,
        labels: [],
        export_formats: [],
        datasets: [],
        perspective_questions: [],
        perspective_answers: []
      }
      this.showSuccess('Filtros limpos')
    },

    removeUser(user: any) {
      const userId = typeof user === 'object' ? user.id : user
      this.filters.users = this.filters.users.filter((id) => id !== userId)
    },

    removeLabel(label: any) {
      const labelId = typeof label === 'object' ? label.id : label
      this.filters.labels = this.filters.labels.filter((id) => id !== labelId)
    },



    removeExportFormat(format: string) {
      this.filters.export_formats = this.filters.export_formats.filter((f) => f !== format)
    },

    removeDataset(datasetName: string) {
      console.log('[DEBUG] Removendo dataset:', datasetName)
      const index = this.filters.datasets.indexOf(datasetName)
      if (index > -1) {
        this.filters.datasets.splice(index, 1)
      }
      console.log('[DEBUG] Datasets depois:', this.filters.datasets)
    },

    getDatasetDisplayName(dataset: any) {
      if (typeof dataset === 'object') {
        // Se é um objeto, usar a propriedade name
        return dataset.name || dataset
      }
      // Se é uma string, retornar diretamente
      return dataset
    },

    getLabelTypeColor(type: string) {
      const colors: {[key: string]: string} = {
        category: 'blue',
        span: 'green',
        relation: 'orange'
      }
      return colors[type] || 'grey'
    },

    formatDate(dateString: string) {
      if (!dateString) return '-'
      return new Date(dateString).toLocaleDateString('pt-PT', {
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit'
      })
    },

    showSuccess(message: string) {
      // Usar console.log apenas
        console.log('SUCCESS:', message)
      // Fallback para alert 
        alert(message)
    },

    showError(message: string) {
      // Usar console.error apenas
        console.error('ERROR:', message)
      // Fallback para alert
        alert('Erro: ' + message)
    },

    clearAnnotationFilters() {
      this.annotationFilters = {
        users: [],
        labels: [],
        examples: [],
        discrepancy_filter: null,
        perspective_questions: [],
        perspective_answers: []
      }
      this.annotationExportFormats = []
      this.annotationReportData = null
      this.annotationReportError = null
      this.filteredPerspectiveAnswers = []
    },
    
    async generateAndExportAnnotationReport() {
      this.isGeneratingAnnotations = true
      
      try {
        // Primeiro gerar o relatório
        await this.generateAnnotationReport()
        
        // Se há formatos selecionados e o relatório foi gerado com sucesso, exportar
        if (this.annotationExportFormats.length > 0 && this.annotationReportData && this.annotationReportData.data) {
          await this.exportAnnotationReport()
        } else if (this.annotationExportFormats.length === 0) {
          // Se não há formatos selecionados, apenas gerar e mostrar mensagem
          this.showSuccess('Relatório gerado com sucesso! Visualize os resultados abaixo.')
        }
      } catch (error) {
        console.error('Erro ao gerar relatório:', error)
        this.showError('Erro ao gerar relatório')
      } finally {
        this.isGeneratingAnnotations = false
      }
    },
    
    async generateAnnotationReport() {
      this.isGeneratingAnnotations = true
      this.annotationReportError = null
      
      try {
        // Construir parâmetros da query
        const params = new URLSearchParams()
        
        // Parâmetro obrigatório: project_ids
        params.append('project_ids', this.projectId)
        
        // Parâmetros opcionais
        if (this.annotationFilters.users && this.annotationFilters.users.length > 0) {
          params.append('user_ids', this.annotationFilters.users.join(','))
        }
        
        if (this.annotationFilters.labels && this.annotationFilters.labels.length > 0) {
          params.append('label_ids', this.annotationFilters.labels.join(','))
        }
        
        if (this.annotationFilters.examples && this.annotationFilters.examples.length > 0) {
          params.append('example_ids', this.annotationFilters.examples.join(','))
        }
        
        if (this.annotationFilters.discrepancy_filter) {
          params.append('discrepancy_filter', this.annotationFilters.discrepancy_filter)
        }
        
        if (this.annotationFilters.perspective_questions && this.annotationFilters.perspective_questions.length > 0) {
          params.append('perspective_question_ids', this.annotationFilters.perspective_questions.join(','))
        }
        
        if (this.annotationFilters.perspective_answers && this.annotationFilters.perspective_answers.length > 0) {
          // Expandir as respostas agrupadas para incluir todos os IDs
          const expandedAnswerIds = []
          for (const selectedAnswerId of this.annotationFilters.perspective_answers) {
            // Encontrar a resposta correspondente nas respostas filtradas
            const selectedAnswer = this.filteredPerspectiveAnswers.find(answer => answer.id === selectedAnswerId)
            if (selectedAnswer && selectedAnswer.ids) {
              // Se tem IDs agrupados, adicionar todos
              expandedAnswerIds.push(...selectedAnswer.ids)
            } else {
              // Se não tem IDs agrupados, usar o ID original
              expandedAnswerIds.push(selectedAnswerId)
            }
          }
          params.append('perspective_answer_ids', expandedAnswerIds.join(','))
          console.log('[DEBUG] Respostas selecionadas:', this.annotationFilters.perspective_answers)
          console.log('[DEBUG] IDs expandidos enviados:', expandedAnswerIds)
        }
        
        // Adicionar paginação
        params.append('page', this.annotationPage.toString())
        params.append('page_size', '50')
        
        // Fazer a requisição
        const response = await this.$axios.get(`/v1/reports/annotations/?${params.toString()}`)
        this.annotationReportData = response.data
        
      } catch (error: any) {
        console.error('Erro ao gerar relatório de anotações:', error)
        this.annotationReportError = error.response?.data?.detail || error.message || 'Erro desconhecido'
      } finally {
        this.isGeneratingAnnotations = false
      }
    },
    
    async loadAnnotationPage(page: number) {
      if (this.annotationReportData) {
        this.annotationPage = page
        await this.generateAnnotationReport()
      }
    },
    
    async exportAnnotationReport() {
      // Se não há formatos selecionados, não exportar
      if (!this.annotationExportFormats || this.annotationExportFormats.length === 0) {
        return
      }
      
      this.isExportingAnnotation = true
      
      try {
        // Construir parâmetros da query
        const params = new URLSearchParams()
        
        // Parâmetro obrigatório: project_ids
        params.append('project_ids', this.projectId)
        
        // Parâmetros opcionais
        if (this.annotationFilters.users && this.annotationFilters.users.length > 0) {
          params.append('user_ids', this.annotationFilters.users.join(','))
        }
        
        if (this.annotationFilters.labels && this.annotationFilters.labels.length > 0) {
          params.append('label_ids', this.annotationFilters.labels.join(','))
        }
        
        if (this.annotationFilters.examples && this.annotationFilters.examples.length > 0) {
          params.append('example_ids', this.annotationFilters.examples.join(','))
        }
        
        if (this.annotationFilters.discrepancy_filter) {
          params.append('discrepancy_filter', this.annotationFilters.discrepancy_filter)
        }
        
        if (this.annotationFilters.perspective_questions && this.annotationFilters.perspective_questions.length > 0) {
          params.append('perspective_question_ids', this.annotationFilters.perspective_questions.join(','))
        }
        
        if (this.annotationFilters.perspective_answers && this.annotationFilters.perspective_answers.length > 0) {
          // Expandir as respostas agrupadas para incluir todos os IDs
          const expandedAnswerIds = []
          for (const selectedAnswerId of this.annotationFilters.perspective_answers) {
            // Encontrar a resposta correspondente nas respostas filtradas
            const selectedAnswer = this.filteredPerspectiveAnswers.find(answer => answer.id === selectedAnswerId)
            if (selectedAnswer && selectedAnswer.ids) {
              // Se tem IDs agrupados, adicionar todos
              expandedAnswerIds.push(...selectedAnswer.ids)
            } else {
              // Se não tem IDs agrupados, usar o ID original
              expandedAnswerIds.push(selectedAnswerId)
            }
          }
          params.append('perspective_answer_ids', expandedAnswerIds.join(','))
          console.log('[DEBUG] Respostas selecionadas:', this.annotationFilters.perspective_answers)
          console.log('[DEBUG] IDs expandidos enviados:', expandedAnswerIds)
        }
        
        // Adicionar máximo de resultados
        params.append('max_results', this.annotationExportMaxResults.toString())
        
        // Exportar cada formato selecionado
        for (const format of this.annotationExportFormats) {
          const exportParams = new URLSearchParams(params.toString())
          exportParams.append('export_format', format)
          
          // Baixar o arquivo
          const url = `/v1/reports/annotations/export/?${exportParams.toString()}`
          
          // Fazer download usando fetch para melhor controle
          const response = await this.$axios.get(url, { responseType: 'blob' })
          
          // Determinar nome do arquivo e tipo MIME baseado no formato
          let filename, mimeType
          switch (format) {
            case 'csv':
              filename = `relatorio_anotacoes_${new Date().toISOString().split('T')[0]}.csv`
              mimeType = 'text/csv'
              break
            case 'pdf':
              filename = `relatorio_anotacoes_${new Date().toISOString().split('T')[0]}.pdf`
              mimeType = 'application/pdf'
              break
            default:
              filename = `relatorio_anotacoes_${new Date().toISOString().split('T')[0]}.${format}`
              mimeType = 'application/octet-stream'
          }
          
          // Criar link de download
          const blob = new Blob([response.data], { type: mimeType })
          const downloadUrl = window.URL.createObjectURL(blob)
          const link = document.createElement('a')
          link.href = downloadUrl
          link.download = filename
          document.body.appendChild(link)
          link.click()
          document.body.removeChild(link)
          window.URL.revokeObjectURL(downloadUrl)
        }
        
        // Mostrar mensagem de sucesso
        if (this.annotationExportFormats.length === 1) {
          this.showSuccess(`Relatório exportado com sucesso em formato ${this.annotationExportFormats[0].toUpperCase()}`)
        } else {
          this.showSuccess(`Relatório exportado com sucesso em ${this.annotationExportFormats.length} formatos`)
        }
        
      } catch (error) {
        console.error('Erro ao exportar relatório:', error)
        this.showError('Erro ao exportar relatório')
      } finally {
        this.isExportingAnnotation = false
      }
    },

    getExportFormatColor(value: string) {
      const colors: {[key: string]: string} = {
        csv: 'green',
        pdf: 'red'
      }
      return colors[value] || 'grey'
    },

    getSelectedUserText(user: any) {
      if (typeof user === 'object') {
        return user.username;
      } else if (typeof user === 'string') {
        return user;
      }
      return '';
    },

    getSelectedLabelType(label: any) {
      if (typeof label === 'object') {
        return label.type;
      } else if (typeof label === 'string') {
        return 'category'; // Assuming a default type if not provided
      }
      return '';
    },

    getSelectedLabelText(label: any) {
      if (typeof label === 'object') {
        return label.text;
      } else if (typeof label === 'string') {
        return label;
      }
      return '';
    },



    // Métodos auxiliares para filtros de discrepância
    getDiscrepancyColor(value: string) {
      const colors: {[key: string]: string} = {
        all: 'blue',
        with_discrepancy: 'orange',
        without_discrepancy: 'green'
      }
      return colors[value] || 'grey'
    },

    getDiscrepancyIcon(value: string) {
      const icons: {[key: string]: string} = {
        all: this.mdiInformation,
        with_discrepancy: this.mdiAlertCircle,
        without_discrepancy: this.mdiCheckCircle
      }
      return icons[value] || this.mdiInformation
    },

    // Métodos para remover filtros específicos
    removePerspectiveQuestion(question: any) {
      const questionId = typeof question === 'object' ? question.id : question
      this.filters.perspective_questions = this.filters.perspective_questions.filter((id) => id !== questionId)
    },

    removePerspectiveAnswer(answer: any) {
      const answerId = typeof answer === 'object' ? answer.id : answer
      this.filters.perspective_answers = this.filters.perspective_answers.filter((id) => id !== answerId)
    },

    removeAnnotationExportFormat(format: string) {
      this.annotationExportFormats = this.annotationExportFormats.filter((f) => f !== format)
    },

    onPerspectiveQuestionsChange() {
      // Limpar respostas selecionadas quando as perguntas mudam
      this.annotationFilters.perspective_answers = []
      
      // Se não há perguntas selecionadas, limpar respostas filtradas
      if (!this.annotationFilters.perspective_questions || this.annotationFilters.perspective_questions.length === 0) {
        this.filteredPerspectiveAnswers = []
        return
      }
      
      // Filtrar respostas que pertencem às perguntas selecionadas
      const answersForSelectedQuestions = this.availablePerspectiveAnswers.filter(answer =>
        this.annotationFilters.perspective_questions.includes(answer.question_id)
      )
      
      // Agrupar respostas iguais (mesmo texto) numa única opção
      const groupedAnswers = new Map()
      
      answersForSelectedQuestions.forEach(answer => {
        const answerText = answer.text.trim().toLowerCase()
        
        if (groupedAnswers.has(answerText)) {
          // Se já existe uma resposta com este texto, adicionar o ID à lista
          const existing = groupedAnswers.get(answerText)
          existing.ids.push(answer.id)
        } else {
          // Primeira resposta com este texto
          groupedAnswers.set(answerText, {
            id: answer.id, // Usar o primeiro ID encontrado
            text: answer.text, // Manter a capitalização original
            question_id: answer.question_id,
            ids: [answer.id] // Lista de todos os IDs com este texto
          })
        }
      })
      
      // Converter o Map de volta para array
      this.filteredPerspectiveAnswers = Array.from(groupedAnswers.values())
      
      console.log('[DEBUG] Perguntas selecionadas:', this.annotationFilters.perspective_questions)
      console.log('[DEBUG] Respostas filtradas:', this.filteredPerspectiveAnswers)
    },

    getSelectedAnswerText(answer: any) {
      if (typeof answer === 'object') {
        return answer.text;
      } else if (typeof answer === 'string') {
        return answer;
      }
      return '';
    },

    getSelectedPerspectiveQuestionText(question: any) {
      if (typeof question === 'object') {
        return question.text;
      } else if (typeof question === 'string') {
        return question;
      }
      return '';
    },

    getSelectedPerspectiveAnswerText(answer: any) {
      if (typeof answer === 'object') {
        return answer.text;
      } else if (typeof answer === 'string') {
        return answer;
      }
      return '';
    },

    getQuestionsWithAnswers(perspectiveData) {
      console.log('[DEBUG] getQuestionsWithAnswers chamado com:', perspectiveData)
      
      if (!perspectiveData || !perspectiveData.answers || !perspectiveData.questions) {
        console.log('[DEBUG] Dados inválidos, retornando array vazio')
        return []
      }

      // Criar um mapa de perguntas com suas respostas
      const questionsMap = new Map()
      
      // Primeiro, adicionar todas as perguntas
      perspectiveData.questions.forEach((question) => {
        questionsMap.set(question.question_id, {
          question_id: question.question_id,
          question_text: question.question_text,
          answers: []
        })
      })

      // Depois, adicionar as respostas às respectivas perguntas
      perspectiveData.answers.forEach((answer) => {
        if (questionsMap.has(answer.question_id)) {
          questionsMap.get(answer.question_id).answers.push(answer)
        }
      })

      // Converter para array e filtrar apenas perguntas que têm respostas
      const result = Array.from(questionsMap.values()).filter((question) => question.answers.length > 0)
      console.log('[DEBUG] Resultado final:', result)
      return result
    },

    // Gerar cor dinâmica para labels
    getLabelColor(label) {
      const colors = [
        'deep-purple', 'indigo', 'blue', 'light-blue', 'cyan', 
        'teal', 'green', 'light-green', 'lime', 'orange', 
        'deep-orange', 'brown', 'blue-grey', 'pink', 'purple'
      ]
      let hash = 0
      for (let i = 0; i < label.length; i++) {
        hash = label.charCodeAt(i) + ((hash << 5) - hash)
      }
      return colors[Math.abs(hash) % colors.length]
    },

    // Calcular total de anotações
    getTotalAnnotations() {
      if (!this.reportData || this.reportData.length === 0) return 0
      
      return this.reportData.reduce((total, annotator) => {
        const labelTotal = Object.values(annotator.label_breakdown || {}).reduce((sum, count) => sum + count, 0)
        return total + labelTotal
      }, 0)
    },

    // Calcular número de labels únicas
    getUniqueLabelsCount() {
      if (!this.reportData || this.reportData.length === 0) return 0
      
      const uniqueLabels = new Set()
      this.reportData.forEach(annotator => {
        if (annotator.label_breakdown) {
          Object.keys(annotator.label_breakdown).forEach(label => {
            uniqueLabels.add(label)
          })
        }
      })
      
      return uniqueLabels.size
    }
  }
})
</script>

<style scoped>
.v-chip {
  margin: 2px;
}

.v-card-title.primary {
  background: linear-gradient(45deg, #1976d2, #42a5f5);
}

.v-data-table >>> .v-data-table__wrapper {
  border-radius: 12px;
}

.v-card {
  border-radius: 12px;
}



.text-caption {
  font-size: 0.75rem !important;
}

.dataset-breakdown {
  max-width: 450px;
  padding: 8px;
}

.dataset-section {
  background: #f8f9fa;
  border-radius: 8px;
  border-left: 4px solid #009688;
  padding: 12px;
  margin-bottom: 12px;
  box-shadow: 0 1px 3px rgba(0,0,0,0.1);
}

.dataset-section:last-child {
  margin-bottom: 0;
}

.dataset-header {
  display: flex;
  align-items: center;
  margin-bottom: 8px;
  font-weight: 500;
  color: #2c3e50;
}

.dataset-name {
  font-size: 0.875rem;
  font-weight: 600;
  color: #009688;
}

.labels-in-dataset {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  padding-left: 20px;
}

.label-chip {
  margin: 0 !important;
  font-size: 0.75rem !important;
  height: 24px !important;
  transition: all 0.2s ease;
}

.label-chip:hover {
  transform: translateY(-1px);
  box-shadow: 0 2px 4px rgba(0,0,0,0.15);
}

.no-data-message {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 16px;
  background: #f5f5f5;
  border-radius: 8px;
  border: 1px dashed #ccc;
}

.label-breakdown-container {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
  padding: 4px;
}

.total-label-chip {
  margin: 0 !important;
  font-size: 0.75rem !important;
  height: 24px !important;
  transition: all 0.2s ease;
}

.total-label-chip:hover {
  transform: translateY(-1px);
  box-shadow: 0 2px 4px rgba(0,0,0,0.15);
}

.no-labels-message {
  display: flex;
  align-items: center;
  padding: 8px;
  background: #f5f5f5;
  border-radius: 6px;
  border: 1px dashed #ccc;
}

/* Estilos para as anotações consolidadas */
.labels-container {
  max-width: 280px;
  word-wrap: break-word;
}

.labels-container .v-chip {
  max-width: 100%;
  white-space: normal;
  height: auto !important;
  min-height: 24px;
  padding: 4px 8px;
}

.perspective-questions-container {
  max-width: 280px;
  word-wrap: break-word;
}

.perspective-questions-container .v-chip {
  max-width: 100%;
  white-space: normal;
  height: auto !important;
  min-height: 24px;
  padding: 4px 8px;
}

.perspective-answers-container {
  max-width: 280px;
  word-wrap: break-word;
}

.perspective-answers-container .v-chip {
  max-width: 100%;
  white-space: normal;
  height: auto !important;
  min-height: 24px;
  padding: 4px 8px;
}

.questions-list {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  padding-left: 20px;
}

.question-chip {
  margin: 0 !important;
  font-size: 0.75rem !important;
  height: 24px !important;
  transition: all 0.2s ease;
}

.question-chip:hover {
  transform: translateY(-1px);
  box-shadow: 0 2px 4px rgba(0,0,0,0.15);
}

.answers-list {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  padding-left: 20px;
}

.answer-chip {
  margin: 0 !important;
  font-size: 0.75rem !important;
  height: 24px !important;
  transition: all 0.2s ease;
}

.answer-chip:hover {
  transform: translateY(-1px);
  box-shadow: 0 2px 4px rgba(0,0,0,0.15);
}

/* Substituir CSS de perguntas e respostas separadas */
.perspective-qa-breakdown {
  max-width: 350px;
  word-wrap: break-word;
}

.question-section {
  margin-bottom: 12px;
}

.question-header {
  display: flex;
  align-items: center;
  margin-bottom: 6px;
  font-weight: 500;
  color: #3f51b5;
}

.question-name {
  font-size: 0.875rem;
  font-weight: 600;
  color: #3f51b5;
}

.answers-in-question {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  padding-left: 20px;
}

.answer-chip {
  margin: 0 !important;
  font-size: 0.75rem !important;
  height: auto !important;
  min-height: 24px;
  padding: 4px 8px;
  max-width: 100%;
  white-space: normal;
  transition: all 0.2s ease;
}

.answer-chip:hover {
  transform: translateY(-1px);
  box-shadow: 0 2px 4px rgba(0,0,0,0.15);
}



/* Estilos para containers de dados */
.labels-container {
  max-width: 280px;
  word-wrap: break-word;
}

.datasets-container {
  max-width: 400px;
  word-wrap: break-word;
}

.qa-container {
  max-width: 350px;
  word-wrap: break-word;
}

.dataset-group {
  margin-bottom: 8px;
}

.question-group {
  margin-bottom: 8px;
}
</style>
