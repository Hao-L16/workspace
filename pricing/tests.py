from datetime import datetime, timedelta
from decimal import Decimal
from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from django.utils import timezone
from pricing.models import QuoteSearch, QuoteOffer, FavoriteOffer
from pricing.forms import ArnoldClarkSearchForm
from pricing.views import _calc_days, ARNOLD_CLARK_RATES


class QuoteSearchModelTest(TestCase):
    """测试 QuoteSearch 模型"""

    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )

    def test_quote_search_creation(self):
        """测试报价搜索创建"""
        pickup_dt = timezone.now()
        dropoff_dt = pickup_dt + timedelta(days=3)

        search = QuoteSearch.objects.create(
            user=self.user,
            pickup_entity_id='GLA_PA3',
            return_entity_id='GLA_PA3',
            pickup_datetime=pickup_dt,
            dropoff_datetime=dropoff_dt,
            driver_age=25
        )

        self.assertEqual(search.user, self.user)
        self.assertEqual(search.pickup_entity_id, 'GLA_PA3')
        self.assertEqual(search.driver_age, 25)
        self.assertEqual(search.status, 'PENDING')

    def test_quote_search_str_method(self):
        """测试 QuoteSearch 的字符串表示"""
        pickup_dt = timezone.now()
        dropoff_dt = pickup_dt + timedelta(days=2)

        search = QuoteSearch.objects.create(
            user=self.user,
            pickup_entity_id='GLA_PA3',
            return_entity_id='GLA_PA3',
            pickup_datetime=pickup_dt,
            dropoff_datetime=dropoff_dt,
            driver_age=25
        )

        expected_str = f"Search#{search.id} GLA_PA3 {pickup_dt.date()}"
        self.assertEqual(str(search), expected_str)


class QuoteOfferModelTest(TestCase):
    """测试 QuoteOffer 模型"""

    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.search = QuoteSearch.objects.create(
            user=self.user,
            pickup_entity_id='GLA_PA3',
            return_entity_id='GLA_PA3',
            pickup_datetime=timezone.now(),
            dropoff_datetime=timezone.now() + timedelta(days=2),
            driver_age=25
        )

    def test_quote_offer_creation(self):
        """测试报价创建"""
        offer = QuoteOffer.objects.create(
            search=self.search,
            agent_id='arnoldclark',
            provider_name='Arnold Clark',
            car_name='Small',
            transmission='Manual',
            seats=4,
            total_price=Decimal('82.00'),
            currency='GBP',
            deeplink_url='https://example.com',
            raw_json={'test': 'data'}
        )

        self.assertEqual(offer.search, self.search)
        self.assertEqual(offer.agent_id, 'arnoldclark')
        self.assertEqual(offer.total_price, Decimal('82.00'))
        self.assertEqual(offer.currency, 'GBP')


class FavoriteOfferModelTest(TestCase):
    """测试 FavoriteOffer 模型"""

    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.other_user = User.objects.create_user(
            username='otheruser',
            password='testpass123'
        )

        self.search = QuoteSearch.objects.create(
            user=self.user,
            pickup_entity_id='GLA_PA3',
            return_entity_id='GLA_PA3',
            pickup_datetime=timezone.now(),
            dropoff_datetime=timezone.now() + timedelta(days=2),
            driver_age=25
        )

        self.offer = QuoteOffer.objects.create(
            search=self.search,
            agent_id='arnoldclark',
            provider_name='Arnold Clark',
            car_name='Small',
            transmission='Manual',
            seats=4,
            total_price=Decimal('82.00'),
            currency='GBP',
            deeplink_url='https://example.com',
            raw_json={'test': 'data'}
        )

    def test_favorite_offer_creation(self):
        """测试收藏创建"""
        favorite = FavoriteOffer.objects.create(
            user=self.user,
            offer=self.offer
        )

        self.assertEqual(favorite.user, self.user)
        self.assertEqual(favorite.offer, self.offer)

    def test_unique_favorite_constraint(self):
        """测试用户-报价的唯一性约束"""
        FavoriteOffer.objects.create(
            user=self.user,
            offer=self.offer
        )

        # 尝试创建重复的收藏应该失败
        with self.assertRaises(Exception):  # 可能是 IntegrityError
            FavoriteOffer.objects.create(
                user=self.user,
                offer=self.offer
            )


