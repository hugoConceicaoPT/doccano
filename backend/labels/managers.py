from django.db.models import Count, Manager
import logging

logger = logging.getLogger(__name__)


class LabelManager(Manager):
    label_type_field = "label"

    def calc_label_distribution(self, examples, members, labels):
        """Calculate label distribution.

        Args:
            examples: example queryset.
            members: user queryset.
            labels: label queryset.

        Returns:
            label distribution per user.

        Examples:
            >>> self.calc_label_distribution(examples, members, labels)
            {'admin': {'positive': 10, 'negative': 5}}
        """
        try:
            logger.info(f"Calculando distribuição de labels para {members.count()} membros e {labels.count()} labels")
            
            # Converter querysets para listas se necessário
            if hasattr(examples, 'values_list'):
                example_ids = list(examples.values_list('id', flat=True))
            else:
                example_ids = list(examples)
            
            # Inicializar distribuição com zeros
            distribution = {}
            for member in members:
                distribution[member.username] = {}
                for label in labels:
                    distribution[member.username][label.text] = 0
            
            logger.info(f"Distribuição inicializada para {len(distribution)} utilizadores")
            
            # Se não há examples ou labels, retornar distribuição vazia
            if not example_ids or not labels.exists():
                logger.info("Nenhum example ou label encontrado, retornando distribuição vazia")
                return distribution
            
            # Query para obter contagens - usar try/except para capturar erros de SQL
            try:
                items = (
                    self.filter(example_id__in=example_ids)
                    .values("user__username", f"{self.label_type_field}__text")
                    .annotate(count=Count(f"{self.label_type_field}__text"))
                )
                
                items_list = list(items)  # Executar a query
                logger.info(f"Query executada, encontrados {len(items_list)} items")
                
            except Exception as query_error:
                logger.error(f"Erro na query SQL: {str(query_error)}", exc_info=True)
                return distribution
            
            # Preencher distribuição com dados reais
            for item in items_list:
                username = item.get("user__username")
                label_text = item.get(f"{self.label_type_field}__text")
                count = item.get("count", 0)
                
                if username and label_text and username in distribution:
                    if label_text in distribution[username]:
                        distribution[username][label_text] = count
                    else:
                        logger.warning(f"Label '{label_text}' não encontrado na distribuição inicial para user '{username}'")
                else:
                    logger.warning(f"Dados inválidos no item: username='{username}', label='{label_text}', count={count}")
            
            logger.info(f"Distribuição calculada com sucesso")
            return distribution
            
        except Exception as e:
            logger.error(f"Erro ao calcular distribuição de labels: {str(e)}", exc_info=True)
            # Retornar distribuição vazia em caso de erro
            try:
                return {member.username: {label.text: 0 for label in labels} for member in members}
            except:
                return {}

    def get_label_percentage(self, examples, labels):
        """Calculate label distribution as percentages per example.

        Args:
            examples: example queryset.
            labels: label queryset.

        Returns:
            Dictionary with percentage of each label per example.

        Examples:
            >>> self.get_label_percentage(examples, labels)
            {'example_1': {'positive': 66.7, 'negative': 33.3}, 'example_2': {'positive': 50.0, 'negative': 50.0}}
        """
        try:
            logger.info(f"Calculando percentagens para {len(examples)} examples e {labels.count()} labels")
            
            # Inicializar percentagens
            percentage = {}
            for example in examples:
                percentage[example] = {}
                for label in labels:
                    percentage[example][label.text] = 0.0
            
            # Se não há examples ou labels, retornar percentagens vazias
            if not examples or not labels.exists():
                logger.info("Nenhum example ou label encontrado, retornando percentagens vazias")
                return percentage

            try:
                items = (
                    self.filter(example_id__in=examples)
                    .values("example_id", f"{self.label_type_field}__text")
                    .annotate(count=Count(f"{self.label_type_field}__text"))
                )
                
                items_list = list(items)  # Executar a query
                logger.info(f"Query executada, encontrados {len(items_list)} items")
                
            except Exception as query_error:
                logger.error(f"Erro na query SQL: {str(query_error)}", exc_info=True)
                return percentage

            example_totals = {example: 0 for example in examples}

            for item in items_list:
                example_id = item.get("example_id")
                label_text = item.get(f"{self.label_type_field}__text")
                count = item.get("count", 0)
                
                if example_id and label_text and example_id in percentage:
                    if label_text in percentage[example_id]:
                        percentage[example_id][label_text] = count
                        example_totals[example_id] += count

            # Convert counts to percentages
            for example_id, labels_dict in percentage.items():
                total = example_totals.get(example_id, 0)
                if total > 0:
                    for label in labels_dict:
                        labels_dict[label] = (labels_dict[label] / total) * 100  # Calcula a percentagem
            
            logger.info(f"Percentagens calculadas com sucesso")
            return percentage
            
        except Exception as e:
            logger.error(f"Erro ao calcular percentagens de labels: {str(e)}", exc_info=True)
            # Retornar percentagens vazias em caso de erro
            try:
                return {example: {label.text: 0.0 for label in labels} for example in examples}
            except:
                return {}

    def get_labels(self, label, project):
        if project.collaborative_annotation:
            return self.filter(example=label.example)
        else:
            return self.filter(example=label.example, user=label.user)

    def can_annotate(self, label, project) -> bool:
        raise NotImplementedError("Please implement this method in the subclass")

    def filter_annotatable_labels(self, labels, project):
        return [label for label in labels if self.can_annotate(label, project)]


class CategoryManager(LabelManager):
    def can_annotate(self, label, project) -> bool:
        is_exclusive = project.single_class_classification
        categories = self.get_labels(label, project)
        if is_exclusive:
            return not categories.exists()
        else:
            return not categories.filter(label=label.label).exists()


class SpanManager(LabelManager):
    def can_annotate(self, label, project) -> bool:
        overlapping = getattr(project, "allow_overlapping", False)
        spans = self.get_labels(label, project)
        if overlapping:
            return True
        for span in spans:
            if span.is_overlapping(label):
                return False
        return True


class TextLabelManager(LabelManager):
    def can_annotate(self, label, project) -> bool:
        texts = self.get_labels(label, project)
        for text in texts:
            if text.is_same_text(label):
                return False
        return True


class RelationManager(LabelManager):
    label_type_field = "type"

    def can_annotate(self, label, project) -> bool:
        return True


class BoundingBoxManager(LabelManager):
    def can_annotate(self, label, project) -> bool:
        return True


class SegmentationManager(LabelManager):
    def can_annotate(self, label, project) -> bool:
        return True
