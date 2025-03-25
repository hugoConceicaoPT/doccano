<template>
  <form-create v-bind.sync="editedItem" :items="items">
    <v-btn :disabled="!isFormValid" color="primary" class="text-capitalize" @click="save">
      Save
    </v-btn>

    <v-btn
      :disabled="!isFormValid"
      color="primary"
      style="text-transform: none"
      outlined
      @click="saveAndAnother"
    >
      Save and add another
    </v-btn>
  </form-create>
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

  middleware: ['check-auth', 'auth', 'setCurrentProject'],

  data() {
    return {
      editedItem: {
        username: '',
        firstName: '',
        lastName: '',
        email: '',
        password: '',
        passwordConfirmation: '',
        isSuperUser: false,
        isStaff: false
      } as UserDTO,
      defaultItem: {
        username: '',
        firstName: '',
        lastName: '',
        email: '',
        password: '',
        passwordConfirmation: '',
        isSuperUser: false,
        isStaff: false
      } as UserDTO,
      items: [] as UserDTO[]
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
      await this.service.create(this.editedItem)
      this.$router.push(`/users`)
    },

    async saveAndAnother() {
      await this.service.create(this.editedItem)
      this.editedItem = Object.assign({}, this.defaultItem)
      this.items = await this.service.list()
    }
  }
})
</script>