class ArnoldClarkSearchFormTest(TestCase):
    """测试 ArnoldClarkSearchForm"""

    def test_valid_form(self):
        """测试有效的表单"""
        tomorrow = timezone.now().date() + timedelta(days=1)
        day_after = tomorrow + timedelta(days=2)

        form_data = {
            'pickup_location': 'GLA_PA3',
            'pickup_date': tomorrow,
            'pickup_time': '10:00',
            'return_location': 'GLA_PA3',
            'return_date': day_after,
            'return_time': '10:00'
        }

        form = ArnoldClarkSearchForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_invalid_return_before_pickup(self):
        """测试返回时间早于接车时间的无效表单"""
        tomorrow = timezone.now().date() + timedelta(days=1)

        form_data = {
            'pickup_location': 'GLA_PA3',
            'pickup_date': tomorrow,
            'pickup_time': '15:00',
            'return_location': 'GLA_PA3',
            'return_date': tomorrow,
            'return_time': '10:00'  # 早于接车时间
        }

        form = ArnoldClarkSearchForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('__all__', form.errors)
        self.assertIn('Return datetime must be after pick-up datetime', str(form.errors))

    def test_same_day_valid(self):
        """测试同一天但时间有效的表单"""
        tomorrow = timezone.now().date() + timedelta(days=1)

        form_data = {
            'pickup_location': 'GLA_PA3',
            'pickup_date': tomorrow,
            'pickup_time': '10:00',
            'return_location': 'GLA_PA3',
            'return_date': tomorrow,
            'return_time': '15:00'
        }

        form = ArnoldClarkSearchForm(data=form_data)
        self.assertTrue(form.is_valid())


