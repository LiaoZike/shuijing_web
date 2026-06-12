from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from .models import Pond, PondAerator, PondAeratorStateLog


@dataclass(frozen=True)
class AeratorOperationSnapshot:
    total: int
    operating: int
    stopped: int
    disabled: int
    items: list[dict]

    @property
    def summary(self) -> str:
        if self.total <= 0:
            return "水車: 尚未設定。"
        return (
            f"水車: {self.operating}/{self.total} 運作中，"
            f"{self.stopped} 停止，{self.disabled} 停用。"
        )


def resolve_cron_ponds(config) -> list[Pond]:
    ponds = list(config.ponds.all().order_by("name"))
    if not ponds and config.target_user_id:
        ponds = list(Pond.objects.filter(owners=config.target_user).order_by("name"))
    return ponds


def evaluate_aerator_operations(ponds: Iterable[Pond], *, persist: bool = True) -> AeratorOperationSnapshot:
    pond_ids = [pond.pk for pond in ponds]
    if not pond_ids:
        return AeratorOperationSnapshot(0, 0, 0, 0, [])

    aerators = (
        PondAerator.objects
        .filter(pond_id__in=pond_ids)
        .select_related("pond")
        .prefetch_related("pond__sensors")
        .order_by("pond__name", "name")
    )

    items = []
    operating_count = 0
    disabled_count = 0

    from django.utils import timezone
    evaluated_at = timezone.now()

    for aerator in aerators:
        is_operating = aerator.evaluate_is_operating()
        if persist:
            aerator.last_is_operating = is_operating
            aerator.last_evaluated_at = evaluated_at
            aerator.last_evaluation_reason = aerator.build_evaluation_reason(is_operating)
            aerator.save(update_fields=["last_is_operating", "last_evaluated_at", "last_evaluation_reason"])
            PondAeratorStateLog.objects.create(
                pond=aerator.pond,
                aerator=aerator,
                recorded_at=evaluated_at,
                is_operating=is_operating,
                reason=aerator.last_evaluation_reason,
            )
        if is_operating:
            operating_count += 1
        if not aerator.is_active:
            disabled_count += 1
        items.append({
            "pond_id": aerator.pond_id,
            "pond_name": aerator.pond.name,
            "aerator_id": aerator.pk,
            "aerator_name": aerator.name,
            "is_active": aerator.is_active,
            "is_operating": is_operating,
            "rule_count": len(aerator.rules or []),
        })

    total = len(items)
    stopped_count = max(0, total - operating_count)
    return AeratorOperationSnapshot(
        total=total,
        operating=operating_count,
        stopped=stopped_count,
        disabled=disabled_count,
        items=items,
    )
