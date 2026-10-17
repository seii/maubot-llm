import unittest
import os
import aiohttp
from maubot_llm.backends import BasicOpenAIBackend, OpenAIBackend, AnthropicBackend


BASIC_OPENAI_BASE_URL = os.getenv("TEST_BASIC_OPENAI_BASE_URL")
BASIC_OPENAI_MODEL = os.getenv("TEST_BASIC_OPENAI_MODEL")
BASIC_OPENAI_API_KEY = os.getenv("TEST_BASIC_OPENAI_API_KEY")
OPENAI_API_KEY = os.getenv("TEST_OPENAI_API_KEY")
OPENAI_MODEL = os.getenv("TEST_OPENAI_MODEL", "gpt-4-turbo")
ANTHROPIC_API_KEY = os.getenv("TEST_ANTHROPIC_API_KEY")
ANTHROPIC_MODEL = os.getenv("TEST_ANTHROPIC_MODEL", "claude-3-opus-20240229")


class TestBackends(unittest.IsolatedAsyncioTestCase):
    async def test_basic(self) -> None:
        if BASIC_OPENAI_BASE_URL is None:
            print("SKIPPING because TEST_BASIC_OPENAI_BASE_URL not configured")
            return
        backend = BasicOpenAIBackend(dict(base_url=BASIC_OPENAI_BASE_URL, api_key=BASIC_OPENAI_API_KEY))
        async with aiohttp.ClientSession() as http:
            context = [{"role": "user", "content": "Please say the word 'hello' in lowercase and nothing else."}]
            system = "You are a helpful digital assistant."
            completion = await backend.create_chat_completion(http, context=context, system=system, model=BASIC_OPENAI_MODEL)
            self.assertEqual(completion.data["role"], "assistant")
            self.assertRegex(completion.data["content"], r".*hello.*")
            self.assertEqual(completion.error, "")

            models = await backend.fetch_models(http)
            self.assertGreater(len(models.data), 0)
    
    async def test_openai(self) -> None:
        if OPENAI_API_KEY is None:
            print("SKIPPING because TEST_OPENAI_API_KEY not configured")
            return
        backend = OpenAIBackend(dict(api_key=OPENAI_API_KEY))
        async with aiohttp.ClientSession() as http:
            context = [{"role": "user", "content": "Please say the word 'hello' in lowercase and nothing else."}]
            completion = await backend.create_chat_completion(http, context=context, model=OPENAI_MODEL)
            self.assertEqual(completion.data["role"], "assistant")
            self.assertRegex(completion.data["content"], r".*hello.*")
            self.assertEqual(completion.error, "")

            models = await backend.fetch_models(http)
            self.assertGreater(len(models.data), 0)
    
    async def test_anthropic(self) -> None:
        if ANTHROPIC_API_KEY is None:
            print("SKIPPING because TEST_ANTHROPIC_API_KEY not configured")
            return
        backend = AnthropicBackend(dict(api_key=ANTHROPIC_API_KEY, max_tokens=1024))
        async with aiohttp.ClientSession() as http:
            context = [{"role": "user", "content": "Please say the word 'hello' in lowercase and nothing else."}]
            completion = await backend.create_chat_completion(http, context=context, model=ANTHROPIC_MODEL)
            self.assertEqual(completion.data["role"], "assistant")
            self.assertRegex(completion.data["content"], r".*hello.*")
            self.assertEqual(completion.error, "")

if __name__ == "__main__":
    unittest.main()
