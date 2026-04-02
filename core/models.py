from django.db import models
# from Claud import admin
from django.utils import timezone

######################################################
# Function:首頁輪播資料模型
######################################################
class HeroSlide(models.Model):
    CATEGORY_CHOICES = [
        ('production', '生產 PRODUCTION'),
        ('ecology',    '生態 ECOLOGY'),
        ('life',       '生活 LIFE'),
    ]

    category     = models.CharField('主題', max_length=20, choices=CATEGORY_CHOICES)
    title        = models.CharField('標題', max_length=100)
    subtitle     = models.CharField('副標題', max_length=200, blank=True)
    description  = models.CharField('說明', max_length=300, blank=True)
    image        = models.ImageField('圖片', upload_to='static/image/slides/')
    cc_credit    = models.CharField('創用CC來源標註', max_length=300, blank=True,
                                    help_text='例：攝影 © 王小明 / CC BY 4.0，留空表示無需標註')
    is_active    = models.BooleanField('顯示', default=True)
    order        = models.PositiveIntegerField('排序', default=0)

    class Meta:
        ordering = ['order']
        verbose_name = '輪播圖片'
        verbose_name_plural = '輪播圖片'

    def __str__(self):
        return f"{self.get_category_display()} - {self.title}"
    
    
##################################################
# Function: 首頁服務項目
##################################################
class ServiceItem(models.Model):
    icon        = models.CharField('圖示（Emoji）', max_length=10, default='🌾',
                                   help_text='直接貼上 emoji，例如 🌾 🛍️ 📷 ✨')
    title       = models.CharField('標題', max_length=100)
    description = models.TextField('說明')
    link_text   = models.CharField('連結文字', max_length=50, default='了解更多',
                                   help_text='例如：探索農產、瀏覽商品')
    link_url    = models.CharField('連結網址', max_length=200, default='#')
    is_featured = models.BooleanField('特色標示（金框）', default=False)
    badge_text  = models.CharField('標籤文字', max_length=20, blank=True,
                                   help_text='例如：限定體驗，留空不顯示')
    is_active   = models.BooleanField('顯示', default=True)
    order       = models.PositiveIntegerField('排序', default=0)
 
    class Meta:
        ordering = ['order']
        verbose_name = '服務項目'
        verbose_name_plural = '服務項目'
 
    def __str__(self):
        return self.title 
 
##################################################
# Function: 活動資料模型
##################################################
class Activity(models.Model):
    title       = models.CharField('活動名稱', max_length=100)
    title_2     = models.CharField('副標題', max_length=200, blank=True)
    tags        = models.CharField('標籤', max_length=200, blank=True,
                                   help_text='用逗號分隔，例如：科技, USR, 體驗課程')
    description = models.TextField('活動說明')
    date        = models.DateField('活動日期')
    end_date    = models.DateField('結束日期', blank=True, null=True,
                                   help_text='單日活動留空')
    register_deadline = models.DateTimeField('報名截止時間', blank=True, null=True,
                                         help_text='留空表示不限截止日')
    time        = models.CharField('活動時間', max_length=50, blank=True,
                                   help_text='例如：09:00 - 17:00')
    location    = models.CharField('地點', max_length=100)  # 必填拿掉 blank=True
    cover_image = models.ImageField('宣傳圖片', upload_to='static/image/activities/',
                                    blank=True, null=True)
    link_url    = models.CharField('報名/詳情連結', max_length=200, blank=True)
    max_participants = models.PositiveIntegerField('人數上限', blank=True, null=True,
                                                   help_text='留空表示不限人數')
    max_per_user      = models.PositiveIntegerField('每人限報名次數', default=1,
                                                    help_text='同一活動每人最多報名幾次')
    contact_name  = models.CharField('聯絡人', max_length=50)       # 必填
    contact_phone = models.CharField('聯絡電話', max_length=20)     # 必填
    contact_email = models.EmailField('聯絡信箱', blank=True)

    is_active   = models.BooleanField('顯示', default=True)
    is_featured = models.BooleanField('置頂推薦', default=False)

    class Meta:
        ordering = ['date']
        verbose_name = '活動'
        verbose_name_plural = '活動'

    def __str__(self):
        return f"{self.date} - {self.title}"

    def tag_list(self):
        if not self.tags:
            return []
        return [t.strip() for t in self.tags.split(',') if t.strip()]

    def is_past(self):
        today = timezone.now().date()
        if self.end_date:
            return self.end_date < today
        return self.date < today

    def is_registration_open(self):
        """報名是否開放中"""
        today = timezone.now().date()
        if self.is_past():
            return False
        if self.register_deadline:
            return today <= self.register_deadline
        return True
    def registration_count(self):
        """實際報名總人數（加總每筆的人數）"""
        from django.db.models import Sum
        result = self.registrations.aggregate(total=Sum('participant_count'))
        return result['total'] or 0
    def remaining_spots(self):
        if not self.max_participants:
            return None
        return self.max_participants - self.registration_count()

    is_past.boolean = True
    is_past.short_description = '已結束'
    is_registration_open.boolean = True
    is_registration_open.short_description = '報名中'

##################################################
# Function: 活動報名資料模型
##################################################
class Registration(models.Model):
    activity       = models.ForeignKey(Activity, on_delete=models.CASCADE,
                                       related_name='registrations',
                                       verbose_name='活動')
    user           = models.ForeignKey('auth.User', on_delete=models.CASCADE,
                                       related_name='registrations',
                                       verbose_name='報名者')
    name           = models.CharField('姓名', max_length=50)
    phone          = models.CharField('電話', max_length=20)
    email          = models.EmailField('信箱')
    participant_count = models.PositiveIntegerField('報名人數', default=1,
                                                    help_text='包含本人，例如全家4人填4')
    note           = models.TextField('備註', blank=True,
                                      help_text='同行人姓名、飲食需求等')
    created_at     = models.DateTimeField('報名時間', auto_now_add=True)
    class Meta:
        unique_together = ('activity', 'user')
        verbose_name = '報名記錄'
        verbose_name_plural = '報名記錄'
    def __str__(self):
        return f"{self.activity.title} - {self.name}（{self.participant_count}人）"
    
##################################################
# Function: 同行人員資料模型
##################################################
class Participant(models.Model):
    registration = models.ForeignKey(
        Registration,
        on_delete=models.CASCADE,
        related_name='participants',
        verbose_name='報名記錄'
    )
    name  = models.CharField('姓名', max_length=50)
    phone = models.CharField('電話', max_length=20)
    email = models.EmailField('信箱', blank=True)

    class Meta:
        verbose_name = '同行人員'
        verbose_name_plural = '同行人員'

    def __str__(self):
        return f"{self.name}（{self.registration.activity.title}）"