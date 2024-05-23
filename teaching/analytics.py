from django.db.models import Sum
from courses.models import QuizLessonStep, CodeChallengeLessonStep
from learning.models import CodeChallengeSubmission, LearnerQuizPerformance


class CourseAssessmentAnalytics:
    @classmethod
    def get_course_statistics(cls, course):
        return {
            'quiz_statistics': cls.get_quiz_statistics(course),
            'code_challenge_statistics': cls.get_code_challenge_statistics(course),
        }

    @classmethod
    def get_quiz_statistics(cls, course):
        quiz_steps = QuizLessonStep.objects.filter(base_step__lesson__chapter__course=course).select_related(
            'base_step', 'base_step__lesson', 'base_step__lesson__chapter'
        ).order_by(
            'base_step__lesson__chapter__creation_date',
            'base_step__lesson__order',
            'base_step__order'
        )

        stats = []

        for step in quiz_steps:
            performances = LearnerQuizPerformance.objects.filter(quiz_step=step)
            total_attempts = performances.aggregate(Sum('attempts'))['attempts__sum'] or 0
            pass_count = performances.filter(passed=True).count()
            total_learners = performances.count()
            success_rate = (pass_count / total_learners) * 100 if total_learners > 0 else 0

            stats.append({
                'chapter': step.base_step.lesson.chapter.title,
                'lesson': step.base_step.lesson.title,
                'step_order': step.base_step.order,
                'step_id': step.base_step.id,
                'total_attempts': total_attempts,
                'total_learners': total_learners,
                'success_rate': success_rate,
            })

        return stats

    @classmethod
    def get_code_challenge_statistics(cls, course):
        challenge_steps = CodeChallengeLessonStep.objects.filter(base_step__lesson__chapter__course=course).select_related(
            'base_step', 'base_step__lesson', 'base_step__lesson__chapter'
        ).order_by(
            'base_step__lesson__chapter__creation_date',
            'base_step__lesson__order',
            'base_step__order'
        )

        stats = []

        for step in challenge_steps:
            submissions = CodeChallengeSubmission.objects.filter(code_challenge_step=step)
            total_attempts = submissions.aggregate(Sum('attempts'))['attempts__sum'] or 0
            pass_count = submissions.filter(passed=True).count()
            total_learners = submissions.count()
            success_rate = (pass_count / total_learners) * 100 if total_learners > 0 else 0

            stats.append({
                'chapter': step.base_step.lesson.chapter.title,
                'lesson': step.base_step.lesson.title,
                'step_order': step.base_step.order,
                'step_id': step.base_step.id,
                'total_attempts': total_attempts,
                'total_learners': total_learners,
                'success_rate': success_rate,
            })

        return stats
