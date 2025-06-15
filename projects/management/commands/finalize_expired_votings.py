from django.core.management.base import BaseCommand
from django.utils import timezone
from projects.models import Project
from projects.views.rule import check_and_finalize_expired_votings
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Finaliza automaticamente as regras de votações que já expiraram'

    def add_arguments(self, parser):
        parser.add_argument(
            '--project-id',
            type=int,
            help='ID específico do projeto para verificar (opcional)',
        )

    def handle(self, *args, **options):
        self.stdout.write('Iniciando verificação de votações expiradas...')
        
        project_id = options.get('project_id')
        
        if project_id:
            # Verificar projeto específico
            try:
                project = Project.objects.get(id=project_id)
                self.stdout.write(f'Verificando projeto: {project.name} (ID: {project_id})')
                check_and_finalize_expired_votings(project_id)
                self.stdout.write(self.style.SUCCESS(f'Projeto {project_id} verificado com sucesso'))
            except Project.DoesNotExist:
                self.stdout.write(self.style.ERROR(f'Projeto com ID {project_id} não encontrado'))
        else:
            # Verificar todos os projetos
            projects = Project.objects.all()
            total_projects = projects.count()
            self.stdout.write(f'Verificando {total_projects} projetos...')
            
            for project in projects:
                try:
                    check_and_finalize_expired_votings(project.id)
                    self.stdout.write(f'✓ Projeto {project.id}: {project.name}')
                except Exception as e:
                    self.stdout.write(
                        self.style.ERROR(f'✗ Erro no projeto {project.id}: {str(e)}')
                    )
                    logger.error(f'Erro ao verificar projeto {project.id}: {str(e)}')
            
            self.stdout.write(
                self.style.SUCCESS(f'Verificação concluída para {total_projects} projetos')
            )
        
        self.stdout.write('Verificação de votações expiradas finalizada.') 