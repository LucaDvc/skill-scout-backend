from django.db.models import Sum
from courses.models import QuizLessonStep, CodeChallengeLessonStep, SortingProblemLessonStep, TextProblemLessonStep
from learning.models import LearnerAssessmentStepPerformance


class CourseAssessmentAnalytics:
    @classmethod
    def get_course_statistics(cls, course):
        return {
            'quiz_statistics': cls.get_statistics_by_step_type(course, QuizLessonStep, 'Quiz'),
            'code_challenge_statistics': cls.get_statistics_by_step_type(course, CodeChallengeLessonStep, 'Code Challenge'),
            'sorting_problem_statistics': cls.get_statistics_by_step_type(course, SortingProblemLessonStep, 'Sorting Problem'),
            'text_problem_statistics': cls.get_statistics_by_step_type(course, TextProblemLessonStep, 'Text Problem')
        }

    @classmethod
    def get_statistics_by_step_type(cls, course, step_model, step_type):
        steps = step_model.objects.filter(base_step__lesson__chapter__course=course).select_related(
            'base_step', 'base_step__lesson', 'base_step__lesson__chapter'
        ).order_by(
            'base_step__lesson__chapter__creation_date',
            'base_step__lesson__order',
            'base_step__order'
        )

        stats = []

        for step in steps:
            performances = LearnerAssessmentStepPerformance.objects.filter(base_step=step.base_step)
            total_attempts = performances.aggregate(Sum('attempts'))['attempts__sum'] or 0
            pass_count = performances.filter(passed=True).count()
            total_learners = performances.count()
            success_rate = (pass_count / total_attempts) * 100 if total_attempts > 0 else 0

            stats.append({
                'lesson_id': step.base_step.lesson.id,
                'lesson_title': step.base_step.lesson.title,
                'step_order': step.base_step.order,
                'step_id': step.base_step.id,
                'step_type': step_type,
                'total_attempts': total_attempts,
                'total_learners': total_learners,
                'success_rate': success_rate,
            })

        return stats
