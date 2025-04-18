<template>
    <v-card>
        <v-card-title>
            Discrepancy Threshold: {{ this.project.minPercentage }} %
        </v-card-title>
        <discrepancy-list v-model="selected" :items="items" :isLoading="isLoading" :discrepancyThreshold="this.project.minPercentage" />
    </v-card>
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

    middleware: ['check-auth', 'auth', 'isSuperUser', 'setCurrentProject'],


    data() {
        return {
            items: {} as Percentage,
            isLoading: false,
            drawerLeft: null,
            selected: {} as Percentage
        }
    },

    async fetch() {
        this.isLoading = true
        if (this.project.canDefineCategory) {
            this.items = await this.$repositories.metrics.fetchCategoryPercentage(this.projectId)
        }
        if (this.project.canDefineSpan) {
            this.items = await this.$repositories.metrics.fetchSpanPercentage(this.projectId)
        }
        if (this.project.canDefineRelation) {
            this.items = await this.$repositories.metrics.fetchRelationPercentage(this.projectId)
        }
        this.isLoading = false
    },

    computed: {
        ...mapGetters('projects', ['project']),

        projectId(): string {
            return this.$route.params.id
        },
    },

    watch: {
        project: {
            handler(newVal) {
                if (newVal && (newVal.canDefineCategory || newVal.canDefineSpan || newVal.canDefineRelation)) {
                    this.$fetch();
                }
            },
            immediate: true,
            deep: true
        }
    }
})
</script>

<style scoped>
::v-deep .v-dialog {
    width: 800px;
}
</style>