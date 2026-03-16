import tempfile
from unittest.mock import patch

from django.test import TestCase, Client, override_settings
from django.contrib.auth.models import User
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.paginator import Page
from community.models import Post
from community.forms import PostForm


class PostModelTest(TestCase):
    """测试 Post 模型"""

    def setUp(self):
        """测试前准备数据"""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )

    def test_post_creation(self):
        """测试帖子创建"""
        post = Post.objects.create(
            author=self.user,
            category='ROUTE',
            title='Test Route',
            content='This is a test route post.'
        )

        self.assertEqual(post.author, self.user)
        self.assertEqual(post.category, 'ROUTE')
        self.assertEqual(post.title, 'Test Route')
        self.assertEqual(str(post), 'Test Route')

    def test_post_categories(self):
        """测试帖子分类"""
        # 测试所有分类选项
        categories = dict(Post.Category.choices)
        expected = {
            'ROUTE': 'Route',
            'AVOID': 'Avoid',
            'TIPS': 'Tips'
        }
        self.assertEqual(categories, expected)

    @patch('cloudinary.uploader.upload')
    def test_post_with_image(self, mock_upload):
        """测试带图片的帖子"""
        # 模拟 Cloudinary 上传返回结果
        mock_upload.return_value = {
            'url': 'http://example.com/test_image.jpg',
            'public_id': 'test_image',
            'version': 1,
            'type': 'upload',
            'resource_type': 'image',
        }

        # 创建临时图片文件
        image_content = b'fake image content'
        image_file = SimpleUploadedFile(
            'test_image.jpg',
            image_content,
            content_type='image/jpeg'
        )

        post = Post.objects.create(
            author=self.user,
            category='TIPS',
            title='Test with Image',
            content='Post with image',
            image=image_file
        )

        self.assertIsNotNone(post.image)
        # CloudinaryField returns a CloudinaryResource; check public_id
        self.assertEqual(post.image.public_id, 'test_image')


class PostFormTest(TestCase):
    """测试 PostForm"""

    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )

    def test_valid_form(self):
        """测试有效的表单"""
        form_data = {
            'category': 'ROUTE',
            'title': 'Valid Title',
            'content': 'Valid content for the post.'
        }

        form = PostForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_invalid_form_missing_title(self):
        """测试缺少标题的无效表单"""
        form_data = {
            'category': 'ROUTE',
            'content': 'Content without title'
        }

        form = PostForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('title', form.errors)

    def test_invalid_form_missing_content(self):
        """测试缺少内容的无效表单"""
        form_data = {
            'category': 'ROUTE',
            'title': 'Title without content'
        }

        form = PostForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('content', form.errors)

    @patch('cloudinary.uploader.upload')
    def test_form_with_image(self, mock_upload):
        """测试带图片的表单"""
        mock_upload.return_value = {
            'url': 'http://example.com/test_image.jpg',
            'public_id': 'test_image',
            'version': 1,
        }

        image_content = b'fake image content'
        image_file = SimpleUploadedFile(
            'test_image.jpg',
            image_content,
            content_type='image/jpeg'
        )

        form_data = {
            'category': 'TIPS',
            'title': 'Post with Image',
            'content': 'Content with image'
        }
        file_data = {'image': image_file}

        form = PostForm(data=form_data, files=file_data)
        self.assertTrue(form.is_valid())


