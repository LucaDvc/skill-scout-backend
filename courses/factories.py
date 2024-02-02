from courses.models import TextLessonStep, VideoLessonStep, QuizLessonStep, QuizChoice, CodeChallengeLessonStep, \
    CodeChallengeTestCase, BaseLessonStep, ProgrammingLanguage


class LessonStepFactory:
    lesson_step_creators = {
        'text': lambda data, lesson: TextLessonStepFactory.create(data, lesson),
        'quiz': lambda data, lesson: QuizLessonStepFactory.create(data, lesson),
        'video': lambda data, lesson: VideoLessonStepFactory.create(data, lesson),
        'codechallenge': lambda data, lesson: CodeChallengeLessonStepFactory.create(data, lesson),
    }

    @staticmethod
    def create(lesson_step_data, lesson):
        lesson_step_type = lesson_step_data.pop('type', None)
        creator = LessonStepFactory.lesson_step_creators.get(lesson_step_type)

        if creator:
            return creator(lesson_step_data, lesson)
        else:
            raise ValueError(f"Invalid lesson step type: {lesson_step_type}")


class TextLessonStepFactory:
    @staticmethod
    def create(lesson_step_data, lesson):
        base = lesson_step_data.pop('base_step')
        base_step = BaseLessonStep.objects.create(
            lesson=lesson,
            **base
        )
        return TextLessonStep.objects.create(base_step=base_step, **lesson_step_data)


class VideoLessonStepFactory:
    @staticmethod
    def create(lesson_step_data, lesson):
        base = lesson_step_data.pop('base_step')
        base_step = BaseLessonStep.objects.create(
            lesson=lesson,
            **base
        )
        return VideoLessonStep.objects.create(base_step=base_step, **lesson_step_data)


class QuizLessonStepFactory:
    @staticmethod
    def create(lesson_step_data, lesson):
        base = lesson_step_data.pop('base_step')
        base_step = BaseLessonStep.objects.create(
            lesson=lesson,
            **base
        )
        quiz_lesson_step = QuizLessonStep.objects.create(base_step=base_step, **lesson_step_data)
        quiz_choices_data = lesson_step_data.pop('quiz_choices', [])
        for quiz_choice_data in quiz_choices_data:
            QuizChoice.objects.create(quiz=quiz_lesson_step, **quiz_choice_data)
        return quiz_lesson_step


class CodeChallengeLessonStepFactory:
    @staticmethod
    def create(lesson_step_data, lesson):
        # First, create a BaseLessonStep instance
        base = lesson_step_data.pop('base_step')
        base_step = BaseLessonStep.objects.create(
            lesson=lesson,
            **base
        )

        language_id = lesson_step_data.pop('language').get('id')
        try:
            language = ProgrammingLanguage.objects.get(id=language_id)
        except ProgrammingLanguage.DoesNotExist:
            raise ValueError(f"Invalid language id: {language_id}")

        # Prepare data for CodeChallengeLessonStep
        code_challenge_step_data = {**lesson_step_data, 'base_step': base_step, 'language': language}

        test_cases_data = code_challenge_step_data.pop('test_cases', [])
        # Create CodeChallengeLessonStep linked to the base step
        code_challenge_step = CodeChallengeLessonStep.objects.create(**code_challenge_step_data)

        # Handle the test cases
        for test_case_data in test_cases_data:
            CodeChallengeTestCase.objects.create(
                code_challenge_step=code_challenge_step,
                **test_case_data
            )

        return code_challenge_step
