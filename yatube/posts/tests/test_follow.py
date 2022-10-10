from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from posts.models import Comment, Follow, Group, Post

User = get_user_model()


class FollowViewTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(
            username='User_one'
        )
        cls.user_2 = User.objects.create_user(
            username='User_two'
        )
        cls.follow = Follow.objects.create(
            author=cls.user,
            user=cls.user_2
        )
        cls.group_1 = Group.objects.create(
            title='Название группы тестa-1',
            slug='test-slug_1',
            description='Описание группы теста-1'
        )
        cls.group_2 = Group.objects.create(
            title='Название группы теста-2',
            slug='test-slug_2',
            description='Описание группы теста-2'
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Текст поста теста',
            group=cls.group_1,
        )
        cls.comment = Comment.objects.create(
            post=cls.post,
            text='Ок',
            author=cls.user
        )

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_follow_user(self):
        """Авторизованный пользователь,
        может подписываться на других пользователей"""
        follow_us = Follow.objects.count()
        self.authorized_client.get(reverse('posts:profile_follow',
                                           kwargs={'username': self.user_2}))
        self.assertTrue(Follow.objects.filter(user=self.user,
                                              author=self.user_2).exists())
        self.assertEqual(Follow.objects.count(), follow_us + 1)

    def test_unfollow_user(self):
        """Авторизованный пользователь
        может удалять других пользователей из подписок"""
        Follow.objects.create(user=self.user, author=self.user_2)
        follow_count = Follow.objects.count()
        self.assertTrue(Follow.objects.filter(user=self.user,
                                              author=self.user_2).exists())
        self.authorized_client.get(
            reverse(
                'posts:profile_unfollow',
                kwargs={'username': self.user_2}
            )
        )
        self.assertFalse(
            Follow.objects.filter(
                user=self.user,
                author=self.user_2
            ).exists()
        )
        self.assertEqual(Follow.objects.count(), follow_count - 1)

    def test_new_post_follow(self):
        """ Новая запись пользователя будет в ленте у его подписчиков.
        """
        following = User.objects.create(username='backend')
        Follow.objects.create(user=self.user, author=following)
        post = Post.objects.create(author=following, text=self.post.text)
        response = self.authorized_client.get(reverse('posts:follow_index'))
        self.assertIn(post, response.context['page_obj'].object_list)

    def test_new_post_unfollow(self):
        """ Новая запись пользователя не будет у тех кто не подписан на него.
        """
        self.client.logout()
        User.objects.create_user(
            username='backend',
            password='pass'
        )
        self.client.login(username='backend')
        response = self.authorized_client.get(reverse('posts:follow_index'))
        self.assertNotIn(
            self.post.text,
            response.context['page_obj'].object_list
        )
