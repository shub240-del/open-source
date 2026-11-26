"""Run the offline RailDesk reconciliation and waitlist demo."""
from fixtures import sample_gateway_settlements, sample_internal_settlements, sample_waitlist
from service import promote_waitlist, reconcile_settlements

if __name__ == "__main__":
    report = reconcile_settlements(sample_internal_settlements(), sample_gateway_settlements())
    for name, values in report.items():
        print(f"{name}: {values}")
    print(f"promoted: {promote_waitlist(sample_waitlist(), 2)}")
