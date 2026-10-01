"""Complete interval capacity check for exact integer renewable resource claims."""
from .execution_model import ResourceClaim, ResourceDefinition
from .model import Check, Status


def check_capacity(resource: ResourceDefinition, claims: tuple[ResourceClaim, ...]) -> Check:
    if resource.mode != "renewable":
        return Check("resource_capacity", Status.UNKNOWN, "unsupported resource mode")
    changes: dict[int, int] = {}
    for claim in claims:
        if (claim.resource_id, claim.unit) != (resource.resource_id, resource.unit):
            return Check("resource_capacity", Status.FAIL, "resource identity or unit mismatch")
        changes[claim.starts_at] = changes.get(claim.starts_at, 0) + claim.quantity
        changes[claim.ends_at] = changes.get(claim.ends_at, 0) - claim.quantity
    used = 0
    for time, change in sorted(changes.items()):
        # Aggregate all starts and ends at the boundary: [start, end).
        used += change
        if used > resource.capacity:
            return Check("resource_capacity", Status.FAIL,
                         f"{resource.resource_id} at {time}: {used} > {resource.capacity} {resource.unit}")
    return Check("resource_capacity", Status.PASS, f"complete portfolio fits {resource.resource_id}")
