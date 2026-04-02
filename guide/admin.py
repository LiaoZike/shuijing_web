from django.contrib import admin
from .models import StorySpot, StoryFact, ARAsset


class StoryFactInline(admin.TabularInline):
    model = StoryFact
    extra = 1
    fields = ('title', 'fact_type', 'content', 'sort_order')


class ARAssetInline(admin.TabularInline):
    model = ARAsset
    extra = 1
    fields = (
        'title',
        'asset_type',
        'marker_image',
        'target_file',
        'video_file',
        'audio_file',
        'image_file',
        'model_file',
        'is_active',
    )


@admin.register(StorySpot)
class StorySpotAdmin(admin.ModelAdmin):
    list_display = (
        'title',
        'category',
        'location_name',
        'sort_order',
        'is_featured',
        'is_active',
        'updated_at',
    )
    list_filter = ('category', 'is_featured', 'is_active')
    search_fields = ('title', 'short_intro', 'content', 'location_name')
    prepopulated_fields = {'slug': ('title',)}
    ordering = ('sort_order', 'id')
    inlines = [StoryFactInline, ARAssetInline]

    fieldsets = (
        ('基本資料', {
            'fields': ('title', 'slug', 'category', 'location_name')
        }),
        ('內容', {
            'fields': ('short_intro', 'content', 'cover_image')
        }),
        ('顯示設定', {
            'fields': ('sort_order', 'is_featured', 'is_active')
        }),
    )


@admin.register(StoryFact)
class StoryFactAdmin(admin.ModelAdmin):
    list_display = ('title', 'spot', 'fact_type', 'sort_order')
    list_filter = ('fact_type', 'spot')
    search_fields = ('title', 'content', 'spot__title')
    ordering = ('spot', 'sort_order', 'id')


@admin.register(ARAsset)
class ARAssetAdmin(admin.ModelAdmin):
    list_display = ('title', 'spot', 'asset_type', 'is_active', 'created_at')
    list_filter = ('asset_type', 'is_active', 'spot')
    search_fields = ('title', 'spot__title')
    ordering = ('spot', 'id')