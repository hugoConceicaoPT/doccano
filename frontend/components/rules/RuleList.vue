<template>
    <div>
        <v-select v-model="selectedVersion" :items="availableVersions" label="Select the version"
            clearable class="my-4 mx-4" />

        <v-select v-model="selectedRule" :items="availableRules" label="Select the rule" clearable
            class="mb-4 mx-4" />

        <v-data-table class="mx-4" :items="filteredItems" :headers="headers" :loading="isLoading"
            :loading-text="$t('generic.loading')" :no-data-text="$t('vuetify.noDataAvailable')" :footer-props="{
                showFirstLastPage: true,
                'items-per-page-text': $t('vuetify.itemsPerPageText'),
                'page-text': $t('dataset.pageText')
            }" item-key='exampleName + id' @input="$emit('input', $event)">
            <template #top>
                <v-text-field v-model="search" :prepend-inner-icon="mdiMagnify" :label="$t('generic.search')"
                    single-line hide-details filled />
            </template>
            <template #[`header.data-table-select`]>
            </template>
            <template #[`item.numberVersion`]="{ item }">
                {{ item.numberVersion }}
            </template>

            <template #[`item.ruleDiscussion`]="{ item }">
                {{ item.ruleDiscussion }}
            </template>

            <template #[`item.result`]="{ item }">
                <v-chip :color="item.result === 'Approved' ? 'success' 
                            : item.result === 'Rejected' ? 'error'
                            : 'warning'" dark>
                    {{ item.result }}
                </v-chip>
            </template>
        </v-data-table>
    </div>
</template>

<script lang="ts">
import Vue from 'vue'
import type { PropType } from 'vue'
import { mdiMagnify, mdiPencil } from '@mdi/js'
import { Discussion } from '~/pages/projects/_id/rules/index.vue'

export default Vue.extend({
    props: {
        isLoading: {
            type: Boolean,
            default: false,
            required: true
        },
        items: {
            type: Array as PropType<Discussion[]>,
            required: true
        },
    },

    data() {
        return {
            search: '',
            mdiMagnify,
            mdiPencil,
            selectedVersion: null as string | null,
            exampleNameMap: {} as Record<string, string>,
            selectedRule: null as string | null,
            isReady: false
        }
    },

    computed: {
        headers() {
            return [
                { text: 'Version', value: 'numberVersion', sortable: true },  
                { text: 'Rule', value: 'ruleDiscussion', sortable: true },
                { text: 'Result', value: 'result', sortable: true }
            ]
        },
        projectId(): string {
            return this.$route.params.id
        },
        filteredItems(): Discussion[] {
            let result = this.items.filter(item =>
                item.numberVersion.toLowerCase().includes(this.search.toLowerCase()) || item.ruleDiscussion.toLowerCase().includes(this.search.toLowerCase())
            )

            if (this.selectedVersion) {
                result = result.filter(item => item.numberVersion === this.selectedVersion)
            }
            if (this.selectedRule) {
                result = result.filter(item => item.ruleDiscussion === this.selectedRule)
            }

            return result
        },
        availableVersions(): string[] {
            if (!this.selectedRule) {
                return [...new Set(this.items.map(item => item.numberVersion))]
            }

            return [...new Set(
                this.items
                    .filter(item => item.ruleDiscussion === this.selectedRule)
                    .map(item => item.numberVersion)
            )]
        },
        availableRules(): string[] {
            if (!this.selectedVersion) {
                return [...new Set(this.items.map(item => item.ruleDiscussion))]
            }

            return [...new Set(
                this.items
                    .filter(item => item.numberVersion === this.selectedVersion)
                    .map(item => item.ruleDiscussion)
            )]
        }
    },
})
</script>

<style scoped>
.container {
    padding-left: 20px;
    padding-right: 20px;
    margin-top: 10px;
}
</style>