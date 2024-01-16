from typing import List


class TemplateInterface:
    subject: str = ''
    template_id: str = ''

    # Returns the subject of the email
    def get_subject(self) -> str:
        return self.subject

    # Returns the template id of the email
    def get_template_id(self) -> str:
        return self.template_id

    # Returns the data to be sent to the template. Override this method in
    # your class
    def get_data(self) -> dict:
        return {}

    # Returns the email address(es) to which the email is to be sent
    def get_to(self) -> str or List[str]:
        raise NotImplementedError(
            'You must implement this method in your class',
        )
