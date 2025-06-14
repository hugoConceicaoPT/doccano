<template>
  <div>
    <v-card>
      <v-alert
        v-if="errorMessage"
        class="mx-4 my-4"
        type="error"
        dismissible
        @click="errorMessage = ''"
      >
        {{ errorMessage }}
      </v-alert>
      <v-card-title> Side-by-Side Annotation Comparison </v-card-title>
      <v-card-text>
        <v-row>
          <v-col cols="12" md="6">
            <v-select
              v-model="selectedUser1"
              :items="userOptions"
              label="Select first user"
              dense
              outlined
              clearable
              hide-details
              :loading="isLoadingUsers"
              no-data-text="No users found"
              class="mb-4"
            />
          </v-col>
          <v-col cols="12" md="6">
            <v-select
              v-model="selectedUser2"
              :items="userOptions"
              label="Select second user"
              dense
              outlined
              clearable
              hide-details
              :loading="isLoadingUsers"
              no-data-text="No users found"
              class="mb-4"
            />
          </v-col>
        </v-row>

        <v-select
          v-if="selectedUser1 && selectedUser2"
          v-model="selectedExample"
          :items="exampleOptions"
          label="Select an annotation with discrepancy"
          dense
          outlined
          clearable
          hide-details
          :loading="isLoading"
          no-data-text="No discrepant annotations found"
          class="mb-4"
        />

        <v-btn
          v-if="selectedUser1 && selectedUser2 && selectedExample"
          color="primary"
          class="mt-4"
          :loading="isLoadingAnnotation"
          @click="viewDiscrepancy"
        >
          View Comparison
        </v-btn>
      </v-card-text>
    </v-card>

    <!-- New section to show annotation comparison -->
    <v-card v-if="showComparison" class="mt-4">
      <v-card-title>
        Annotation Comparison:
        {{ selectedExample ? exampleNameMap[selectedExample] || selectedExample : '' }}
        <v-spacer></v-spacer>
        <v-btn icon @click="showComparison = false">
          <v-icon>mdi-close</v-icon>
        </v-btn>
      </v-card-title>

      <!-- Section to show original example text -->
      <v-card-subtitle v-if="exampleText" class="pb-0"> Original Text </v-card-subtitle>
      <v-card-text v-if="exampleText" class="pt-1 pb-4">
        <v-card outlined class="pa-4">
          <div v-if="isLoadingExampleText" class="text-center">
            <v-progress-circular indeterminate color="primary"></v-progress-circular>
          </div>
          <div v-else>
            <pre class="example-text">{{ exampleText }}</pre>
          </div>
        </v-card>
      </v-card-text>

      <v-card-subtitle class="pb-0"> User Annotations </v-card-subtitle>
      <v-card-text class="pt-1">
        <v-row>
          <v-col cols="12" md="6">
            <v-card outlined>
              <v-card-title>{{ selectedUser1 ? getUsernameById(selectedUser1) : '' }}</v-card-title>
              <v-card-text>
                <div v-if="isLoadingAnnotation" class="text-center">
                  <v-progress-circular indeterminate color="primary"></v-progress-circular>
                </div>
                <div v-else>
                  <p v-if="labelsUser1.length > 0" class="mb-2">Labels used:</p>
                  <div v-if="labelsUser1.length > 0" class="d-flex flex-wrap">
                    <v-chip
                      v-for="label in labelsUser1"
                      :key="label.id"
                      class="ma-1"
                      color="primary"
                      small
                    >
                      {{ label.text }}
                    </v-chip>
                  </div>
                  <p v-else>No labels used</p>
                </div>
              </v-card-text>
            </v-card>
          </v-col>
          <v-col cols="12" md="6">
            <v-card outlined>
              <v-card-title>{{ selectedUser2 ? getUsernameById(selectedUser2) : '' }}</v-card-title>
              <v-card-text>
                <div v-if="isLoadingAnnotation" class="text-center">
                  <v-progress-circular indeterminate color="primary"></v-progress-circular>
                </div>
                <div v-else>
                  <p v-if="labelsUser2.length > 0" class="mb-2">Labels used:</p>
                  <div v-if="labelsUser2.length > 0" class="d-flex flex-wrap">
                    <v-chip
                      v-for="label in labelsUser2"
                      :key="label.id"
                      color="primary"
                      small
                      class="ma-1"
                    >
                      {{ label.text }}
                    </v-chip>
                  </div>
                  <p v-else>No labels used</p>
                </div>
              </v-card-text>
            </v-card>
          </v-col>
        </v-row>
      </v-card-text>
    </v-card>
  </div>
