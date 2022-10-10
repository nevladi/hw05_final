from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse
from posts.models import Group, Post

User = get_user_model()


class PostsFormsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание'
        )

    def setUp(self):
        self.guest_client = Client()
        self.user = User.objects.create_user(username='Backand')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_create_posts(self):
        """Проверка создания нового поста."""
        posts_counter = Post.objects.count()
        posts_for_test = {
            'text': 'Тестовый пост',
            'group': self.group.id,
        }
        response = self.authorized_client.post(reverse('posts:post_create'),
                                               data=posts_for_test,
                                               follow=True)
        self.assertEqual(Post.objects.count(), posts_counter + 1)
        self.assertTrue(Post.objects.filter(
            text=posts_for_test['text'],
            group=self.group.id,
            author=self.user
        ).exists())
        self.assertRedirects(response, reverse(
            'posts:profile', kwargs={'username': self.user.username}))

    def test_create_posts_not_group(self):
        """Проверяем созданный пост без указания группы."""
        posts_counter = Post.objects.count()
        post_not_group = {
            'text': 'Тестовый пост',
            'group': '',
        }
        response = self.authorized_client.post(reverse('posts:post_create'),
                                               data=post_not_group,
                                               follow=True)
        self.assertEqual(Post.objects.count(), posts_counter + 1)
        self.assertTrue(Post.objects.filter(
            group__isnull=True,
            text=post_not_group['text'],
            author=self.user
        ).exists())
        self.assertRedirects(response, reverse(
            'posts:profile', kwargs={'username': self.user.username}))

    def test_edit_post(self):
        """Проверяем редактирование поста автором."""
        self.post = Post.objects.create(
            text='Тестовый пост',
            author=self.user
        )
        posts_counter = Post.objects.count()
        edit_post = {
            'text': 'Редактированный тестовый пост',
            'group': self.group.id,
            'author': self.user,
        }
        response = self.authorized_client.post(
            reverse('posts:post_edit', kwargs={'post_id': self.post.id}),
            data=edit_post, follow=True)
        self.assertEqual(Post.objects.count(), posts_counter)
        self.assertTrue(Post.objects.filter(
            text='Редактированный тестовый пост',
            group=self.group.id,
            author=self.user).exists())
        self.assertRedirects(response, reverse(
            'posts:post_detail', kwargs={'post_id': self.post.id}))
