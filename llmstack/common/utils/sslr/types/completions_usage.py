from openai.types.completion_usage import CompletionUsage as _CompletionUsage


class CompletionUsage(_CompletionUsage):
    def get_input_tokens(self):
        if hasattr(self, "input_tokens"):
            return getattr(self, "input_tokens")

        return self.prompt_tokens

    def get_output_tokens(self):
        if hasattr(self, "output_tokens"):
            return getattr(self, "output_tokens")

        return self.completion_tokens
