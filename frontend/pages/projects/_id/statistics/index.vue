<template>
    <v-row>
        <v-col v-if="!!project.canDefineCategory" cols="12">
            <non-discrepancy-progress :categoryPercentage="categoryPercentage" :project="this.project" />
        </v-col>
        <v-col v-if="!!project.canDefineCategory" cols="12">
            <label-percentage-distribution title="Label Discrepancy Percentage" :distribution="categoryPercentage"
                :label-types="categoryTypes" :examples="examples" />
        </v-col>
    </v-row>
</template>

<script>
import { mapGetters } from 'vuex'
import NonDiscrepancyProgress from '~/components/statistics/NonDiscrepancyProgress.vue'
import LabelPercentageDistribution from '~/components/statistics/LabelPercentageDistribution'

export default {
    components: {
        LabelPercentageDistribution,
        NonDiscrepancyProgress
    },

    layout: 'project',

    middleware: ['check-auth', 'auth', 'setCurrentProject', 'isProjectAdmin'],

    validate({ params }) {
        return /^\d+$/.test(params.id)
    },

    data() {
        return {
            categoryTypes: [],
            categoryPercentage: {},
            examples: {}
        }
    },

    computed: {
        ...mapGetters('projects', ['project']),

        projectId() {
            return this.$route.params.id
        }
    },

    watch: {
        '$route.query': _.debounce(function () {
            // @ts-ignore
            this.$fetch()
        }, 1000)
    },
    async created() {
        if (this.project.canDefineCategory) {
            this.categoryTypes = await this.$services.categoryType.list(this.projectId)
            this.categoryPercentage = await this.$repositories.metrics.fetchCategoryPercentage(this.projectId)
            this.examples = await this.$services.example.list(this.projectId, this.$route.query)
        }
    }
}
</script>