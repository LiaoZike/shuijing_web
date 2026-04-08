from django.shortcuts import render, get_object_or_404
from .models import StorySpot, ARAsset


def guide_home(request):
    spots = StorySpot.objects.filter(is_active=True).order_by('sort_order', 'id')
    featured_spots = spots.filter(is_featured=True)

    treasure_spots = spots.filter(category='treasure')
    lightwall_spots = spots.filter(category='lightwall')
    origin_spots = spots.filter(category='origin')
    temple_spots = spots.filter(category='temple')
    ecology_spots = spots.filter(category='ecology')
    usr_spots = spots.filter(category='usr')

    preview_video = ARAsset.objects.filter(
        is_active=True,
        video_file__isnull=False
    ).exclude(video_file='').first()

    featured_others = spots.exclude(category='treasure')[:6]

    context = {
        'spots': spots,
        'featured_spots': featured_spots,
        'treasure_spots': treasure_spots,
        'lightwall_spots': lightwall_spots,
        'origin_spots': origin_spots,
        'temple_spots': temple_spots,
        'ecology_spots': ecology_spots,
        'usr_spots': usr_spots,
        'featured_others': featured_others,
        'page_title': '水井村互動導覽',
        'current_category': None,
        'preview_video': preview_video,
    }
    return render(request, 'guide/guide_home.html', context)


def guide_category(request, category):
    spots = StorySpot.objects.filter(
        is_active=True,
        category=category
    ).order_by('sort_order', 'id')

    category_map = dict(StorySpot.CATEGORY_CHOICES)

    context = {
        'spots': spots,
        'featured_spots': spots.filter(is_featured=True),
        'page_title': f'水井村互動導覽｜{category_map.get(category, category)}',
        'current_category': category,
        'category_label': category_map.get(category, category),
    }
    return render(request, 'guide/guide_home.html', context)



def guide_detail(request, slug):
    spot = get_object_or_404(
        StorySpot.objects.prefetch_related('facts', 'ar_assets'),
        slug=slug,
        is_active=True
    )

    facts = spot.facts.all().order_by('sort_order', 'id')
    ar_assets = spot.ar_assets.filter(is_active=True).order_by('id')

    history_facts = facts.filter(fact_type='history')
    legend_facts = facts.filter(fact_type='legend')
    guide_facts = facts.filter(fact_type='guide')
    fun_facts = facts.filter(fact_type='fun')

    context = {
        'spot': spot,
        'facts': facts,
        'history_facts': history_facts,
        'legend_facts': legend_facts,
        'guide_facts': guide_facts,
        'fun_facts': fun_facts,
        'ar_assets': ar_assets,
        'page_title': spot.title,
    }
    return render(request, 'guide/guide_detail.html', context)
"""
def guide_ar(request, slug):
    spot = get_object_or_404(
        StorySpot.objects.prefetch_related('ar_assets'),
        slug=slug,
        is_active=True
    )

    ar_assets = spot.ar_assets.filter(is_active=True).order_by('id')
    primary_asset = ar_assets.first()

    has_target = bool(primary_asset and primary_asset.target_file)
    has_video = bool(primary_asset and primary_asset.video_file)
    has_image = bool(primary_asset and primary_asset.image_file)
    has_audio = bool(primary_asset and primary_asset.audio_file)
    has_model = bool(primary_asset and primary_asset.model_file)

    context = {
        'spot': spot,
        'ar_assets': ar_assets,
        'primary_asset': primary_asset,
        'has_target': has_target,
        'has_video': has_video,
        'has_image': has_image,
        'has_audio': has_audio,
        'has_model': has_model,
        'page_title': f'{spot.title} AR 體驗',
    }
    return render(request, 'guide/ar_experience.html', context)
"""

def guide_ar_treasures(request, slug):
    # 用 slug 找到入口 spot
    spot = get_object_or_404(
        StorySpot,
        slug=slug,
        is_active=True
    )
    ar_assets = ARAsset.objects.filter(
        spot__slug=spot.slug,
        spot__is_active=True,
        is_active=True
    ).select_related('spot').order_by('spot__sort_order', 'spot__id', 'id')

    # 取第一個有 target_file 的（合併檔）
    target_file_url = None
    for asset in ar_assets:
        if asset.target_file:
            target_file_url = asset.target_file.url
            break

    context = {
        'target_name': spot.title,
        'page_title': f'{spot.title} AR 體驗',
        'ar_assets': ar_assets,
        'target_file_url': target_file_url,
        'has_assets': ar_assets.exists(),
        'has_target': bool(target_file_url),
        'spot': spot,
    }
    return render(request, 'guide/ar_treasures.html', context)