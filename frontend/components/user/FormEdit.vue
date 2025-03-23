<template>
    <base-card
      :title="$t('Edit User')"
      :agree-text="$t('generic.save')"
      :cancel-text="$t('generic.cancel')"
      @agree="submit"
      @cancel="$emit('cancel')"
    >
      <template #content>
        <v-form v-model="valid" ref="form">
          <v-text-field
            v-model="formData.username"
            :label="$t('Username')"
            :rules="[rules.required]"
          />
          <v-text-field
            v-model="formData.password"
            :label="$t('Password (leave blank to keep unchanged)')"
            type="password"
          />
        </v-form>
      </template>
    </base-card>
  </template>
  
  <script lang="ts">
  import Vue from 'vue'
  import BaseCard from '@/components/utils/BaseCard.vue'
  import { UserDTO } from '~/services/application/user/userData'
  
  export default Vue.extend({
    components: {
      BaseCard
    },
  
    props: {
      user: {
        type: Object as () => UserDTO,
        required: true
      }
    },
  
    data() {
      return {
        formData: {
          id: this.user.id,
          username: this.user.username,
          password: ''
        },
        valid: false,
        rules: {
          required: (v: string) => !!v || 'Required'
        }
      }
    },
  
    methods: {
      submit() {
        const form = this.$refs.form as Vue & { validate: () => boolean }
        if (!form.validate()) return
  
        const updatedUser = {
          id: this.formData.id,
          username: this.formData.username,
        }
  
        // Só inclui a senha se o usuário digitou algo
        if (this.formData.password) {
          Object.assign(updatedUser, { password: this.formData.password })
        }
  
        this.$emit('confirmEdit', updatedUser)
      }
    }
  })
  </script>
  