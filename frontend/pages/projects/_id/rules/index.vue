<template>
    <v-card>
      <v-alert v-if="successMessage" type="success" dismissible @click="successMessage = ''">
        {{ successMessage }}
      </v-alert>
      <v-alert v-if="errorMessage" type="error" dismissible @click="errorMessage = ''">
        {{ errorMessage }}
      </v-alert>
      <v-card-title>Annotation Rules Voting</v-card-title>
      <v-card-text>
        <v-container>
          <v-btn color="primary" @click="$router.push({ path: '/projects/' + projectId + '/rules/add' })">
        Configurar
          </v-btn>
        </v-container>
      </v-card-text>
    </v-card>
  </template>
  
  <script lang="ts">
  import Vue from 'vue';
  
  export default Vue.extend({
    layout: 'project',
    middleware: ['check-auth', 'auth', 'setCurrentProject'],
    data() {
      return {
        successMessage: '',
        errorMessage: '',
      };
    },
    computed: {
      projectId(): string {
        return this.$route.params.id;
      },
    },
  });
  </script>