</template>

<script lang="ts">
import Vue from 'vue'
import { Percentage, Progress } from '~/domain/models/metrics/metrics'
import { MemberItem } from '~/domain/models/member/member'

interface LabelInfo {
  id: number
  text: string
}

interface UserProgress {
  userId: number
  username: string
  done: number
}

export default Vue.extend({
  
  layout: 'project',
  middleware: ['check-auth', 'auth', 'setCurrentProject', 'project-closed'],

  data() {
    return {
      items: {} as Percentage,
      isLoading: false,
      isLoadingUsers: false,
      isLoadingAnnotation: false,
      isLoadingExampleText: false,
      selectedExample: null as string | null,
      selectedUser1: null as number | null,
      selectedUser2: null as number | null,
      exampleNameMap: {} as Record<string, string>,
      members: [] as MemberItem[],
      userProgress: [] as UserProgress[],
      errorMessage: '',
      minPercentage: 0,
      showComparison: false,
      labelsUser1: [] as LabelInfo[],
      labelsUser2: [] as LabelInfo[],
      exampleText: null as string | null,
      categoryTypes: [] as any[],
      totalExamples: 0
    }
  },

  async fetch() {
    this.isLoading = true
    try {
      // Get project to access minPercentage
      const project = await this.$repositories.project.findById(this.projectId)
      if (project && project.minPercentage !== undefined) {
        this.minPercentage = project.minPercentage
      }

      this.items = await this.$repositories.metrics.fetchCategoryPercentage(this.projectId)
      await this.loadExampleNames(this.items)

      // Load category types (needed for labels)
      this.categoryTypes = await this.$repositories.categoryType.list(this.projectId)
    } catch (error) {
      this.handleError(error)
    }
    this.isLoading = false
  },

  computed: {
    projectId(): string {
      return this.$route.params.id
    },

    discrepancyThreshold(): number {
      return this.minPercentage
    },

    // Filter only users who have annotation progress
    userOptions(): Array<{ text: string; value: number }> {
      return this.userProgress
        .filter((user) => user.done > 0)
        .map((user) => ({
          text: user.username,
          value: user.userId
        }))
    },

    exampleOptions(): Array<{ text: string; value: string }> {
      const options = []

      for (const [exampleId, labels] of Object.entries(this.items)) {
        const hasDiscrepancy = !Object.values(labels).some(
          (percentage) => percentage > this.discrepancyThreshold
        )

        if (hasDiscrepancy && this.exampleNameMap[exampleId]) {
          options.push({
            text: this.exampleNameMap[exampleId],
            value: exampleId
          })
        }
      }

      return options
    }
  },

  async created() {
    await this.fetchMembers()
  },

  methods: {
    async fetchMembers() {
      this.isLoadingUsers = true
      try {
        // Fetch project members
        this.members = await this.$repositories.member.list(this.projectId)

        // Fetch member progress
        const progress: Progress = await this.$repositories.metrics.fetchMemberProgress(
          this.projectId
        )
        this.totalExamples = progress.total

        // Map progress for each user
        this.userProgress = []

        // For each member, find their corresponding progress
        for (const member of this.members) {
          const userProgressItem = progress.progress.find((p) => {
            // Username format may vary, so we try to find by partial match
            return p.user.includes(member.username) || member.username.includes(p.user)
          })

          if (userProgressItem) {
            this.userProgress.push({
              userId: member.user,
              username: member.username,
              done: userProgressItem.done
            })
          }
        }

        // Sort by number of completed annotations (descending)
        this.userProgress.sort((a, b) => b.done - a.done)
      } catch (error) {
        this.handleError(error)
      }
      this.isLoadingUsers = false
    },

    getUsernameById(userId: number): string {
      const member = this.members.find((m) => m.user === userId)
      return member ? member.username : `User ${userId}`
    },

    async resolveExampleName(id: string) {
      if (!this.exampleNameMap[id]) {
        try {
          const example = await this.$repositories.example.findById(this.projectId, Number(id))
          this.$set(this.exampleNameMap, id, example.filename.replace(/\.[^/.]+$/, ''))
        } catch (error) {
          console.error('Error loading example name:', error)
        }
      }
      return this.exampleNameMap[id]
    },

    async loadExampleNames(items: Percentage) {
      const exampleNames = Object.keys(items)
      await Promise.all(exampleNames.map(this.resolveExampleName))
    },

    async fetchExampleText(exampleId: string) {
      this.isLoadingExampleText = true
      this.exampleText = null

      try {
        // Fetch example text
        const example = await this.$repositories.example.findById(this.projectId, Number(exampleId))
        if (example && example.text) {
          this.exampleText = example.text
        } else {
          // If text not found directly, try to fetch raw data
          this.exampleText = JSON.stringify(example, null, 2)
        }
      } catch (error) {
        console.error('Error fetching example text:', error)
        this.exampleText = 'Error loading example text.'
      } finally {
        this.isLoadingExampleText = false
      }
    },

    async viewDiscrepancy() {
      if (this.selectedUser1 && this.selectedUser2 && this.selectedExample) {
        this.isLoadingAnnotation = true
        this.showComparison = true
        this.labelsUser1 = []
        this.labelsUser2 = []
        this.exampleText = null

        try {
          // Load example text
          await this.fetchExampleText(this.selectedExample)

          const exampleId = Number(this.selectedExample)

          // Fetch user 1 annotations
          try {
            // Fetch all available categories (category types/labels)
            if (this.categoryTypes.length === 0) {
              this.categoryTypes = await this.$repositories.categoryType.list(this.projectId)
            }

            // Fetch categories for specific example - passing true for allUsers
            // to ensure we see categories from all users
            const categories = await this.$repositories.category.list(
              this.projectId,
              exampleId,
              true // Add allUsers parameter as true
            )

            console.log('Categories found:', categories)

            // Filter categories for user 1
            const userCategories1 = categories.filter(
              (category) => category.user === this.selectedUser1
            )

            console.log('User 1 categories:', userCategories1)

            // Map categories to get label information
            this.labelsUser1 = userCategories1.map((category) => {
              const categoryType = this.categoryTypes.find((t) => t.id === category.label)
              return {
                id: category.label,
                text: categoryType ? categoryType.text : `Label ID ${category.label}`
              }
            })

            // Filter categories for user 2
            const userCategories2 = categories.filter(
              (category) => category.user === this.selectedUser2
            )

            console.log('User 2 categories:', userCategories2)

            // Map categories to get label information
            this.labelsUser2 = userCategories2.map((category) => {
              const categoryType = this.categoryTypes.find((t) => t.id === category.label)
              return {
                id: category.label,
                text: categoryType ? categoryType.text : `Label ID ${category.label}`
              }
            })
          } catch (error: any) {
            console.error('Error fetching annotations:', error)
            this.errorMessage = `Database is slow or unavailable. Please try again later.`
          }
        } catch (error) {
          this.handleError(error)
        } finally {
          this.isLoadingAnnotation = false
        }
      }
    },

    async getLabelNames(labelIds: number[]): Promise<string[]> {
      try {
        // Fetch category types if not already loaded
        if (this.categoryTypes.length === 0) {
          this.categoryTypes = await this.$repositories.categoryType.list(this.projectId)
        }

        // Map IDs to names
        return labelIds.map((id) => {
          const categoryType = this.categoryTypes.find((type) => type.id === id)
          return categoryType ? categoryType.text : `Label ID ${id}`
        })
      } catch (error: any) {
        console.error('Error fetching label names:', error)
        return labelIds.map((id) => `Label ID ${id}`)
      }
    },

    handleError(error: any) {
      if (error.response && error.response.status === 400) {
        this.errorMessage = 'Error retrieving data.'
      } else {
        this.errorMessage =
          'The database is slow or unavailable. Please try again later.'
      }
    }
  }
})
</script>

<style scoped>
::v-deep .v-dialog {
  width: 800px;
}

pre {
  white-space: pre-wrap;
  word-wrap: break-word;
  background-color: #f5f5f5;
  padding: 10px;
  border-radius: 4px;
  font-size: 14px;
  max-height: 400px;
  overflow-y: auto;
}

.example-text {
  background-color: #f8f9fa;
  border-left: 4px solid #3f51b5;
}
</style>
