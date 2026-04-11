from django.db import models
from django.utils import timezone
import os
import uuid

def get_upload_path(instance, filename, prefix):
    """
    自定義上傳路徑處理函式
    格式：[路徑]/[模型名]_[隨機碼].[副檔名]
    """
    ext = filename.split('.')[-1].lower()
    # 使用 uuid 確保檔名唯一性
    new_filename = f"{instance._meta.model_name}_{uuid.uuid4().hex[:8]}.{ext}"
    return os.path.join(prefix, new_filename)

def upload_slides(instance, filename): return get_upload_path(instance, filename, 'slides/')
def upload_activities(instance, filename): return get_upload_path(instance, filename, 'activities/')
def upload_usr_aiot(instance, filename): return get_upload_path(instance, filename, 'usr/aiot/')
def upload_usr_achievements(instance, filename): return get_upload_path(instance, filename, 'usr/achievements/')
def upload_usr_videos(instance, filename): return get_upload_path(instance, filename, 'usr/videos/')
def upload_usr_video_images(instance, filename): return get_upload_path(instance, filename, 'usr/video_images/')
def upload_usr_team(instance, filename): return get_upload_path(instance, filename, 'usr/team/')
def upload_notices(instance, filename): return get_upload_path(instance, filename, 'notices/')
def upload_usr_achievement_images(instance, filename): return get_upload_path(instance, filename, 'usr/achievements/gallery/')

######################################################
# Function:首頁輪播資料模型
######################################################
class HeroSlide(models.Model):
    category     = models.CharField('主題', max_length=50)  # ← 改這裡
    title        = models.CharField('標題', max_length=100)
    subtitle     = models.CharField('副標題', max_length=200, blank=True)
    description  = models.CharField('說明', max_length=300, blank=True)
    image        = models.ImageField('圖片', upload_to=upload_slides)
    cc_credit    = models.CharField('創用CC來源標註', max_length=300, blank=True)
    is_active    = models.BooleanField('顯示', default=True)
    order        = models.PositiveIntegerField('排序', default=0)

    class Meta:
        verbose_name = '首頁輪播'
        verbose_name_plural = '首頁輪播'
        ordering = ['order']

    def __str__(self):
        return f"{self.category} - {self.title}"
        
    
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
    link_url    = models.CharField('連結網址', max_length=500, default='#')
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
    cover_image = models.ImageField('宣傳圖片', upload_to=upload_activities,
                                    blank=True, null=True)
    link_url    = models.CharField('報名/詳情連結', max_length=500, blank=True)
    max_participants = models.PositiveIntegerField('總人數上限', blank=True, null=True,
                                                   help_text='留空表示不限總人數')
    max_per_user      = models.PositiveIntegerField('每帳號限報名人數', blank=True, null=True,
                                                    help_text='留空表示不限制')
    contact_name  = models.CharField('聯絡人', max_length=50)       # 必填
    contact_phone = models.CharField('聯絡電話', max_length=20)     # 必填
    contact_email = models.EmailField('聯絡信箱', blank=True)

    allow_waitlist = models.BooleanField('允許候補', default=False,
                                         help_text='當名額不足時，是否允許轉為候補')
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
        from django.utils import timezone
        if self.is_past():
            return False
        if self.is_registration_closed:
            return False
        if self.register_deadline:
            return timezone.now() <= self.register_deadline
        return True
    def registration_count(self):
        """實際確認報名總人數（只計算 confirmed，加總每筆的人數）"""
        from django.db.models import Sum
        result = self.registrations.filter(status='confirmed').aggregate(total=Sum('participant_count'))
        return result['total'] or 0

    def waitlist_count(self):
        """候補總人數（只計算 waitlist，加總每筆的人數）"""
        from django.db.models import Sum
        result = self.registrations.filter(status='waitlist').aggregate(total=Sum('participant_count'))
        return result['total'] or 0

    def remaining_spots(self):
        if not self.max_participants:
            return None
        return max(0, self.max_participants - self.registration_count())
    is_registration_closed = models.BooleanField(
        '強制關閉報名',
        default=False,
        help_text='勾選後立即停止報名，不論截止日期'
    )
    is_past.boolean = True
    is_past.short_description = '已結束'
    is_registration_open.boolean = True
    is_registration_open.short_description = '報名中'

