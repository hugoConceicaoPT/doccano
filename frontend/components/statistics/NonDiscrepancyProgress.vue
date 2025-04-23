<template>
    <v-card>
        <v-card-title>Non Discrepancy Progress</v-card-title>
        <v-divider />
        <v-card-text>
            <div v-for="(item, index) in stats.progress" :key="index" class="mb-2">
                <span class="font-weight-medium">{{ item.user }}</span>
                <span class="font-weight-medium">{{ item.done }} / {{ stats.total }}</span>
                <v-progress-linear :value="rate(item.done, stats.total)" />
            </div>
        </v-card-text>
    </v-card>
</template>

<script lang="ts">
import Vue from 'vue'
import { PropType } from 'vue/types/v3-component-props'
import { Percentage } from '~/domain/models/metrics/metrics'
import { Project } from '~/domain/models/project/project'

export default Vue.extend({
    props: {
        categoryPercentage: {
            type: Object as PropType<Percentage>,
            default: () => {},
            required: true
        },
        project: {
            type: Object as PropType<Project>,
            required: true
        }
    },

    computed: {
        stats() {
            const examples = Object.keys(this.categoryPercentage ?? {})
            let done = 0

            examples.forEach(exampleId => {
                const labelData = this.categoryPercentage?.[exampleId] ?? ''
                const hasMin = Object.values(labelData ?? '').some(p => p >= this.project.minPercentage )
                if (hasMin) done += 1
            })

            return {
                total: examples.length,
                progress: [
                    { user: this.project.name, done }
                ]
            }
        }
    },
    methods: {
        rate(done: number, total: number) {
            return (done / total) * 100
        }
    }
})
</script>