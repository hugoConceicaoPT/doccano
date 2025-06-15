<template>
  <v-list dense>
    <v-btn color="ms-4 my-1 mb-2 primary text-capitalize" nuxt @click="toLabeling">
      <v-icon left>
        {{ mdiPlayCircleOutline }}
      </v-icon>
      {{ $t('home.startAnnotation') }}
    </v-btn>
    
    <!-- Dialog de aviso para utilizadores sem perspectiva -->
    <v-dialog v-model="perspectiveWarningDialog" persistent max-width="500">
      <v-card>
        <v-card-title class="warning white--text">
          <v-icon left color="white">mdi-alert</v-icon>
          Sem perspectiva pessoal definida
        </v-card-title>
        <v-card-text class="pa-4">
          <div class="text-center">
            <v-icon size="80" color="warning" class="mb-4">mdi-clipboard-alert-outline</v-icon>
            <h3 class="text-h6 mb-3">Perspectiva pessoal necessária</h3>
            <p class="text-body-1 grey--text">
              Para começar a anotar, precisa primeiro de definir a sua perspectiva pessoal respondendo às questões configuradas para este projeto.
            </p>
            <p class="text-body-2 grey--text">
              Isto ajuda a garantir a consistência e qualidade das anotações.
            </p>
          </div>
        </v-card-text>
        <v-card-actions>
          <v-spacer />
          <v-btn 
            color="grey" 
            text 
            @click="perspectiveWarningDialog = false"
          >
            Cancelar
          </v-btn>
          <v-btn 
            color="primary" 
            @click="goToPerspective"
          >
            <v-icon left>mdi-clipboard-text</v-icon>
            Definir Perspectiva
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
    
    <v-list-item-group v-model="selected" mandatory>
      <v-list-item
        v-for="(item, i) in filteredItems"
        :key="i"
        @click="$router.push(localePath(`/projects/${$route.params.id}/${item.link}`))"
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
import {
  mdiAccount,
  mdiBookOpenOutline,
  mdiChartBar,
  mdiCog,
  mdiCommentAccountOutline,
  mdiDatabase,
  mdiHome,
  mdiLabel,
  mdiPlayCircleOutline,
  mdiCommentTextOutline,
  mdiArrowCollapse,
  mdiChartBoxOutline,
  mdiProgressPencil,
  mdiFileDocumentOutline,
  mdiCompare,
  mdiVote
} from '@mdi/js'
import { getLinkToAnnotationPage } from '~/presenter/linkToAnnotationPage'

export default {
  props: {
    isProjectAdmin: {
      type: Boolean,
      default: false,
      required: true
    },
    project: {
      type: Object,
      default: () => {},
      required: true
    }
  },

  data() {
    return {
      selected: null,
      mdiPlayCircleOutline,
      perspectiveWarningDialog: false,
      isCheckingPerspective: false
    }
  },

  computed: {
    filteredItems() {
      const items = [
        {
          icon: mdiHome,
          text: this.$t('projectHome.home'),
          link: '',
          isVisible: true
        },
        {
          icon: mdiDatabase,
          text: this.$t('dataset.dataset'),
          link: 'dataset',
          isVisible: true
        },
        {
          icon: mdiLabel,
          text: this.$t('labels.labels'),
          link: 'labels',
          isVisible:
            (this.isProjectAdmin || this.project.allowMemberToCreateLabelType) &&
            this.project.canDefineLabel
        },
        {
          icon: mdiLabel,
          text: 'Relations',
          link: 'links',
          isVisible:
            (this.isProjectAdmin || this.project.allowMemberToCreateLabelType) &&
            this.project.canDefineRelation
        },
        {
          icon: mdiAccount,
          text: this.$t('members.members'),
          link: 'members',
          isVisible: this.isProjectAdmin
        },
        {
          icon: mdiCommentTextOutline,
          text: 'Perspective',
          link: 'perspectives',
          isVisible: true
        },
        {
          icon: mdiArrowCollapse,
          text: 'Discrepancy',
          link: 'discrepancies',
          isVisible: this.isProjectAdmin
        },
        {
          icon: mdiProgressPencil,
          text: 'Annotations Rules',
          link: 'rules',
          isVisible: this.isProjectAdmin
        },
        {
          icon: mdiVote,
          text: 'Votação',
          link: 'voting',
          isVisible: !this.isProjectAdmin
        },
        {
          icon: mdiCompare,
          text: 'Discrepancies Side To Side',
          link: 'discrepancies-side-to-side',
          isVisible: this.isProjectAdmin
        },
        {
          icon: mdiCommentAccountOutline,
          text: 'Comments',
          link: 'comments',
          isVisible: this.isProjectAdmin
        },
        {
          icon: mdiFileDocumentOutline,
          text: 'Reports',
          link: 'reports',
          isVisible: this.isProjectAdmin
        },
        {
          icon: mdiBookOpenOutline,
          text: this.$t('guideline.guideline'),
          link: 'guideline',
          isVisible: this.isProjectAdmin
        },
        {
          icon: mdiChartBar,
          text: this.$t('statistics.statistics'),
          link: 'metrics',
          isVisible: this.isProjectAdmin
        },
        {
          icon: mdiChartBoxOutline,
          text: 'Statistics',
          link: 'statistics',
          isVisible: this.isProjectAdmin
        },
        {
          icon: mdiCog,
          text: this.$t('settings.title'),
          link: 'settings',
          isVisible: this.isProjectAdmin
        }
      ]
      return items.filter((item) => item.isVisible)
    }
  },
  methods: {
    async toLabeling() {
      // Admins não precisam de verificação de perspectiva - podem anotar sem perspectiva definida
      if (this.isProjectAdmin) {
        this.proceedToAnnotation()
        return
      }

      // Para não-admins, verificar se tem perspectiva definida
      this.isCheckingPerspective = true
      
      try {
        const hasPerspective = await this.checkUserHasPerspective()
        
        if (hasPerspective) {
          // Utilizador tem perspectiva definida, pode prosseguir para anotação
          this.proceedToAnnotation()
        } else {
          // Utilizador não tem perspectiva definida, mostrar aviso
          this.perspectiveWarningDialog = true
        }
      } catch (error) {
        console.error('Erro ao verificar perspectiva:', error)
        // Em caso de erro, permitir prosseguir (para não bloquear totalmente)
        this.proceedToAnnotation()
      } finally {
        this.isCheckingPerspective = false
      }
    },

    async checkUserHasPerspective() {
      try {
        // Buscar respostas do utilizador atual
        const answers = await this.$services.answer.list()
        
        // Verificar se existe pelo menos uma resposta do utilizador no projeto atual
        if (!answers || answers.length === 0) {
          return false
        }

        // Buscar o papel do utilizador no projeto para obter o member ID
        const memberRole = await this.$repositories.member.fetchMyRole(this.$route.params.id)
        if (!memberRole) {
          return false
        }

        // Verificar se existe pelo menos uma resposta deste membro
        const userAnswers = answers.filter(answer => answer.member === memberRole.id)
        
        return userAnswers.length > 0
      } catch (error) {
        console.error('Erro ao verificar perspectiva do utilizador:', error)
        throw error
      }
    },

    proceedToAnnotation() {
      const query = this.$services.option.findOption(this.$route.params.id)
      const link = getLinkToAnnotationPage(this.$route.params.id, this.project.projectType)
      this.$router.push({
        path: this.localePath(link),
        query
      })
    },

    goToPerspective() {
      this.perspectiveWarningDialog = false
      this.$router.push(this.localePath(`/projects/${this.$route.params.id}/perspectives`))
    }
  }
}
</script>
