<template>
    <v-row>
        <v-col cols="12">
            <perspective-percentage-distribution title="Perspective Distribution" :distribution="perspectiveDistribution"
                 />
        </v-col>
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
import PerspectivePercentageDistribution from '~/components/statistics/PerspectivePercentageDistribution.vue'

export default {
    components: {
        LabelPercentageDistribution,
        NonDiscrepancyProgress,
        PerspectivePercentageDistribution
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
            examples: {},
            perspectiveDistribution: {}
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
        this.categoryTypes = await this.$services.categoryType.list(this.projectId)
        this.categoryPercentage = await this.$repositories.metrics.fetchCategoryPercentage(this.projectId)
        this.perspectiveDistribution = await this.$repositories.statistics.fetchPerspectiveAnswerDistribution(this.projectId)
        this.examples = await this.$services.example.list(this.projectId, this.$route.query)
    }
}
</script>