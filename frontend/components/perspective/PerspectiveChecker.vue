<template>
  <!-- Dialog de aviso para utilizadores sem perspectiva -->
  <v-dialog v-model="showDialog" persistent max-width="500">
    <v-card>
      <v-card-title class="warning white--text">
        <v-icon left color="white">mdi-alert</v-icon>
        No personal perspective defined
      </v-card-title>
      <v-card-text class="pa-4">
        <div class="text-center">
          <v-icon size="80" color="warning" class="mb-4">mdi-clipboard-alert-outline</v-icon>
          <h3 class="text-h6 mb-3">Personal perspective required</h3>
          <p class="text-body-1 grey--text">
            To start annotating, you must first define your personal perspective by answering the questions configured for this project.
          </p>
          <p class="text-body-2 grey--text">
            This helps ensure consistency and quality of annotations.
          </p>
        </div>
      </v-card-text>
      <v-card-actions>
        <v-spacer />
        <v-btn 
          color="grey" 
          text 
          @click="handleCancel"
        >
          Cancel
        </v-btn>
        <v-btn 
          color="primary" 
          @click="handleGoToPerspective"
        >
          <v-icon left>mdi-clipboard-text</v-icon>
          Define Perspective
        </v-btn>
      </v-card-actions>
    </v-card>
  </v-dialog>
</template>

<script lang="ts">
import Vue from 'vue'

export default Vue.extend({
  name: 'PerspectiveChecker',
  
  props: {
    projectId: {
      type: [String, Number],
      required: true
    },
    isProjectAdmin: {
      type: Boolean,
      default: false
    }
  },

  data() {
    return {
      showDialog: false,
      isChecking: false
    }
  },

  methods: {
    /**
     * Main method to check perspective and proceed or show warning
     * @returns {Promise<boolean>} true if can proceed, false if dialog was shown
     */
    async checkPerspectiveAndProceed(): Promise<boolean> {
      // Admins don't need perspective verification - they can annotate without defined perspective
      if (this.isProjectAdmin) {
        return true
      }

      // For non-admins, check if they have defined perspective
      this.isChecking = true
      
      try {
        const hasPerspective = await this.checkUserHasPerspective()
        
        if (hasPerspective) {
          // User has defined perspective, can proceed to annotation
          return true
        } else {
          // User doesn't have defined perspective, show warning
          this.showDialog = true
          return false
        }
      } catch (error) {
        console.error('Error checking perspective:', error)
        // In case of error, allow proceeding (to not block completely)
        return true
      } finally {
        this.isChecking = false
      }
    },

    /**
     * Checks if current user has registered perspective answers
     * @returns {Promise<boolean>} true if has answers, false otherwise
     */
    async checkUserHasPerspective(): Promise<boolean> {
      try {
        // Fetch current user's answers
        const answers = await this.$services.answer.list()
        
        // Check if there's at least one answer from user in current project
        if (!answers || answers.length === 0) {
          return false
        }

        // Fetch user's role in project to get member ID
        const memberRole = await this.$repositories.member.fetchMyRole(this.projectId.toString())
        if (!memberRole) {
          return false
        }

        // Check if there's at least one answer from this member
        const userAnswers = answers.filter(answer => answer.member === memberRole.id)
        
        return userAnswers.length > 0
      } catch (error) {
        console.error('Error checking user perspective:', error)
        throw error
      }
    },

    /**
     * Handle dialog cancellation
     * @emits cancelled
     */
    handleCancel(): void {
      this.showDialog = false
      this.$emit('cancelled')
    },

    /**
     * Redirect to perspectives page
     * @emits redirected-to-perspective
     */
    handleGoToPerspective(): void {
      this.showDialog = false
      const perspectiveRoute = this.$nuxt.localePath(`/projects/${this.projectId}/perspectives`)
      this.$router.push(perspectiveRoute)
      this.$emit('redirected-to-perspective')
    }
  }
})
</script>

<style scoped>
.v-dialog .v-card-title.warning {
  background-color: #ff9800 !important;
}

.v-dialog .v-card {
  border-radius: 8px !important;
}

.v-icon.mdi-clipboard-alert-outline {
  opacity: 0.8;
}
</style> 