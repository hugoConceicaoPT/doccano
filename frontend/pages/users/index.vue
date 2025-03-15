<template>
  <v-card>
    <v-card-title>
      <action-menu @create="$router.push('users/add')" />
      <v-btn class="text-capitalize ms-2" outlined @click.stop="dialogDelete = true">
        {{ $t('generic.delete') }}
      </v-btn>
      <v-dialog v-model="dialogDelete">
        <form-delete :selected="selected" @cancel="dialogDelete = false" />
      </v-dialog>
    </v-card-title>
    <v-navigation-drawer v-if="isSuperUser" v-model="drawerLeft" app clipped>
      <the-side-bar />
    </v-navigation-drawer>
    <label-list v-model="selected" :items="items" :is-loading="isLoading" />
  </v-card>
</template>

<script lang="ts">
import Vue from 'vue'
import { mapGetters } from 'vuex'
import ActionMenu from '@/components/user/ActionMenu.vue'
import FormDelete from '@/components/user/FormDelete.vue'
import LabelList from '@/components/label/LabelList.vue'
import { UserDTO } from '~/services/application/user/userData'
import TheSideBar from '~/components/user/TheSideBar.vue'

export default Vue.extend({
  components: {
    ActionMenu,
    FormDelete,
    LabelList,
    TheSideBar
  },

  layout: 'projects',

  middleware: ['check-auth', 'auth', 'isSuperUser'],

  data() {
    return {
      dialogDelete: false,
      items: [] as UserDTO[],
      selected: [] as UserDTO[],
      isLoading: false,
      tab: 0,
      drawerLeft: null
    }
  },

  computed: {
    ...mapGetters('auth', ['isStaff', 'isSuperUser'])
  }
})
</script>

<style scoped>
::v-deep .v-dialog {
  width: 800px;
}
</style>
