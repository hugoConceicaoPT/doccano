<template>
  <v-card>
    <v-card-title>
      <action-menu @create="$router.push('users/add')" />
      <v-btn
        class="text-capitalize ms-2"
        outlined
        :disabled="!canDelete"
        @click.stop="dialogDelete = true"
      >
        {{ $t('generic.delete') }}
      </v-btn>
      <v-btn
       class="text-capitalize ms-2"
       outlined
      :disabled="selected.length !== 1"
      @click.stop="dialogEdit = true"
>
      {{ $t('generic.edit') }}
      </v-btn>
      <v-dialog v-model="dialogDelete">
        <form-delete
          :selected="selected"
          @remove="handleDelete"
          @cancel="dialogDelete = false"
        />
      </v-dialog>
      <v-dialog v-model="dialogEdit">
      <form-edit
      :user="selected[0]"
      @confirmEdit="handleEdit"
      @cancel="dialogEdit = false"
      />
      </v-dialog>
    </v-card-title>
    <v-navigation-drawer v-if="isSuperUser" v-model="drawerLeft" app clipped>
      <the-side-bar />
    </v-navigation-drawer>
    <user-list v-model="selected" :items="items" :is-loading="isLoading" />
  </v-card>
</template>

<script lang="ts">
import Vue from 'vue'
import { mapGetters } from 'vuex'
import ActionMenu from '@/components/user/ActionMenu.vue'
import FormDelete from '@/components/user/FormDelete.vue'
import UserList from '@/components/user/UserList.vue'
import { UserDTO } from '~/services/application/user/userData'
import TheSideBar from '@/components/user/TheSideBar.vue'
import FormEdit from '@/components/user/FormEdit.vue'


export default Vue.extend({
  components: {
    ActionMenu,
    FormDelete,
    FormEdit,
    UserList,
    TheSideBar
  },

  layout: 'projects',

  middleware: ['check-auth', 'auth', 'isSuperUser'],

  data() {
    return {
      dialogDelete: false,
      items: [] as UserDTO[],
      selected: [] as UserDTO[],
      dialogEdit: false,
      isLoading: false,
      tab: 0,
      drawerLeft: null
    }
  },

  computed: {
    ...mapGetters('auth', ['isStaff', 'isSuperUser']),

    canDelete(): boolean {
      return this.selected.length > 0
    }
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
        // Tenta excluir cada usuário selecionado
        for (const user of this.selected) {
          await this.$services.user.delete(user.id)
        }
        // Atualiza a lista removendo os usuários deletados
        this.items = this.items.filter(
          user => !this.selected.some(selectedUser => selectedUser.id === user.id)
        )
        this.selected = []
        this.dialogDelete = false // Fecha o diálogo em caso de sucesso
      } catch (error) {
        this.dialogDelete = false;

        setTimeout(() => {
          console.error("Erro ao excluir utilizadores:", error);
          const err = error as any;
          if (err.response && err.response.status === 403) {
            alert("You cannot delete your own account.");
          } else {
            alert("Error deleting users");
          }
        }, 300);
      } finally {
        this.isLoading = false
      }
    },
  async handleEdit(updatedUser: UserDTO) {
  this.isLoading = true
  try {
    await this.$services.user.update(updatedUser.id, updatedUser)

    // Atualiza localmente a lista com os dados editados
    this.items = this.items.map(user =>
      user.id === updatedUser.id ? updatedUser : user
    )

    this.dialogEdit = false
    this.selected = []
  } catch (error) {
    console.error('Erro ao editar utilizador:', error)
    alert('Erro ao editar utilizador')
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
