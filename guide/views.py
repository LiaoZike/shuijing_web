from django.shortcuts import render, get_object_or_404
from .models import StorySpot


def guide_home(request):
    spots = StorySpot.objects.filter(is_active=True).order_by('sort_order', 'id')

    featured_spots = spots.filter(is_featured=True)

    context = {
        'spots': spots,
        'featured_spots': featured_spots,
        'page_title': '水井村互動導覽',
        'current_category': None,
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

    context = {
        'spot': spot,
        'facts': facts,
        'ar_assets': ar_assets,
        'page_title': spot.title,
    }
    return render(request, 'guide/guide_detail.html', context)
