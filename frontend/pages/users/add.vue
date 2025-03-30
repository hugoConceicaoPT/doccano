<template>
  <div>
    <v-alert v-if="sucessMessage" type="success" dismissible>{{ sucessMessage }}</v-alert>
    <v-alert v-if="errorMessage" type="error" dismissible>{{ errorMessage }}</v-alert>
    <form-create v-bind.sync="editedItem" :items="items">
      <v-btn color="error" style="text-transform: none" @click="$router.push('/users')">
        Cancel
      </v-btn>
      <v-btn :disabled="!isFormValid" color="primary" class="text-capitalize" @click="save">
        Save
      </v-btn>
      <v-btn :disabled="!isFormValid" color="primary" style="text-transform: none" outlined @click="saveAndAnother">
        Save and add another
      </v-btn>
    </form-create>
  </div>
</template>

<script lang="ts">
import Vue from 'vue'
import FormCreate from '~/components/user/FormCreate.vue'
import { UserDTO } from '~/services/application/user/userData'

export default Vue.extend({
  components: {
    FormCreate
  },

  layout: 'projects',

  middleware: ['check-auth', 'auth'],

  data() {
    return {
      editedItem: {
        username: '',
        first_name: '',
        last_name: '',
        email: '',
        password: '',
        passwordConfirmation: '',
        isSuperUser: false,
        isStaff: false
      } as UserDTO,
      defaultItem: {
        username: '',
        first_name: '',
        last_name: '',
        email: '',
        password: '',
        passwordConfirmation: '',
        isSuperUser: false,
        isStaff: false
      } as UserDTO,
      items: [] as UserDTO[],
      errorMessage: '',
      sucessMessage: ''
    }
  },

  computed: {
    projectId(): string {
      return this.$route.params.id
    },

    isFormValid(): boolean {
      return !!this.editedItem.username && !!this.editedItem.password && !!this.editedItem.passwordConfirmation;
    },

    service(): any {
      return this.$services.user
    }
  },

  methods: {
    async save() {
      try {
        await this.service.create(this.editedItem)
        this.sucessMessage = 'The user was successfully created!'
        setTimeout(() => {
          this.$router.push(`/users`)
        }, 1000)
      } catch (error: any) {
        this.handleError(error)
      }
    },

    async saveAndAnother() {
      try {
        await this.service.create(this.editedItem)
        this.sucessMessage = 'The user was successfully created!'
        this.editedItem = Object.assign({}, this.defaultItem)
        this.items = await this.service.list()
      } catch (error) {
        this.handleError(error)
      }
    },

    handleError(error: any) {
      this.editedItem = Object.assign({}, this.defaultItem)
      if (error.response && error.response.status === 400) {
        const errors = error.response.data
        if (errors.username) {
          this.errorMessage = errors.username[0]
        } else if (errors.email) {
          this.errorMessage = errors.email[0]
        } else {
          this.errorMessage = JSON.stringify(errors)
        }
      } else {
        this.errorMessage = 'Database is slow or unavailable. Please try again later.'
      }
    }
  }
})
</script>
