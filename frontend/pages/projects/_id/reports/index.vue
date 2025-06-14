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
                          <v-list-item-subtitle class="text-caption">ID: {{ item.id }}</v-list-item-subtitle>
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
                          <v-list-item-subtitle class="text-caption">Tipo: {{ item.type }}</v-list-item-subtitle>
                        </v-list-item-content>
                      </template>
                    </v-autocomplete>
                  </v-col>

                  <!-- Filtro de Perspectivas -->
                  <v-col cols="12" md="6">
                    <v-autocomplete
                      v-model="filters.perspectives"
                      :items="availablePerspectives"
                      item-text="name"
                      item-value="id"
                      label="Perspectivas"
                      multiple
                      chips
                      deletable-chips
                      clearable
                      outlined
                      dense
                      :prepend-inner-icon="mdiEye"
                      hint="Selecione perspectivas específicas ou deixe vazio para todas"
                      persistent-hint
                    >
                      <template #selection="{ item, index }">
                        <v-chip
                          v-if="index < 2"
                          small
                          close
                          color="purple"
                          text-color="white"
                          @click:close="removePerspective(item)"
                        >
                          {{ getSelectedPerspectiveText(item) }}
                        </v-chip>
                        <span v-if="index === 2" class="grey--text text-caption">
                          (+{{ filters.perspectives.length - 2 }} outras)
                        </span>
                      </template>
                      <template #item="{ item }">
                        <v-list-item-avatar>
                          <v-icon color="purple">{{ mdiEye }}</v-icon>
                        </v-list-item-avatar>
                        <v-list-item-content>
                          <v-list-item-title>{{ item.name }}</v-list-item-title>
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
                      <template #selection="{ item, index }">
                        <v-chip
                          v-if="index < 2"
                          small
                          close
                          color="teal"
                          text-color="white"
                          @click:close="() => removeDataset(item)"
                        >
                          {{ item }}
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
                          <v-list-item-subtitle class="text-caption">{{ item.count }} exemplo(s)</v-list-item-subtitle>
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
              <v-data-table
                v-if="reportData && reportData.length > 0"
                :headers="tableHeaders"
                :items="reportData"
                :loading="isGenerating"
                class="elevation-2"
                :items-per-page="15"
                :footer-props="{
                  'items-per-page-options': [10, 15, 25, 50, -1],
                  'items-per-page-text': 'Itens por página:'
                }"
                loading-text="Carregando dados..."
                no-data-text="Nenhum dado disponível"
              >
                <template #top>
                  <v-toolbar flat color="grey lighten-4">
                    <v-toolbar-title class="text-h6">
                      <v-icon left>{{ mdiTable }}</v-icon>
                      Resultados do Relatório
                    </v-toolbar-title>
                    <v-spacer />
                    <v-chip color="primary" outlined> {{ reportData.length }} anotador(es) </v-chip>
                  </v-toolbar>
                </template>

                <template #[`item.label_breakdown`]="{ item }">
                  <div class="label-breakdown-container">
                    <v-chip
                      v-for="(count, label) in item.label_breakdown"
                      :key="label"
                      small
                      class="total-label-chip"
                      color="secondary"
                    >
                      {{ label }}: {{ count }}
                    </v-chip>
                    <div
                      v-if="Object.keys(item.label_breakdown).length === 0"
                      class="no-labels-message"
                    >
                      <v-icon small color="grey">{{ mdiInformationOutline }}</v-icon>
                      <span class="grey--text text-caption ml-1">Nenhuma label</span>
                    </div>
                  </div>
                </template>

                <template #[`item.dataset_label_breakdown`]="{ item }">
                  <div class="dataset-breakdown">
                    <div
                      v-for="(labels, dataset) in item.dataset_label_breakdown"
                      :key="dataset"
                      class="dataset-section"
                    >
                      <div class="dataset-header">
                        <v-icon small color="teal" class="mr-1">{{ mdiDatabase }}</v-icon>
                        <span class="dataset-name">{{ dataset }}</span>
                      </div>
                      <div class="labels-in-dataset">
                        <v-chip
                          v-for="(count, label) in labels"
                          :key="`${dataset}-${label}`"
                          small
                          class="label-chip"
                          color="primary"
                          outlined
                        >
                          {{ label }}
                        </v-chip>
                      </div>
                    </div>
                    <div
                      v-if="!item.dataset_label_breakdown || Object.keys(item.dataset_label_breakdown).length === 0"
                      class="no-data-message"
                    >
                      <v-icon small color="grey">{{ mdiInformationOutline }}</v-icon>
                      <span class="grey--text text-caption ml-1">Nenhuma anotação encontrada</span>
                    </div>
                  </div>
                </template>
              </v-data-table>

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
                  <v-icon left>{{ mdiDownload }}</v-icon>
                  Gerar e Exportar Relatório
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
                      
                      <!-- Formato de Exportação -->
                      <v-col cols="12" md="6">
                        <v-select
                          v-model="annotationExportFormat"
                          :items="exportFormatOptions"
                          item-text="text"
                          item-value="value"
                          label="Formato de Exportação"
                          outlined
                          dense
                          :prepend-inner-icon="mdiFileDelimited"
                          hint="Selecione o formato para exportar o relatório"
                          persistent-hint
                        >
                          <template #selection="{ item }">
                            <v-chip small :color="getExportFormatColor(item.value)" text-color="white">
                              <v-icon small left>{{ item.icon }}</v-icon>
                              {{ item.text }}
                            </v-chip>
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
                      <template #[`item.detail`]="{ item }">
                        <v-tooltip bottom>
                          <template #activator="{ on, attrs }">
                            <v-btn
                              x-small
                              icon
                              v-bind="attrs"
                              v-on="on"
                            >
                              <v-icon small>{{ mdiInformationOutline }}</v-icon>
                            </v-btn>
                          </template>
                          <span>
                            {{ item.detail ? JSON.stringify(item.detail) : 'Sem detalhes' }}
                          </span>
                        </v-tooltip>
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
  mdiDatabase
} from '@mdi/js'
import datasetNameMixin from '~/mixins/datasetName.js'

