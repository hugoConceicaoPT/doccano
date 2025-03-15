<template>
  <v-card>
    <v-car-title>
      <v-card-title>
        <action-menu @create="$router.push('users/add')" />
        <v-btn class="text-capitalize ms-2" outlined @click.stop="dialogDelete = true">
          {{ $t('generic.delete') }}
        </v-btn>
        <v-dialog v-model="dialogDelete">
          <form-delete :selected="selected" @cancel="dialogDelete = false" />
        </v-dialog>
      </v-card-title>
    </v-car-title>
    <label-list v-model="selected" :items="items" :is-loading="isLoading" />
  </v-card>
</template>

<script lang="ts">
import Vue from 'vue'
import ActionMenu from '@/components/user/ActionMenu.vue'
import FormDelete from '@/components/user/FormDelete.vue'
import LabelList from '@/components/label/LabelList.vue'
import { UserDTO } from '~/services/application/user/userData'

export default Vue.extend({
  components: {
    ActionMenu,
    FormDelete,
    LabelList
  },

  layout: 'projects',

  middleware: ['check-auth', 'auth'],

  data() {
    return {
      dialogDelete: false,
      items: [] as UserDTO[],
      selected: [] as UserDTO[],
      isLoading: false,
      tab: 0
    }
  }
})
</script>

<style scoped>
::v-deep .v-dialog {
  width: 800px;
}
</style>
