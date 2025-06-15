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
                        "Answer A": {
                            "percentage": 50.0,
                            "annotator": "User Name"
                        },
                        "Answer B": {
                            "percentage": 50.0,
                            "annotator": "User Name"
                        }
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
                key = answer.answer_text
                member = answer.member

                if key not in distribution:
                    distribution[key] = {
                        "count": 0,
                        "annotators": set()
                    }
                distribution[key]["count"] += 1
                if member and member.user:
                    distribution[key]["annotators"].add(member.user.username)

            # Calcular percentagens (evitar divisão por zero)
            if total_answers > 0:
                distribution_percent = {
                    k: {
                        "percentage": (v["count"] / total_answers) * 100,
                        "annotator": ", ".join(v["annotators"])
                    }
                    for k, v in distribution.items()
                }
            else:
                distribution_percent = {}

            result[question.id] = {
                "question": question.question,
                "answers": distribution_percent,
                "total": total_answers
            }

        return result