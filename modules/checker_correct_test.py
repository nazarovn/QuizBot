
class Checker:

    def __init__(self):
        self.test_attr = {
            'testname': str,
            'description': str,
            'user_logins': (list, type(None)),
            'begindate': (str, type(None)),
            'enddate': (str, type(None)),
            'duration': (int, type(None)),
            'questions': list
        }
        self.question_button_attr = {
            'question_type': str,
            'question': str,
            'variants': list,
            'answer': str
        }
        self.question_text_attr = {
            'question_type': str,
            'question': str,
            'answer': str
        }
        self.errors = []

    def _check_test_attr(self, test: dict):
        for attr, dtypes in self.test_attr.items():
            if attr not in test:
                self.errors.append(f'Not test attr {attr}')
                continue
            if not isinstance(test[attr], dtypes):
                self.errors.append(f'Incorrect test attr {attr} (not {dtypes})')

    def _check_question(self, test: dict):
        for question in test['questions']:
            if 'question_type' not in question:
                self.errors.append(f"Not attr 'question_type' in question: {question}")
                continue
            
            if question['question_type'] == 'button':
                question_attr = self.question_button_attr
            elif question['question_type'] == 'text':
                question_attr = self.question_text_attr
            else:
                self.errors.append(f"Unknown question_type: {question['question_type']}, must be in ['butoon', 'text']")
                continue

            for attr, dtypes in question_attr.items():
                if attr not in question:
                    self.errors.append(f"Not question attr {attr}")
                    continue
                if not isinstance(question[attr], dtypes):
                    self.errors.append(f'Incorrect question attr {attr} (not {dtypes})')

    def __call__(self, test: dict):
        self.check(test)

    def check(self, test: dict):
        checks = [self._check_test_attr, self._check_question]
        for check_ in checks:
            check_(test)
            if self.errors:
                return ';\n'.join(self.errors)

