from vt_manager_kvm.controller.SlotAllocator import SlotAllocator
from vt_manager_kvm.models import Slot
m = SlotAllocator()
a = m.acquire("p7", "am1", "s1")
b = m.acquire("p8", "am1", "s2")

