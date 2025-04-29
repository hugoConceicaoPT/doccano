from django.db.models import Manager

class PerspectiveManager(Manager):
    
    def calc_perspective_answer_distribution(self, perspective):
        """
        Calculate the percentage of each answer per question in a perspective.

        Args:
            perspective: Perspective instance.

        Returns:
            dict: {
                question_id: {
                    "answers": {
                        "Answer A": 50.0,
                        "Answer B": 50.0
                    },
                    "total": 2
                },
                ...
            }
        """
        result = {}

        questions = perspective.questions.all()

        for question in questions:
            # Obter respostas da pergunta
            answers = question.answers.all()

            total_answers = answers.count()

            # Inicializar distribuição
            distribution = {}

            for answer in answers:
                if answer.answer_option:
                    key = answer.answer_option.option
                else:
                    key = answer.answer_text

                if key not in distribution:
                    distribution[key] = 0
                distribution[key] += 1

            # Calcular percentagens
            distribution_percent = {k: (v / total_answers) * 100 for k, v in distribution.items()}

            result[question.id] = {
                "question": question.question,
                "answers": distribution_percent,
                "total": total_answers
            }

        return result