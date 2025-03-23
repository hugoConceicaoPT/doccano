<template>
  <v-card>
    <v-card-title>
      <action-menu @create="$router.push('perspectives/add')" />
      <v-btn class="text-capitalize ms-2" outlined @click.stop="dialogDelete = true">
        {{ $t('generic.delete') }}
      </v-btn>
      <v-dialog v-model="dialogDelete">
        <form-delete :selected="selected" @remove="handleDelete" @cancel="dialogDelete = false" />
      </v-dialog>
    </v-card-title>
    <user-list v-model="selected" :items="items" :is-loading="isLoading" />
  </v-card>
</template>

<script lang="ts">
import Vue from 'vue'
import { mapGetters } from 'vuex'
import ActionMenu from '@/components/perspective/ActionMenu.vue'
import FormDelete from '@/components/user/FormDelete.vue'
import UserList from '@/components/user/UserList.vue'
import { UserDTO } from '~/services/application/user/userData'

export default Vue.extend({
  components: {
    ActionMenu,
    FormDelete,
    UserList
  },

  layout: 'project',

  middleware: ['check-auth', 'auth', 'isSuperUser', 'setCurrentProject'],

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
  },

  mounted() {
    this.fetchUsers()
  },

  methods: {
    async fetchUsers() {
      this.isLoading = true
      try {
        const response = await this.$services.user.list()
        this.items = response
      } catch (error) {
        console.error('Erro ao buscar utilizadores:', error)
      } finally {
        this.isLoading = false
      }
    },
    async deleteUser(userId: number) {
      this.isLoading = true
      try {
        await this.$services.user.delete(userId)
        this.items = this.items.filter((user) => user.id !== userId)
      } catch (error) {
        console.error('Erro ao excluir utilizador:', error)
      } finally {
        this.isLoading = false
      }
    },
    async handleDelete() {
      this.isLoading = true
      try {
        // Exclui cada usuário selecionado
        for (const user of this.selected) {
          await this.$services.user.delete(user.id)
        }
        // Atualiza a lista removendo os usuários deletados
        this.items = this.items.filter(
          (user) => !this.selected.some((selectedUser) => selectedUser.id === user.id)
        )
        // Limpa a seleção e fecha o diálogo
        this.selected = []
        this.dialogDelete = false
      } catch (error) {
        console.error('Erro ao excluir utilizadores:', error)
      } finally {
        this.isLoading = false
      }
    }
  }
})
</script>

<style scoped>
::v-deep .v-dialog {
  width: 800px;
}
</style>
