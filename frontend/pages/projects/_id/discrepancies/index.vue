<template>
    <div>
        <v-card>
            <v-alert v-if="errorMessage" class="mx-4 my-4" type="error" dismissible @click="errorMessage = ''">
                {{ errorMessage }}
            </v-alert>
            <v-card-title>
                Discrepancy Threshold: {{ this.project && this.project.minPercentage !== undefined ? this.project.minPercentage : '-' }} %
            </v-card-title>
            <discrepancy-list v-model="selected" :items="items" :isLoading="isLoading"
                :discrepancyThreshold="this.project && this.project.minPercentage !== undefined ? this.project.minPercentage : 0" />
        </v-card>
    </div>
</template>

<script lang="ts">
import Vue from 'vue'
import { mapGetters } from 'vuex'
import DiscrepancyList from '~/components/discrepancy/DiscrepancyList.vue'
import { Percentage } from '~/domain/models/metrics/metrics'

export default Vue.extend({
    components: {
        DiscrepancyList,
    },

    layout: 'project',

    middleware: ['check-auth', 'auth'],


    data() {
        return {
            items: {} as Percentage,
            isLoading: false,
            drawerLeft: null,
            selected: {} as Percentage,
            errorMessage: '',
        }
    },

    async fetch() {
        this.isLoading = true
        try {
            this.items = await this.$repositories.metrics.fetchCategoryPercentage(this.projectId)
        } catch (error) {
            this.handleError(error)
        }
        this.isLoading = false
    },

    computed: {
        ...mapGetters('projects',   ['project']),

        projectId(): string {
            return this.$route.params.id
        },
    },

    watch: {
        project: {
            handler(newVal) {
                if (newVal) {
                    this.$fetch();
                }
            },
            immediate: true,
            deep: true
        }
    },
    methods: {
        handleError(error: any) {
            if (error.response && error.response.status === 400) {
                this.errorMessage = 'Error retrieving data.'
            } else {
                this.errorMessage = 'Database is slow or unavailable. Please try again later.'
            }
        },
    }
})
</script>

<style scoped>
::v-deep .v-dialog {
    width: 800px;
}
</style>