class PricingViewsTest(TestCase):
    """测试定价视图"""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )

    def test_pricing_search_view_get(self):
        """测试价格搜索视图 GET 请求"""
        response = self.client.get(reverse('pricing_search'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'pricing/search.html')
        self.assertIsInstance(response.context['form'], ArnoldClarkSearchForm)

    def test_pricing_search_view_post_valid(self):
        """测试价格搜索视图 POST 有效数据"""
        self.client.login(username='testuser', password='testpass123')

        tomorrow = timezone.now().date() + timedelta(days=1)
        day_after = tomorrow + timedelta(days=2)

        post_data = {
            'pickup_location': 'GLA_PA3',
            'pickup_date': tomorrow,
            'pickup_time': '10:00',
            'return_location': 'GLA_PA3',
            'return_date': day_after,
            'return_time': '10:00'
        }

        response = self.client.post(reverse('pricing_search'), post_data)
        self.assertEqual(response.status_code, 302)  # 重定向

        # 检查是否创建了 QuoteSearch
        search = QuoteSearch.objects.get(user=self.user)
        self.assertEqual(search.pickup_entity_id, 'GLA_PA3')
        self.assertEqual(search.return_entity_id, 'GLA_PA3')

        # 检查重定向URL是否包含搜索ID
        self.assertIn('/pricing/results/', response['Location'])

    def test_pricing_search_view_post_invalid(self):
        """测试价格搜索视图 POST 无效数据"""
        self.client.login(username='testuser', password='testpass123')

        tomorrow = timezone.now().date() + timedelta(days=1)

        post_data = {
            'pickup_location': 'GLA_PA3',
            'pickup_date': tomorrow,
            'pickup_time': '15:00',
            'return_location': 'GLA_PA3',
            'return_date': tomorrow,
            'return_time': '10:00'  # 无效：早于接车时间
        }

        response = self.client.post(reverse('pricing_search'), post_data)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'pricing/search.html')

        # 检查表单是否包含错误
        form = response.context['form']
        self.assertFalse(form.is_valid())

    def test_pricing_results_view(self):
        """测试价格结果视图"""
        # 创建测试搜索
        search = QuoteSearch.objects.create(
            user=self.user,
            pickup_entity_id='GLA_PA3',
            return_entity_id='GLA_PA3',
            pickup_datetime=timezone.now(),
            dropoff_datetime=timezone.now() + timedelta(days=2),
            driver_age=25
        )

        response = self.client.get(reverse('pricing_results', args=[search.id]))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'pricing/results.html')

        # 检查是否生成了报价
        offers = QuoteOffer.objects.filter(search=search)
        self.assertEqual(offers.count(), len(ARNOLD_CLARK_RATES))

        # 检查上下文数据
        self.assertIn('search', response.context)
        self.assertIn('offers', response.context)

    def test_pricing_history_view(self):
        """测试价格历史视图"""
        self.client.login(username='testuser', password='testpass123')

        # 创建一些搜索记录
        search1 = QuoteSearch.objects.create(
            user=self.user,
            pickup_entity_id='GLA_PA3',
            return_entity_id='GLA_PA3',
            pickup_datetime=timezone.now(),
            dropoff_datetime=timezone.now() + timedelta(days=2),
            driver_age=25
        )

        search2 = QuoteSearch.objects.create(
            user=self.user,
            pickup_entity_id='EDI_PA1',
            return_entity_id='EDI_PA1',
            pickup_datetime=timezone.now() + timedelta(days=1),
            dropoff_datetime=timezone.now() + timedelta(days=3),
            driver_age=30
        )

        response = self.client.get(reverse('pricing_history'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'pricing/history.html')

        # 检查上下文数据
        searches = response.context['searches']
        self.assertEqual(len(searches), 2)

        # 检查按创建时间倒序排列
        self.assertEqual(searches[0], search2)
        self.assertEqual(searches[1], search1)


class UtilityFunctionsTest(TestCase):
    """测试工具函数"""

    def test_calc_days_same_day(self):
        """测试计算天数：同一天"""
        pickup = datetime(2024, 1, 1, 10, 0)
        dropoff = datetime(2024, 1, 1, 15, 0)

        days = _calc_days(pickup, dropoff)
        self.assertEqual(days, 1)

    def test_calc_days_multiple_days(self):
        """测试计算天数：多天"""
        pickup = datetime(2024, 1, 1, 10, 0)
        dropoff = datetime(2024, 1, 3, 10, 0)

        days = _calc_days(pickup, dropoff)
        self.assertEqual(days, 2)

    def test_calc_days_partial_day(self):
        """测试计算天数：不足一天仍算一天"""
        pickup = datetime(2024, 1, 1, 10, 0)
        dropoff = datetime(2024, 1, 2, 2, 0)  # 16小时后

        days = _calc_days(pickup, dropoff)
        self.assertEqual(days, 1)  # 不足一天也算一天

    def test_calc_days_minimum_one_day(self):
        """测试计算天数：最少一天"""
        pickup = datetime(2024, 1, 1, 10, 0)
        dropoff = datetime(2024, 1, 1, 10, 30)  # 30分钟后

        days = _calc_days(pickup, dropoff)
        self.assertEqual(days, 1)


class FavoriteViewsTest(TestCase):
    """测试收藏功能视图"""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )

        # 创建搜索和报价
        self.search = QuoteSearch.objects.create(
            user=self.user,
            pickup_entity_id='GLA_PA3',
            return_entity_id='GLA_PA3',
            pickup_datetime=timezone.now(),
            dropoff_datetime=timezone.now() + timedelta(days=2),
            driver_age=25
        )

        self.offer = QuoteOffer.objects.create(
            search=self.search,
            agent_id='arnoldclark',
            provider_name='Arnold Clark',
            car_name='Small',
            transmission='Manual',
            seats=4,
            total_price=Decimal('82.00'),
            currency='GBP',
            deeplink_url='https://example.com',
            raw_json={'test': 'data'}
        )

    def test_favorites_view_authenticated(self):
        """测试已登录用户的收藏视图"""
        self.client.login(username='testuser', password='testpass123')

        response = self.client.get(reverse('pricing_favorites'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'pricing/favorites.html')

    def test_favorites_view_unauthenticated(self):
        """测试未登录用户的收藏视图"""
        response = self.client.get(reverse('pricing_favorites'))
        self.assertRedirects(response, '/accounts/login/?next=/pricing/favorites/')

    def test_add_to_favorites(self):
        """测试添加收藏"""
        self.client.login(username='testuser', password='testpass123')

        # 模拟添加收藏的POST请求（假设有这样的视图）
        # 这里需要根据实际的视图实现来调整
        pass

    def test_toggle_favorite_offer_add(self):
        """测试添加收藏报价"""
        self.client.login(username='testuser', password='testpass123')

        response = self.client.post(reverse('toggle_favorite_offer', args=[self.offer.id]))
        self.assertEqual(response.status_code, 302)  # 重定向到结果页

        # 检查是否创建了收藏
        favorite = FavoriteOffer.objects.get(user=self.user, offer=self.offer)
        self.assertIsNotNone(favorite)

        # 检查重定向URL
        self.assertIn('/pricing/results/', response['Location'])

    def test_toggle_favorite_offer_remove(self):
        """测试移除收藏报价"""
        self.client.login(username='testuser', password='testpass123')

        # 先添加收藏
        FavoriteOffer.objects.create(user=self.user, offer=self.offer)

        # 再次调用应该移除收藏
        response = self.client.post(reverse('toggle_favorite_offer', args=[self.offer.id]))
        self.assertEqual(response.status_code, 302)

        # 检查收藏是否被移除
        with self.assertRaises(FavoriteOffer.DoesNotExist):
            FavoriteOffer.objects.get(user=self.user, offer=self.offer)

    def test_toggle_favorite_offer_not_found(self):
        """测试不存在的报价收藏"""
        self.client.login(username='testuser', password='testpass123')

        response = self.client.post(reverse('toggle_favorite_offer', args=[999]))
        self.assertEqual(response.status_code, 404)
