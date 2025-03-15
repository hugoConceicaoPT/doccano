<template>
  <v-list dense>
    <v-list-item-group v-model="selected" mandatory>
      <v-list-item
        v-for="(item, i) in filteredItems"
        :key="i"
        @click="$router.push(localePath(`/${item.link}`))"
      >
        <v-list-item-action>
          <v-icon>
            {{ item.icon }}
          </v-icon>
        </v-list-item-action>
        <v-list-item-content>
          <v-list-item-title>
            {{ item.text }}
          </v-list-item-title>
        </v-list-item-content>
      </v-list-item>
    </v-list-item-group>
  </v-list>
</template>

<script>
import { mdiDeveloperBoard, mdiAccount, mdiPlayCircleOutline } from '@mdi/js'

export default {
  props: {
    isSuperUser: {
      type: Boolean,
      default: false
    }
  },

  data() {
    return {
      selected: 0,
      mdiPlayCircleOutline
    }
  },

  computed: {
    filteredItems() {
      const items = [
        {
          icon: mdiDeveloperBoard,
          text: 'Projects',
          link: 'projects',
          isVisible: true
        },
        {
          icon: mdiAccount,
          text: 'Users',
          link: 'users',
          isVisible: true
        }
      ]
      return items.filter((item) => item.isVisible)
    }
  }
}
</script>
