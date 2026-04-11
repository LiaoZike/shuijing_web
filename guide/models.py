from django.db import models
import os
import uuid

def get_guide_upload_path(instance, filename, prefix):
    ext = filename.split('.')[-1].lower()
    new_filename = f"{instance._meta.model_name}_{uuid.uuid4().hex[:8]}.{ext}"
    return os.path.join(prefix, new_filename)

def upload_story_spots(instance, filename): return get_guide_upload_path(instance, filename, 'guide/story_spots/')
def upload_ar_markers(instance, filename): return get_guide_upload_path(instance, filename, 'guide/ar/markers/')
def upload_ar_targets(instance, filename): return get_guide_upload_path(instance, filename, 'guide/ar/targets/')
def upload_ar_videos(instance, filename): return get_guide_upload_path(instance, filename, 'guide/ar/videos/')
def upload_ar_audios(instance, filename): return get_guide_upload_path(instance, filename, 'guide/ar/audios/')
def upload_ar_images(instance, filename): return get_guide_upload_path(instance, filename, 'guide/ar/images/')
def upload_ar_models(instance, filename): return get_guide_upload_path(instance, filename, 'guide/ar/models/')


class StorySpot(models.Model):
    CATEGORY_CHOICES = [
        ('treasure', '三寶'),
        ('lightwall', '光雕牆'),
        ('temple', '廟宇'),
        ('origin', '聚落起源'),
        ('ecology', '生態'),
        ('usr', 'USR成果'),
    ]

    title = models.CharField(max_length=100, verbose_name='標題')
    slug = models.SlugField(unique=True, verbose_name='網址代稱')
    category = models.CharField(
        max_length=30,
        choices=CATEGORY_CHOICES,
        default='treasure',
        verbose_name='分類'
    )
    short_intro = models.CharField(
        max_length=255,
        blank=True,
        verbose_name='短介紹'
    )
    content = models.TextField(blank=True, verbose_name='詳細內容')
    cover_image = models.ImageField(
        upload_to=upload_story_spots,
        blank=True,
        null=True,
        verbose_name='封面圖片'
    )
    cover_image_credit = models.CharField(
        max_length=200,
        blank=True,
        verbose_name='圖片來源',
        help_text='例：CC BY 2.0 / 攝影：王小明 / Wikimedia Commons'
    )
    location_name = models.CharField(
        max_length=100,
        blank=True,
        verbose_name='地點名稱'
    )
    maps_url = models.URLField(
        blank=True,
        verbose_name='Google Maps 連結',
        help_text='建議貼完整長網址 https://www.google.com/maps/place/... 而非短網址'
    )
    sort_order = models.PositiveIntegerField(default=0, verbose_name='排序')
    is_featured = models.BooleanField(default=False, verbose_name='是否精選')
    is_active = models.BooleanField(default=True, verbose_name='是否啟用')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='建立時間')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新時間')

    class Meta:
        verbose_name = '導覽點'
        verbose_name_plural = '導覽點'
        ordering = ['sort_order', 'id']

    def __str__(self):
        return self.title


class StoryFact(models.Model):
    FACT_TYPE_CHOICES = [
        ('history', '文史資料'),
        ('legend', '地方傳說'),
        ('guide', '導覽補充'),
        ('fun', '趣味小知識'),
    ]

    spot = models.ForeignKey(
        StorySpot,
        on_delete=models.CASCADE,
        related_name='facts',
        verbose_name='所屬導覽點'
    )
    title = models.CharField(max_length=100, verbose_name='標題')
    content = models.TextField(verbose_name='內容')
    fact_type = models.CharField(
        max_length=20,
        choices=FACT_TYPE_CHOICES,
        default='guide',
        verbose_name='內容類型'
    )
    sort_order = models.PositiveIntegerField(default=0, verbose_name='排序')

    class Meta:
        verbose_name = '不重要_導覽說明'
        verbose_name_plural = '不重要_導覽說明'
        ordering = ['sort_order', 'id']

    def __str__(self):
        return f'{self.spot.title} - {self.title}'


class ARAsset(models.Model):
    ASSET_TYPE_CHOICES = [
        ('video', '影片'),
        ('audio', '音訊'),
        ('image', '圖片'),
        ('model', '3D模型'),
        ('hybrid', '混合素材'),
    ]

    spot = models.ForeignKey(
        StorySpot,
        on_delete=models.CASCADE,
        related_name='ar_assets',
        verbose_name='所屬導覽點'
    )
    title = models.CharField(max_length=100, verbose_name='素材名稱')
    asset_type = models.CharField(
        max_length=20,
        choices=ASSET_TYPE_CHOICES,
        default='video',
        verbose_name='素材類型'
    )
    marker_image = models.ImageField(
        upload_to=upload_ar_markers,
        blank=True,
        null=True,
        verbose_name='辨識圖片(marker)'
    )
    target_file = models.FileField(
        upload_to=upload_ar_targets,
        blank=True,
        null=True,
        verbose_name='MindAR target 檔'
    )
    video_file = models.FileField(
        upload_to=upload_ar_videos,
        blank=True,
        null=True,
        verbose_name='影片檔'
    )
    audio_file = models.FileField(
        upload_to=upload_ar_audios,
        blank=True,
        null=True,
        verbose_name='音訊檔'
    )
    image_file = models.ImageField(
        upload_to=upload_ar_images,
        blank=True,
        null=True,
        verbose_name='圖片素材'
    )
    model_file = models.FileField(
        upload_to=upload_ar_models,
        blank=True,
        null=True,
        verbose_name='3D模型檔'
    )
    is_active = models.BooleanField(default=True, verbose_name='是否啟用')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='建立時間')

    class Meta:
        verbose_name = 'AR素材'
        verbose_name_plural = 'AR素材'
        ordering = ['id']

    def __str__(self):
        return f'{self.spot.title} - {self.title}'