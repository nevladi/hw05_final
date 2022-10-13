from django import forms
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from posts.models import Group, Post, Comment
import shutil
import tempfile

User = get_user_model()
TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)
TEST_POSTS_INT = 15


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostPageTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='backend')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание группы',
        )
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        uploaded = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif'
        )
        cls.post = Post.objects.create(
            text='Тестовый текст поста',
            author=cls.user,
            group=cls.group,
            image=uploaded,
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        cache.clear()

    def post_info(self, post):
        with self.subTest(post=post):
            self.assertEqual(post.text, self.post.text)
            self.assertEqual(post.author, self.post.author)
            self.assertEqual(post.group.id, self.post.group.id)
            self.assertEqual(post.image, self.post.image)

    def test_forms_correct(self):
        """Проверка формы поста."""
        url_fild = {
            reverse('posts:post_create'),
            reverse('posts:post_edit', kwargs={'post_id': self.post.id, }),
        }
        for reverse_page in url_fild:
            with self.subTest(reverse_page=reverse_page):
                response = self.authorized_client.get(reverse_page)
                self.assertIsInstance(
                    response.context['form'].fields['text'],
                    forms.fields.CharField)
                self.assertIsInstance(
                    response.context['form'].fields['group'],
                    forms.fields.ChoiceField)
                self.assertIsInstance(
                    response.context['form'].fields['image'],
                    forms.fields.ImageField)

    def test_index_page_correct_context(self):
        """Шаблон index.html с правильным контекстом."""
        response = self.authorized_client.get(reverse('posts:index'))
        self.post_info(response.context['page_obj'][0])

    def test_groups_page_correct_context(self):
        """Шаблон group_list.html с правильным контекстом."""
        response = self.authorized_client.get(
            reverse(
                'posts:group_list',
                kwargs={'slug': self.group.slug})
        )
        self.assertEqual(response.context['group'], self.group)
        self.post_info(response.context['page_obj'][0])

    def test_profile_page_correct_context(self):
        """Шаблон profile.html с правильным контекстом."""
        response = self.authorized_client.get(
            reverse(
                'posts:profile',
                kwargs={'username': self.user.username}))
        self.assertEqual(response.context['author'], self.user)
        self.post_info(response.context['page_obj'][0])

    def test_detail_page_correct_context(self):
        """Шаблон post_detail.html с правильным контекстом."""
        response = self.authorized_client.get(
            reverse(
                'posts:post_detail',
                kwargs={'post_id': self.post.id}))
        self.post_info(response.context['post'])

    def test_post_form_comments(self):
        comment = Comment.objects.create(
             post=self.post,
             author=self.user,
             text='Тестовый текст поста',
        )
        response = self.authorized_client.get(
            reverse('posts:post_detail',
                    kwargs={'post_id': self.post.id})).context['comments']

        self.assertIn(comment, response)

    def test_post_not_other_group(self):
        """Новый post не отображается в другой группе."""
        Group.objects.create(
            title='Другой заголовок',
            slug='other-test-group',
            description='Другое тестовое описание',
        )
        response = self.authorized_client.get(reverse('posts:group_list', args=['other-test-group']))
        self.assertNotIn(PostPageTests.post, response.context['page_obj'])


class PaginatorViewTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='Backand')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание'
        )
        cls.posts = []
        for i in range(TEST_POSTS_INT):
            cls.posts.append(Post(
                text=f'Тестовый пост {i}',
                author=cls.user,
                group=cls.group
            )
            )
        Post.objects.bulk_create(cls.posts)

    def setUp(self):
        self.guest_client = Client()

    def test_paginator_correct_num_pages(self):
        """Паджинатор корректно работает на всех страницах."""
        pages_paginator = {
            'index': reverse('posts:index'),
            'group': reverse(
                'posts:group_list',
                kwargs={'slug': self.group.slug}
            ),
            'profile': reverse(
                'posts:profile',
                kwargs={'username': self.user.username}
            )
        }
        for url, reverse_url in pages_paginator.items():
            with self.subTest(url=url):
                response_one = self.guest_client.get(reverse_url)
                self.assertEqual(len(response_one.context['page_obj']),
                                 10)
                response_two = self.guest_client.get(reverse_url + '?page=2')
                self.assertEqual(len(response_two.context['page_obj']),
                                 TEST_POSTS_INT - 10)
