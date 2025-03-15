<template>
  <v-card>
    <v-card-title>Create a User</v-card-title>
    <v-card-text>
      <v-form ref="form" v-model="valid">
        <v-row>
          <v-col cols="12" sm="12">
            <v-text-field
              :value="username"
              :counter="100"
              :label="'Username'"
              :rules="[rules.required, rules.counter, rules.nameDuplicated]"
              outlined
              required
              @input="$emit('update:username', $event)"
            />
          </v-col>
        </v-row>
        <v-row>
          <v-col cols="12" sm="12">
            <v-text-field
              id="password"
              v-model="localPassword"
              :append-icon="show2 ? mdiEye : mdiEyeOff"
              :counter="30"
              name="password"
              :rules="[
                rules.required,
                rules.counter,
                rules.minLength,
                rules.noCommonWords,
                rules.hasNumberAndSpecialChar,
                rules.notSimilarToPersonalInfo
              ]"
              :type="show2 ? 'text' : 'password'"
              :label="$t('user.password')"
              outlined
              @click:append="show2 = !show2"
              @input="$emit('update:password', localPassword)"
            />
          </v-col>
        </v-row>

        <v-row>
          <v-col cols="12" sm="12">
            <v-text-field
              id="passwordConfirmation"
              v-model="localPasswordConfirmation"
              :append-icon="show1 ? mdiEye : mdiEyeOff"
              :counter="30"
              name="passwordConfirmation"
              :rules="[rules.required, rules.counter, rules.passwordsMatch]"
              :type="show1 ? 'text' : 'password'"
              :label="$t('user.passwordConfirmation')"
              outlined
              @click:append="show1 = !show1"
              @input="$emit('update:passwordConfirmation', localPasswordConfirmation)"
            />
          </v-col>
        </v-row>

        <v-row>
          <v-col cols="12" sm="6">
            <v-switch
              v-model="localisSuperUser"
              label="isSuperUser"
              outlined
              @change="$emit('update:isSuperUser', localisSuperUser)"
            >
            </v-switch>
          </v-col>
          <v-col cols="12" sm="6">
            <v-switch
              v-model="localIsStaff"
              label="isStaff"
              outlined
              @change="$emit('update:isStaff', localIsStaff)"
            >
            </v-switch>
          </v-col>
        </v-row>

        <v-row>
          <v-col cols="12" sm="12">
            <slot :valid="valid" />
          </v-col>
        </v-row>
      </v-form>
    </v-card-text>
  </v-card>
</template>

<script lang="ts">
import { mdiReload, mdiEye, mdiEyeOff } from '@mdi/js'
import type { PropType } from 'vue'
import Vue from 'vue'
import { UserDTO } from '~/services/application/user/userData'

export default Vue.extend({
  props: {
    items: {
      type: Array as PropType<UserDTO[]>,
      default: () => [],
      required: true
    },
    id: {
      type: Number as () => number | undefined,
      default: undefined
    },
    username: {
      type: String,
      required: true
    },
    password: {
      type: String,
      required: true
    },
    passwordConfirmation: {
      type: String,
      required: true
    },
    isSuperUser: {
      type: Boolean,
      default: false
    },
    isStaff: {
      type: Boolean,
      default: false
    }
  },

  data() {
    return {
      localPassword: this.password,
      localPasswordConfirmation: this.passwordConfirmation,
      localIsStaff: this.isStaff,
      localisSuperUser: this.isSuperUser,
      selectedColorIndex: 0,
      valid: false,
      rules: {
        passwordsMatch: (
          v: string // @ts-ignore
        ) => this.isEqual(v) || 'Passwords must match',
        required: (v: string) => !!v || 'Required',
        counter: (
          v: string // @ts-ignore
        ) => (v && v.length <= 100) || this.$t('rules.userNameRules').userNameLessThan30Chars,
        nameDuplicated: (
          v: string // @ts-ignore
        ) => !this.isUsedName(v) || this.$t('rules.userNameRules').duplicated,
        minLength: (v: string) =>
          (v && v.length >= 8) || 'Your password must contain at least 8 characters.',
        noCommonWords: (v: string) => {
          const commonWords = ['password', '123456', 'qwerty', 'letmein', 'admin']
          return (
            !commonWords.some((word) => v.toLowerCase().includes(word)) ||
            'Avoid using common words or sequences.'
          )
        },
        hasNumberAndSpecialChar: (v: string) => {
          const hasNumber = /\d/.test(v)
          const hasSpecialChar = /[!@#$%^&*(),.?":{}|<>]/.test(v)
          return (
            (hasNumber && hasSpecialChar) || 'It should include numbers and special characters.'
          )
        },
        notSimilarToPersonalInfo: (v: string) => {
          if (!v) return true // If empty, let 'required' rule handle it
          const personalInfo = [this.username] // Add more fields if needed
          for (const info of personalInfo) {
            if (info && v.toLowerCase().includes(info.toLowerCase()))
              return 'Your password can’t be too similar to your other personal information.'
          }
          return true
        }
      },
      mdiReload,
      show2: false,
      mdiEye,
      mdiEyeOff,
      show1: false
    }
  },

  watch: {
    password(newVal) {
      this.localPassword = newVal
    },
    passwordConfirmation(newVal) {
      this.localPasswordConfirmation = newVal
    }
  },

  methods: {
    isUsedName(username: string): boolean {
      return (
        this.items.filter((item) => item.id !== this.id && item.username === username).length > 0
      )
    },
    isEqual(v: string): boolean {
      return v === this.localPassword
    }
  }
})
</script>
