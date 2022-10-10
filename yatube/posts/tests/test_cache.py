from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import TestCase
from django.urls import reverse
from ..models import Post

User = get_user_model()


IND_PAGE = reverse('posts:index')


class CacheTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.test_user = User.objects.create(username='backend')
        cls.post = Post.objects.create(
            text='Тестовое описание поста',
            author=cls.test_user,
        )

    def test_page_correct_template(self):
        """Кэширование данных работает корректно"""
        response = self.client.get(IND_PAGE)
        cached_response_content = response.content
        Post.objects.create(text='Второй пост', author=self.test_user)
        response = self.client.get(IND_PAGE)
        self.assertEqual(cached_response_content, response.content)
        cache.clear()
        response = self.client.get(IND_PAGE)
        self.assertNotEqual(cached_response_content, response.content)
