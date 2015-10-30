from vt_manager_kvm.controller.MacAllocator import MACallocator
from vt_manager_kvm.controller.SlotAllocator import SlotAllocator
from vt_manager_kvm.models.Slot import Slot
from vt_manager_kvm.models.Mac import Mac


sa=SlotAllocator()
ma=MACallocator()
s = sa.acquire("projecto","agg","slice2")
m = ma.acquire("projecto","agg","slice2")
print m

#ma.release(m.pprex_mac)