declare module 'vue/types/vue' {
  interface Vue {
    $axios: any
  }
}

export default Vue.extend({
  mixins: [datasetNameMixin],

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
    isGenerating: boolean;
    dateFromMenu: boolean;
    dateToMenu: boolean;
    filters: {
      users: number[];
      date_from: string | null;
      date_to: string | null;
      labels: number[];
      perspectives: number[];
      export_formats: string[];
      datasets: string[];
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
    };
    isGeneratingAnnotations: boolean;
    annotationReportData: any;
    annotationReportError: string | null;
    annotationSearch: string;
    annotationHeaders: Array<{text: string; value: string; width?: string; sortable?: boolean}>;
    annotationPage: number;
    annotationExportFormat: string;
    annotationExportMaxResults: number;
    isExportingAnnotation: boolean;
    availableExamples: Array<{id: number; text: string}>;
    exportFormatOptions: Array<{value: string; text: string; icon: string; description: string}>;
    availablePerspectives: Array<{id: number; name: string}>;
    availableDatasets: Array<{name: string; count: number}>;
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

      isGenerating: false,
      dateFromMenu: false,
      dateToMenu: false,

      filters: {
        users: [] as number[],
        date_from: null as string | null,
        date_to: null as string | null,
        labels: [] as number[],
        perspectives: [] as number[],
        export_formats: [] as string[],
        datasets: [] as string[]
      },

      availableUsers: [] as Array<{id: number; username: string}>,
      availableLabels: [] as Array<{id: number; text: string; type: string}>,

      reportData: [] as any[],

      tableHeaders: [
        { text: 'Utilizador', value: 'annotator_username', sortable: true, width: '140px' },
        { text: 'Nome', value: 'annotator_name', sortable: true, width: '180px' },
        { text: 'Total por Label', value: 'label_breakdown', sortable: false, width: '220px' },
        { text: 'Labels por Dataset', value: 'dataset_label_breakdown', sortable: false, width: '460px' }
      ],

      isExporting: false,

      activeTab: 'annotators',
      
      // Dados para relatório de anotações
      annotationFilters: {
        users: [] as number[],
        labels: [] as number[],
        examples: [] as number[],
      },
      isGeneratingAnnotations: false,
      annotationReportData: null as any,
      annotationReportError: null as string | null,
      annotationSearch: '',
      annotationHeaders: [
        { text: 'ID', value: 'id', width: '70px' },
        { text: 'Exemplo', value: 'example_name' },
        { text: 'Utilizador', value: 'username', width: '130px' },
        { text: 'Label', value: 'label_text', width: '150px' },
        { text: 'Data', value: 'created_at', width: '180px' },
        { text: 'Detalhes', value: 'detail', width: '80px', sortable: false }
      ],
      annotationPage: 1,
      annotationExportFormat: 'csv',
      annotationExportMaxResults: 1000000,
      isExportingAnnotation: false,
      availableExamples: [] as Array<{id: number; text: string}>,
      exportFormatOptions: [
        { value: 'csv', text: 'CSV (Comma Separated Values)', icon: mdiFileDelimited, description: 'Ideal para Excel e análise de dados' },
        { value: 'pdf', text: 'PDF (Portable Document Format)', icon: mdiFilePdfBox, description: 'Documento formatado para visualização e impressão' }
      ],
      availablePerspectives: [] as Array<{id: number; name: string}>,
      availableDatasets: [] as Array<{name: string; count: number}>
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
        this.filters.perspectives.length > 0 ||
        this.filters.export_formats.length > 0 ||
        this.filters.date_from ||
        this.filters.date_to ||
        this.filters.datasets.length > 0
      )
    },

    getActiveFiltersCount() {
      let count = 0
      if (this.filters.users.length > 0) count++
      if (this.filters.labels.length > 0) count++
      if (this.filters.perspectives.length > 0) count++
      if (this.filters.export_formats.length > 0) count++
      if (this.filters.date_from) count++
      if (this.filters.date_to) count++
      if (this.filters.datasets.length > 0) count++
      return count
    }
  },

  async created() {
    await this.loadFilterOptions()
  },

  methods: {
    async loadFilterOptions() {
      try {
        // Carregar utilizadores do projeto
        const members = await this.$repositories.member.list(this.projectId)
        this.availableUsers = members.map((member: any) => ({
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

        // Carregar perspectivas disponíveis
        try {
          const perspective = await this.$repositories.perspective.list(this.projectId)
          if (perspective) {
            this.availablePerspectives = [{
              id: perspective.id,
              name: perspective.name
            }]
          } else {
            this.availablePerspectives = []
          }
        } catch (error) {
          console.error('Erro ao carregar perspectivas:', error)
          this.availablePerspectives = []
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

        if (this.filters.perspectives.length > 0) {
          params.append('perspective_ids', this.filters.perspectives.join(','))
        }

        if (this.filters.datasets.length > 0) {
          params.append('dataset_names', this.filters.datasets.join(','))
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

        if (this.filters.perspectives.length > 0) {
          params.append('perspective_ids', this.filters.perspectives.join(','))
        }

        if (this.filters.datasets.length > 0) {
          params.append('dataset_names', this.filters.datasets.join(','))
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
        perspectives: [],
        export_formats: [],
        datasets: []
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

    removePerspective(perspective: any) {
      const perspectiveId = typeof perspective === 'object' ? perspective.id : perspective
      this.filters.perspectives = this.filters.perspectives.filter((id) => id !== perspectiveId)
    },

    removeExportFormat(format: string) {
      this.filters.export_formats = this.filters.export_formats.filter((f) => f !== format)
    },

    removeDataset(dataset: string) {
      console.log('[DEBUG] Removendo dataset:', dataset)
      console.log('[DEBUG] Tipo do dataset:', typeof dataset)
      console.log('[DEBUG] Datasets antes:', this.filters.datasets)
      console.log('[DEBUG] Tipos dos datasets:', this.filters.datasets.map(d => typeof d))
      
      // Garantir que estamos a comparar strings
      const datasetStr = String(dataset)
      const newDatasets = this.filters.datasets.filter((d) => String(d) !== datasetStr)
      
      // Usar Vue.set para garantir reatividade
      this.$set(this.filters, 'datasets', newDatasets)
      console.log('[DEBUG] Datasets depois:', this.filters.datasets)
      
      // Forçar atualização do componente
      this.$forceUpdate()
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
      }
      this.annotationReportData = null
      this.annotationReportError = null
    },
    
    async generateAndExportAnnotationReport() {
      this.isGeneratingAnnotations = true
      
      try {
        // Primeiro gerar o relatório
        await this.generateAnnotationReport()
        
        // Se o relatório foi gerado com sucesso, exportar
        if (this.annotationReportData && this.annotationReportData.data && this.annotationReportData.data.length > 0) {
          await this.exportAnnotationReport()
        }
      } catch (error) {
        console.error('Erro ao gerar e exportar relatório:', error)
        this.showError('Erro ao gerar e exportar relatório')
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
        
        // Adicionar formato e máximo de resultados
        params.append('export_format', this.annotationExportFormat)
        params.append('max_results', this.annotationExportMaxResults.toString())
        
        // Baixar o arquivo
        const url = `/v1/reports/annotations/export/?${params.toString()}`
        
        // Abrir em uma nova janela e aguardar
        await new Promise<void>((resolve) => {
          window.open(url, '_blank')
          // Resolver após um breve delay para garantir que a janela foi aberta
          setTimeout(() => resolve(), 100)
        })
        
        this.showSuccess(`Relatório exportado com sucesso em formato ${this.annotationExportFormat.toUpperCase()}`)
        
      } catch (error) {
        console.error('Erro ao exportar relatório:', error)
        this.showError(`Erro ao exportar relatório em formato ${this.annotationExportFormat.toUpperCase()}`)
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

    getSelectedPerspectiveText(perspective: any) {
      if (typeof perspective === 'object') {
        return perspective.name;
      } else if (typeof perspective === 'string') {
        return perspective;
      }
      return '';
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
  border-radius: 8px;
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
</style>