class CommunityViewsTest(TestCase):
    """测试社区视图"""

    def setUp(self):
        """设置测试客户端和测试数据"""
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.other_user = User.objects.create_user(
            username='otheruser',
            email='other@example.com',
            password='testpass123'
        )

        # 创建测试帖子
        self.post1 = Post.objects.create(
            author=self.user,
            category='ROUTE',
            title='Route Post 1',
            content='Content for route post 1'
        )
        self.post2 = Post.objects.create(
            author=self.user,
            category='TIPS',
            title='Tips Post',
            content='Content for tips post'
        )
        self.post3 = Post.objects.create(
            author=self.other_user,
            category='AVOID',
            title='Avoid Post',
            content='Content for avoid post'
        )

    def test_post_list_view(self):
        """测试帖子列表视图"""
        response = self.client.get(reverse('community_list'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'community/list.html')

        # 检查上下文数据
        self.assertIn('page_obj', response.context)
        self.assertIn('categories', response.context)
        self.assertEqual(len(response.context['page_obj']), 3)

    def test_post_list_pagination(self):
        """测试帖子列表分页"""
        # 创建更多帖子以测试分页
        for i in range(12):  # 总共15个帖子
            Post.objects.create(
                author=self.user,
                category='ROUTE',
                title=f'Post {i}',
                content=f'Content {i}'
            )

        response = self.client.get(reverse('community_list'))
        self.assertEqual(response.status_code, 200)

        page_obj = response.context['page_obj']
        self.assertIsInstance(page_obj, Page)
        self.assertEqual(len(page_obj), 10)  # 第一页10个

        # 测试第二页
        response = self.client.get(reverse('community_list') + '?page=2')
        page_obj = response.context['page_obj']
        self.assertEqual(len(page_obj), 5)  # 第二页5个

    def test_post_list_filtering(self):
        """测试帖子列表过滤"""
        # 按分类过滤
        response = self.client.get(reverse('community_list') + '?category=ROUTE')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['page_obj']), 1)  # 只有1个ROUTE帖子

        # 按关键词搜索
        response = self.client.get(reverse('community_list') + '?q=route')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['page_obj']), 1)

    def test_post_detail_view(self):
        """测试帖子详情视图"""
        response = self.client.get(reverse('community_detail', args=[self.post1.id]))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'community/detail.html')

        # 检查上下文数据
        self.assertEqual(response.context['post'], self.post1)

    def test_post_detail_view_not_found(self):
        """测试不存在的帖子详情"""
        response = self.client.get(reverse('community_detail', args=[999]))
        self.assertEqual(response.status_code, 404)

    def test_post_create_view_get(self):
        """测试创建帖子视图 GET 请求"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('community_new'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'community/new.html')
        self.assertIsInstance(response.context['form'], PostForm)

    def test_post_create_view_post_valid(self):
        """测试创建帖子视图 POST 有效数据"""
        self.client.login(username='testuser', password='testpass123')

        post_data = {
            'category': 'TIPS',
            'title': 'New Test Post',
            'content': 'This is a new test post content.'
        }

        response = self.client.post(reverse('community_new'), post_data)

        # 检查数据库中是否创建了帖子
        post = Post.objects.get(title='New Test Post')
        self.assertEqual(post.author, self.user)
        self.assertEqual(post.category, 'TIPS')

        self.assertRedirects(response, reverse('community_detail', args=[post.id]))

    def test_post_create_view_post_invalid(self):
        """测试创建帖子视图 POST 无效数据"""
        self.client.login(username='testuser', password='testpass123')

        post_data = {
            'category': 'TIPS',
            'title': '',  # 空标题
            'content': 'Content without title'
        }

        response = self.client.post(reverse('community_new'), post_data)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'community/new.html')

        # 检查表单是否包含错误
        form = response.context['form']
        self.assertFalse(form.is_valid())
        self.assertIn('title', form.errors)

    def test_post_create_view_unauthenticated(self):
        """测试未登录用户创建帖子"""
        response = self.client.get(reverse('community_new'))
        self.assertRedirects(response, '/accounts/login/?next=/community/new/')

    def test_post_delete_view_author(self):
        """测试帖子作者删除帖子"""
        self.client.login(username='testuser', password='testpass123')

        response = self.client.post(reverse('community_delete', args=[self.post1.id]))
        self.assertRedirects(response, reverse('community_list'))

        # 检查帖子是否被删除
        with self.assertRaises(Post.DoesNotExist):
            Post.objects.get(id=self.post1.id)

    def test_post_delete_view_not_author(self):
        """测试非作者删除帖子"""
        self.client.login(username='otheruser', password='testpass123')

        response = self.client.post(reverse('community_delete', args=[self.post1.id]))
        self.assertEqual(response.status_code, 403)  # Forbidden

        # 检查帖子是否仍然存在
        post = Post.objects.get(id=self.post1.id)
        self.assertIsNotNone(post)

    def test_post_delete_view_staff(self):
        """测试管理员删除帖子"""
        staff_user = User.objects.create_user(
            username='staffuser',
            password='testpass123',
            is_staff=True
        )
        self.client.login(username='staffuser', password='testpass123')

        response = self.client.post(reverse('community_delete', args=[self.post1.id]))
        self.assertRedirects(response, reverse('community_list'))

        # 检查帖子是否被删除
        with self.assertRaises(Post.DoesNotExist):
            Post.objects.get(id=self.post1.id)

    def test_post_delete_view_get(self):
        """测试删除帖子的 GET 请求（显示确认页面）"""
        self.client.login(username='testuser', password='testpass123')

        response = self.client.get(reverse('community_delete', args=[self.post1.id]))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'community/confirm_delete.html')
        self.assertEqual(response.context['post'], self.post1)
