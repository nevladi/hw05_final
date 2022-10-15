from django.contrib.auth import get_user_model
from django.test import TestCase, Client
from django.urls import reverse

from posts.models import Group, Post, Follow

User = get_user_model()


class PostURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание'
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост',
            pub_date='Тестовая дата',
            group=cls.group
        )
        cls.user_2 = User.objects.create_user(username='User2')

    def setUp(self):
        self.guest_client = Client()
        us_author = PostURLTests.user
        self.authorized_client_author = Client()
        self.authorized_client_author.force_login(us_author)
        self.author = User.objects.create_user(username='Backan')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_home_url_exists_at_desired_location(self):
        """Тестирование страниц, доступных всем пользователям."""
        pages = (
            '/',
            f'/group/{self.group.slug}/',
            f'/profile/{self.user.username}/',
            f'/posts/{self.post.id}/'
        )
        for page in pages:
            with self.subTest(page=page):
                response = self.guest_client.get(page)
                self.assertEqual(response.status_code, 200)

    def test_create_url_exists_at_desired_location(self):
        """Страница /create/ доступна авторизованному пользователю."""
        response = self.authorized_client_author.get('/create/')
        self.assertEqual(response.status_code, 200)

    def test_post_edit_url_exists_at_desired_location_authorized(self):
        """Страница /posts/16/edit/ доступна автору поста."""
        response = self.authorized_client_author.get(
            f'/posts/{self.post.id}/edit/')
        self.assertEqual(response.status_code, 200)

    def test_create_url_redirect_anonymous_on_login(self):
        """Страница /create/ перенаправит анонимного пользователя
        на страницу авторизации.
        """
        response = self.guest_client.get('/create/', follow=True)
        self.assertRedirects(
            response, '/auth/login/?next=/create/')

    def test_post_edit_url_redirect_anonymous_on_login(self):
        """Страница /posts/post_id/edit/ перенаправит анонимного пользователя
        на страницу авторизации.
        """
        response = self.guest_client.get(
            f'/posts/{self.post.id}/edit/', follow=True)
        self.assertRedirects(
            response, f'/auth/login/?next=/posts/{self.post.id}/edit/')

    def test_post_follow_url_redirect_anonymous_on_login(self):
        """Страница /posts/post_id/edit/ перенаправит анонимного пользователя
        на страницу логина.
        """
        response = self.guest_client.get(
            f'/posts/{self.post.id}/edit/', follow=True)
        self.assertRedirects(
            response, f'/auth/login/?next=/posts/{self.post.id}/edit/')

    def test_post_edit_url_redirect_not_author_on_login(self):

        """Страница posts/post_id/edit/ перенаправит авторизованного
         пользователя, не являющегося автором поста,
        на страницу просмотра этого поста.
        """
        response = self.authorized_client.get(
            f'/posts/{self.post.id}/edit/', follow=True)
        self.assertRedirects(
            response, f'/posts/{self.post.id}/')

    def test_urls_uses_correct_template(self):
        """URL-адреса используют соответствующие шаблоны."""
        templates_url_names = {
            '/': 'posts/index.html',
            f'/group/{self.group.slug}/': 'posts/group_list.html',
            f'/profile/{self.user.username}/': 'posts/profile.html',
            f'/posts/{self.post.id}/': 'posts/post_detail.html',
            f'/posts/{self.post.id}/edit/': 'posts/create_post.html',
            '/create/': 'posts/create_post.html',
        }
        for url, template in templates_url_names.items():
            with self.subTest(url=url):
                response = self.authorized_client_author.get(url)
                self.assertTemplateUsed(response, template)

    def test_follow_anonim_user(self):

        follow_count = Follow.objects.count()
        response = self.guest_client.get(
            reverse('posts:profile_follow',
                    kwargs={'username': self.user_2}))
        self.assertEqual(Follow.objects.count(), follow_count)
        self.assertRedirects(
            response, f'/auth/login/?next=/profile/{self.user_2}/follow/')