##################################################
# Function: 活動報名資料模型
##################################################
class Registration(models.Model):
    STATUS_CHOICES = [
        ('confirmed', '已確認'),
        ('waitlist',  '候補中'),
    ]

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
    status         = models.CharField('報名狀態', max_length=10,
                                      choices=STATUS_CHOICES, default='confirmed',
                                      help_text='confirmed=已確認, waitlist=候補中')
    note           = models.TextField('備註', blank=True,
                                      help_text='同行人姓名、飲食需求等')
    created_at     = models.DateTimeField('報名時間', auto_now_add=True)
    class Meta:
        unique_together = ('activity', 'user')
        verbose_name = '報名記錄'
        verbose_name_plural = '報名記錄'
    def __str__(self):
        status_label = '候補' if self.status == 'waitlist' else '確認'
        return f"{self.activity.title} - {self.name}（{self.participant_count}人・{status_label}）"
    def get_date(self):
        return self.activity.date
    
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
    
##################################################
# Function: 聯絡我們表單
##################################################
class ContactMessage(models.Model):
    STATUS_CHOICES = [
        ('new',     '未讀'),
        ('read',    '已讀'),
        ('replied', '已回覆'),
    ]
 
    name       = models.CharField('姓名', max_length=50)
    email      = models.EmailField('信箱')
    phone      = models.CharField('電話', max_length=20, blank=True)
    subject    = models.CharField('主旨', max_length=100)
    message    = models.TextField('訊息內容')
    status     = models.CharField('狀態', max_length=10,
                                  choices=STATUS_CHOICES, default='new')
    created_at = models.DateTimeField('送出時間', auto_now_add=True)
 
    class Meta:
        ordering = ['-created_at']
        verbose_name = '聯絡訊息'
        verbose_name_plural = '聯絡訊息'
 
    def __str__(self):
        return f"{self.name}・{self.subject}（{self.get_status_display()}）"

##################################################
# Function: USR - AIoT 專案 (AIoT Project)
##################################################
class AiotProject(models.Model):
    icon        = models.CharField('圖示（Emoji）', max_length=10, default='🐟')
    title       = models.CharField('專案名稱', max_length=100)
    tags        = models.CharField('標籤', max_length=100, help_text='例如：智慧養殖,水質監測')
    description = models.TextField('專案說明')
    image       = models.ImageField('專案圖片', upload_to=upload_usr_aiot, blank=True, null=True)
    link_url    = models.CharField('連結網址', max_length=500, blank=True, help_text='與在地故事結合的延伸連結')
    is_active   = models.BooleanField('顯示', default=True)
    order       = models.PositiveIntegerField('排序', default=0)

    class Meta:
        ordering = ['order']
        verbose_name = 'USR AIoT 專案'
        verbose_name_plural = 'USR AIoT 專案'

    def __str__(self):
        return self.title

    def tag_list(self):
        if not self.tags:
            return []
        return [t.strip() for t in self.tags.split(',') if t.strip()]


##################################################
# Function: USR - 師生實踐成果 (USR Achievement)
##################################################
class UsrAchievement(models.Model):
    date        = models.DateField('日期')
    category    = models.CharField('分類/標籤', max_length=50, help_text='例如：社會實踐, AIoT 課程')
    title       = models.CharField('標題', max_length=100)
    description = models.TextField('說明')
    image       = models.ImageField('活動照片', upload_to=upload_usr_achievements, blank=True, null=True)
    link_url    = models.CharField('詳細連結', max_length=500, blank=True)
    is_active   = models.BooleanField('顯示', default=True)

    class Meta:
        ordering = ['-date']
        verbose_name = 'USR 師生表現紀錄'
        verbose_name_plural = 'USR 師生表現紀錄'

    def __str__(self):
        return f"[{self.date}] {self.title}"

class UsrAchievementImage(models.Model):
    achievement = models.ForeignKey(UsrAchievement, related_name='images', on_delete=models.CASCADE, verbose_name='所屬成果')
    image       = models.ImageField('圖片', upload_to=upload_usr_achievement_images)
    caption     = models.CharField('圖片說明', max_length=200, blank=True)
    order       = models.IntegerField('排序', default=0)
    created_at  = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['order', 'created_at']
        verbose_name = '師生成果圖片'
        verbose_name_plural = '師生成果圖片'

    def __str__(self):
        return f"Image for {self.achievement.title}"


