"""A RISC-V O3 system for the MSHR and reorder-buffer pilots.

--l1d-mshrs and --rob-entries select hardware settings. --mode selects
which binary workload to run; it does not change the simulated hardware.
"""

import argparse
from pathlib import Path

import m5
from m5.objects import (
    AddrRange,
    Cache,
    L2XBar,
    Process,
    RiscvO3CPU,
    Root,
    SEWorkload,
    SimpleMemory,
    SrcClockDomain,
    System,
    SystemXBar,
    VoltageDomain,
)


parser = argparse.ArgumentParser()
parser.add_argument("--binary", required=True)
parser.add_argument("--mode", choices=("dependent", "independent", "independent16"), required=True)
parser.add_argument("--l1d-mshrs", choices=(2, 4, 8, 16), type=int, required=True)
parser.add_argument("--rob-entries", choices=(64, 192), type=int, default=192)
args = parser.parse_args()
binary = str(Path(args.binary).resolve())

system = System()
system.clk_domain = SrcClockDomain(clock="2GHz", voltage_domain=VoltageDomain())
system.mem_mode = "timing"
system.mem_ranges = [AddrRange("512MiB")]
system.cache_line_size = 64
system.cpu = RiscvO3CPU()
system.cpu.numROBEntries = args.rob_entries

system.l1i = Cache(
    size="32KiB", assoc=8, tag_latency=2, data_latency=2,
    response_latency=2, mshrs=8, tgts_per_mshr=20,
)
system.l1d = Cache(
    size="32KiB", assoc=8, tag_latency=2, data_latency=2,
    response_latency=2, mshrs=args.l1d_mshrs, tgts_per_mshr=20,
)
system.l2 = Cache(
    size="512KiB", assoc=8, tag_latency=12, data_latency=12,
    response_latency=12, mshrs=32, tgts_per_mshr=20,
)
system.l2bus = L2XBar()
system.membus = SystemXBar()
system.cpu.icache_port = system.l1i.cpu_side
system.cpu.dcache_port = system.l1d.cpu_side
system.l1i.mem_side = system.l2bus.cpu_side_ports
system.l1d.mem_side = system.l2bus.cpu_side_ports
system.l2.cpu_side = system.l2bus.mem_side_ports
system.l2.mem_side = system.membus.cpu_side_ports
system.system_port = system.membus.cpu_side_ports
system.memory = SimpleMemory(
    range=system.mem_ranges[0], latency="100ns",
    latency_var="0ns", bandwidth="12.8GiB/s",
)
system.memory.port = system.membus.mem_side_ports

system.cpu.createInterruptController()
system.workload = SEWorkload.init_compatible(binary)
process = Process(cmd=[binary, args.mode])
system.cpu.workload = process
system.cpu.createThreads()

root = Root(full_system=False, system=system)
m5.instantiate()
event = m5.simulate()
print(f"GEM5_EXIT cause={event.getCause()} tick={m5.curTick()}")
