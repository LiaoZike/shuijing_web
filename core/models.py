from django.db import models

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
    description = models.TextField('活動說明')
    date        = models.DateField('活動日期')
    end_date    = models.DateField('結束日期', blank=True, null=True,
                                   help_text='單日活動留空')
    time        = models.CharField('時間', max_length=50, blank=True,
                                   help_text='例如：09:00 - 17:00')
    location    = models.CharField('地點', max_length=100, blank=True)
    cover_image = models.ImageField('宣傳圖片', upload_to='static/image/activities/',
                                    blank=True, null=True)
    link_url    = models.CharField('報名/詳情連結', max_length=200, blank=True,
                                   help_text='留空不顯示按鈕')
 
    # 聯絡資訊
    contact_name  = models.CharField('聯絡人', max_length=50, blank=True)
    contact_phone = models.CharField('聯絡電話', max_length=20, blank=True)
    contact_email = models.EmailField('聯絡信箱', blank=True)
 
    # 狀態
    is_active   = models.BooleanField('顯示於首頁', default=True)
    is_featured = models.BooleanField('置頂推薦', default=False)
 
    class Meta:
        ordering = ['date']
        verbose_name = '活動'
        verbose_name_plural = '活動'
 
    def __str__(self):
        return f"{self.date} - {self.title}"
 