##################################################
# Function: USR - 影音紀錄 (USR Video)
##################################################
class UsrVideo(models.Model):
    date        = models.DateField('發布日期')
    title       = models.CharField('影片/紀錄標題', max_length=150)
    description = models.TextField('詳細說明', blank=True)
    link_url    = models.CharField('YouTube 連結', max_length=500, blank=True)
    embed_code  = models.TextField(
        '自訂嵌入原始碼', 
        blank=True, 
        help_text='可貼入來自 YouTube / Facebook 等平台的嵌入原始碼（iframe 格式）'  # ← 移除 < > 符號
    )
    video_file  = models.FileField('直接上傳影片檔', upload_to=upload_usr_videos, blank=True, null=True)
    is_active   = models.BooleanField('顯示', default=True)

    class Meta:
        ordering = ['-date']
        verbose_name = 'USR 影音紀錄'
        verbose_name_plural = 'USR 影音紀錄'

    def __str__(self):
        return self.title

    def get_embed_url(self):
        if not self.link_url:
            return ""
        if "youtube.com/embed" in self.link_url:
            return self.link_url  # 直接回傳，不替換網域
        import re
        match = re.search(r'(?:youtube\.com/watch\?v=|youtu\.be/)([\w-]+)', self.link_url)
        if match:
            return f"https://www.youtube.com/embed/{match.group(1)}"  # 改回 youtube.com
        return ""
        
    def get_embed_code_or_url(self):
        """回傳優先順序：embed_code > get_embed_url"""
        if self.embed_code and self.embed_code.strip():
            return self.embed_code.strip()
        return ""  # 只負責 raw embed_code；YouTube URL 由 get_embed_url 處理

    def get_youtube_thumbnail(self):
        if not self.link_url:
            return ""
        import re
        match = re.search(r'(?:youtube\.com/watch\?v=|youtu\.be/|youtube\.com/embed/)([\w-]+)', self.link_url)
        if match:
            return f"https://img.youtube.com/vi/{match.group(1)}/maxresdefault.jpg"
        return ""

class UsrVideoImage(models.Model):
    video       = models.ForeignKey(UsrVideo, on_delete=models.CASCADE, related_name='images', verbose_name='所屬紀錄')
    image       = models.ImageField('圖片', upload_to=upload_usr_video_images)
    caption     = models.CharField('圖片說明', max_length=100, blank=True)
    order       = models.PositiveIntegerField('排序', default=0)

    class Meta:
        ordering = ['order']
        verbose_name = '影音紀錄附圖'
        verbose_name_plural = '影音紀錄附圖'

    def __str__(self):
        return f"{self.video.title} - 圖片 {self.order}"


##################################################
# Function: USR - 團隊成員 (Usr Team)
##################################################
class UsrTeamMember(models.Model):
    name        = models.CharField('姓名', max_length=50)
    role        = models.CharField('稱謂/角色', max_length=100)
    description = models.TextField('介紹', blank=True)
    image       = models.ImageField('成員照片', upload_to=upload_usr_team, blank=True, null=True)
    order       = models.PositiveIntegerField('排序', default=0)
    is_active   = models.BooleanField('顯示', default=True)

    class Meta:
        ordering = ['order']
        verbose_name = 'USR 團隊成員'
        verbose_name_plural = 'USR 團隊成員'

    def __str__(self):
        return f"{self.name} ({self.role})"

# Close the file with the new model
class Notice(models.Model):
    CATEGORY_CHOICES = [
        ('important', '重要公告'),
        ('general',   '一般訊息'),
        ('event',     '活動快訊'),
    ]

    title        = models.CharField('標題', max_length=200)
    category     = models.CharField('分類', max_length=20, choices=CATEGORY_CHOICES, default='general')
    content      = models.TextField('內容')
    publish_date = models.DateField('發佈日期', default=timezone.now)
    is_active    = models.BooleanField('顯示', default=True)
    is_priority  = models.BooleanField('置頂', default=False)
    created_at   = models.DateTimeField('建立時間', auto_now_add=True)
    updated_at   = models.DateTimeField('更新時間', auto_now=True)

    class Meta:
        ordering = ['-is_priority', '-publish_date', '-created_at']
        verbose_name = '公告'
        verbose_name_plural = '公告'

    def __str__(self):
        return f"[{self.get_category_display()}] {self.title}"


class NoticeImage(models.Model):
    notice      = models.ForeignKey(Notice, related_name='images', on_delete=models.CASCADE, verbose_name='公告')
    image       = models.ImageField('圖片', upload_to=upload_notices)
    caption     = models.CharField('圖片說明', max_length=200, blank=True)
    order       = models.IntegerField('排序', default=0)
    created_at  = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['order', 'created_at']
        verbose_name = '公告圖片'
        verbose_name_plural = '公告圖片'

    def __str__(self):
        return f"Image for {self.notice.title}"
